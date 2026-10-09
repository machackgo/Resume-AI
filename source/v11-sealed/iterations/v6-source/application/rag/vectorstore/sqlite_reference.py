"""Persistent exact-search reference; single host, private per-candidate files.

Not a server authentication boundary. Never put a live SQLite file on Ceph/NFS.
Binary64 vectors preserve Stage 3C values. SQLite narrows indexed metadata before
streaming exact cosine via a UDF; no ANN or retrieval policy lives here.
"""
from contextlib import contextmanager
from dataclasses import asdict
import json
import os
from pathlib import Path
import sqlite3
import struct
from ..domain import Scope, canonical, stable_id, now, required
from ..embeddings.models import EmbeddingConfig, EmbeddingRecord
from ..embeddings.similarity import cosine
from .config import StoreConfig
from .models import (EmbeddingSpace, ChunkReference, VectorQuery, SearchFilter,
                     StoredEmbedding, SearchHit, StoreHealth)

SCHEMA = Path(__file__).resolve().parents[2] / 'migrations/001_vectorstore_sqlite.sql'

def pack(vector): return struct.pack('<'+'d'*len(vector), *vector)
def unpack(blob): return struct.unpack('<'+'d'*(len(blob)//8), blob)

class SQLiteVectorStore:
    def __init__(self, config: StoreConfig, scope: Scope):
        if not isinstance(scope, Scope): raise ValueError('typed scope required')
        self._scope = scope
        config.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if config.root.stat().st_mode & 0o077:
            raise ValueError('vector root must be private (0700)')
        self.path = config.root / (stable_id('scope', scope.key)+'.sqlite3')
        # Reject symlink substitution; root must be controlled by this process owner.
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        if self.path.stat().st_mode & 0o077: raise ValueError('database must be private (0600)')
        self._db = sqlite3.connect(self.path, timeout=config.timeout_seconds, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        try:
            self._db.execute('PRAGMA foreign_keys=ON')
            self._db.execute('PRAGMA journal_mode=DELETE')
            self._db.execute('PRAGMA synchronous=FULL')
            version = self._db.execute('PRAGMA user_version').fetchone()[0]
            if version == 0:
                try: self._db.executescript(SCHEMA.read_text())
                except sqlite3.OperationalError:
                    if self._db.in_transaction: self._db.rollback()
                    if self._db.execute('PRAGMA user_version').fetchone()[0] != 1: raise
            elif version != 1: raise ValueError('unsupported schema version')
            with self._transaction():
                self._db.execute('INSERT OR IGNORE INTO scope_binding VALUES (1,?,?)', scope.key)
                binding = self._db.execute('SELECT tenant_id,candidate_id FROM scope_binding').fetchone()
                if tuple(binding) != scope.key: raise ValueError('database scope mismatch')
            # Additional defense against SQL accidentally joining another candidate file.
            self._db.set_authorizer(lambda action,*args: sqlite3.SQLITE_DENY
                                    if action in (sqlite3.SQLITE_ATTACH,sqlite3.SQLITE_DETACH)
                                    else sqlite3.SQLITE_OK)
        except Exception:
            self._db.close()
            raise

    @property
    def scope(self): return self._scope

    @contextmanager
    def _transaction(self):
        self._db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self._db.commit()
        except BaseException:
            self._db.rollback()
            raise

    def register_chunks(self, references):
        with self._transaction():
            for ref in references:
                if not isinstance(ref, ChunkReference) or ref.scope != self.scope:
                    raise ValueError('foreign or invalid chunk reference')
                self._db.execute('INSERT OR IGNORE INTO sources(source_id,tenant_id,candidate_id) VALUES (?,?,?)',
                                 (ref.source_id,*self.scope.key))
                source = self._db.execute('SELECT deleted FROM sources WHERE source_id=?',(ref.source_id,)).fetchone()
                if source[0]: raise ValueError('deleted source cannot be revived')
                existing = self._db.execute('SELECT source_id,version FROM source_versions WHERE evidence_id=?',(ref.evidence_id,)).fetchone()
                if existing and tuple(existing) != (ref.source_id,ref.evidence_version):
                    raise ValueError('conflicting evidence identity')
                self._db.execute("INSERT OR IGNORE INTO source_versions VALUES (?,?,?,'staged')",
                                 (ref.evidence_id,ref.source_id,ref.evidence_version))
                values = (ref.chunk_revision_id,ref.chunk_id,ref.evidence_id,ref.source_id,ref.evidence_version,
                          ref.policy_id,ref.source_type,ref.evidence_type,ref.origin,ref.trust,ref.verification_state,
                          canonical(ref.support_ids),canonical(ref.provenance_event_ids),canonical(ref.input_hashes))
                old = self._db.execute('SELECT * FROM chunk_references WHERE chunk_revision_id=?',(ref.chunk_revision_id,)).fetchone()
                if old and tuple(old) != values: raise ValueError('immutable chunk reference conflict')
                self._db.execute('INSERT OR IGNORE INTO chunk_references VALUES ('+','.join('?'*14)+')',values)

    def _space(self, space):
        c = space.config
        values = (space.space_id,c.provider,c.model,c.revision,c.dimension,int(c.normalized),
                  c.document_prefix,c.query_prefix,c.configuration_json,space.input_strategy)
        self._db.execute('INSERT OR IGNORE INTO embedding_spaces VALUES ('+','.join('?'*10)+')', values)
        if tuple(self._db.execute('SELECT * FROM embedding_spaces WHERE space_id=?',(space.space_id,)).fetchone()) != values:
            raise ValueError('embedding space conflict')

    def _validate_record(self, r):
        if not isinstance(r, EmbeddingRecord) or r.scope != self.scope: raise ValueError('foreign record')
        # Reconstruct to validate even a dataclass mutated through unsafe caller code.
        EmbeddingRecord(**{**r.__dict__})
        if r.schema_version != 1: raise ValueError('unsupported embedding schema')
        c = self._db.execute('SELECT * FROM chunk_references WHERE chunk_revision_id=?',(r.chunk_revision_id,)).fetchone()
        if c is None: raise ValueError('missing chunk reference')
        for k in ('chunk_id','evidence_id','source_id','evidence_version','policy_id','origin','trust'):
            if getattr(r,k) != c[k]: raise ValueError('record lineage mismatch: '+k)
        for k in ('support_ids','provenance_event_ids'):
            if getattr(r,k) != tuple(json.loads(c[k+'_json'])): raise ValueError('record provenance mismatch')
        if dict(json.loads(c['input_hashes_json'])).get(r.input_strategy) != r.input_hash:
            raise ValueError('input hash/version mismatch')
        cache = stable_id('embedding_cache','stage3c-v1',r.scope.key,r.input_strategy,r.input_hash,r.config.identity,'document')
        identity = stable_id('embedding_record',r.scope.key,r.chunk_id,r.chunk_revision_id,cache)
        if (r.cache_key,r.record_id) != (cache,identity): raise ValueError('incompatible deterministic identity')
        if self._db.execute('SELECT deleted FROM sources WHERE source_id=?',(r.source_id,)).fetchone()[0]:
            raise ValueError('deleted source')
        if self._db.execute('SELECT 1 FROM purged_ids WHERE embedding_id=?',(r.record_id,)).fetchone():
            raise ValueError('purged embedding cannot be revived')

    def upsert_embeddings(self, records, *, note=''):
        if not isinstance(note,str) or len(note)>1024: raise ValueError('invalid operational note')
        count = 0
        with self._transaction():
            for r in records:
                self._validate_record(r)
                space = EmbeddingSpace(r.config,r.input_strategy)
                self._space(space)
                old = self.get_embedding(r.record_id)
                if old:
                    if old.state == 'deleted': raise ValueError('tombstone cannot be revived')
                    # Regenerated created_at is not a new identity. Preserve original.
                    a,b=asdict(old.record),asdict(r)
                    a.pop('created_at'); b.pop('created_at')
                    if a != b: raise ValueError('immutable embedding identity conflict')
                    if old.note != note:
                        self._db.execute('UPDATE vector_records SET note=?,updated_at=? WHERE embedding_id=?',(note,now(),r.record_id))
                else:
                    time=now()
                    self._db.execute('INSERT INTO vector_records VALUES ('+','.join('?'*14)+')',
                        (r.record_id,*self.scope.key,space.space_id,r.config.dimension,r.chunk_revision_id,
                         r.cache_key,r.input_hash,pack(r.vector),r.created_at,time,time,0,note))
                count += 1
        return count

    def get_embedding(self, embedding_id):
        row=self._db.execute('SELECT * FROM stored_vectors WHERE embedding_id=?',(embedding_id,)).fetchone()
        if row is None: return None
        s=self._db.execute('SELECT * FROM embedding_spaces WHERE space_id=?',(row['space_id'],)).fetchone()
        c=EmbeddingConfig(s['provider'],s['model'],s['revision'],s['dimension'],bool(s['normalized']),
                          s['document_prefix'],s['query_prefix'],s['configuration_json'])
        r=EmbeddingRecord(row['embedding_id'],row['cache_key'],self.scope,row['chunk_id'],row['chunk_revision_id'],
                          row['evidence_id'],row['source_id'],row['evidence_version'],row['policy_id'],c,
                          s['input_strategy'],row['input_hash'],unpack(row['vector']),row['created_at'],
                          row['origin'],row['trust'],tuple(json.loads(row['support_ids_json'])),
                          tuple(json.loads(row['provenance_event_ids_json'])))
        return StoredEmbedding(r,row['state'],row['note'],row['stored_at'],row['updated_at'])

    def _where(self, space, filters):
        if not isinstance(filters, SearchFilter): raise ValueError('typed filter required')
        clauses=[]; values=[]
        if space is not None:
            clauses.append('space_id=?'); values.append(space.space_id)
        for name,value in asdict(filters).items():
            if value is not None:
                clauses.append(name+'=?'); values.append(value)
        return (' WHERE '+' AND '.join(clauses) if clauses else ''), values

    def search_vectors(self, query):
        if not isinstance(query,VectorQuery): raise ValueError('typed query required')
        if not self._db.execute('SELECT 1 FROM embedding_spaces WHERE space_id=?',(query.space.space_id,)).fetchone():
            raise ValueError('unknown/incompatible embedding space')
        where,values=self._where(query.space,query.filters)
        self._db.create_function('query_cosine',1,lambda blob: cosine(query.vector,unpack(blob)),deterministic=True)
        rows=self._db.execute('SELECT embedding_id,chunk_id,chunk_revision_id,evidence_id,query_cosine(vector) AS score '
                              'FROM stored_vectors'+where+' ORDER BY score DESC,embedding_id ASC LIMIT ?',(*values,query.limit))
        return tuple(SearchHit(*row) for row in rows)

    def count(self, space=None, filters=SearchFilter()):
        where,values=self._where(space,filters)
        return self._db.execute('SELECT count(*) FROM stored_vectors'+where,values).fetchone()[0]

    def activate_source_version(self, source_id, evidence_id, *, expected_current):
        with self._transaction():
            s=self._db.execute('SELECT deleted FROM sources WHERE source_id=?',(source_id,)).fetchone()
            target=self._db.execute('SELECT version,state FROM source_versions WHERE source_id=? AND evidence_id=?',(source_id,evidence_id)).fetchone()
            current=self._db.execute("SELECT evidence_id,version FROM source_versions WHERE source_id=? AND state='active'",(source_id,)).fetchone()
            if s is None or s[0] or target is None or target['state']=='deleted': raise ValueError('missing/deleted source version')
            if (current['evidence_id'] if current else None) != expected_current: raise ValueError('stale current-version token')
            if current and current['evidence_id']==evidence_id: return
            if current and target['version'] <= current['version']: raise ValueError('cannot reactivate stale source version')
            if not self._db.execute('SELECT 1 FROM stored_vectors WHERE evidence_id=? AND tombstoned=0 LIMIT 1',(evidence_id,)).fetchone():
                raise ValueError('cannot activate a version without vectors')
            self._db.execute("UPDATE source_versions SET state='superseded' WHERE source_id=? AND state='active'",(source_id,))
            self._db.execute("UPDATE source_versions SET state='active' WHERE evidence_id=?",(evidence_id,))

    def delete_embeddings(self, embedding_ids, *, purge=False):
        with self._transaction():
            return self._delete(tuple(set(embedding_ids)),purge)

    def _delete(self, ids, purge):
        affected=0
        for identity in ids:
            if purge:
                exists=self._db.execute('SELECT 1 FROM vector_records WHERE embedding_id=?',(identity,)).fetchone()
                if exists:
                    self._db.execute('INSERT OR IGNORE INTO purged_ids VALUES (?)',(identity,))
                    affected+=self._db.execute('DELETE FROM vector_records WHERE embedding_id=?',(identity,)).rowcount
            else:
                affected+=self._db.execute('UPDATE vector_records SET tombstoned=1,updated_at=? WHERE embedding_id=? AND tombstoned=0',(now(),identity)).rowcount
        return affected

    def delete_source(self, source_id, *, purge=False):
        with self._transaction():
            ids=[r[0] for r in self._db.execute('SELECT embedding_id FROM stored_vectors WHERE source_id=?',(source_id,))]
            affected=self._delete(ids,purge)
            self._db.execute('UPDATE sources SET deleted=1 WHERE source_id=?',(source_id,))
            self._db.execute("UPDATE source_versions SET state='deleted' WHERE source_id=?",(source_id,))
            return affected

    def health_check(self):
        try:
            integrity=self._db.execute('PRAGMA quick_check').fetchone()[0]
            foreign=list(self._db.execute('PRAGMA foreign_key_check'))
            scope=tuple(self._db.execute('SELECT tenant_id,candidate_id FROM scope_binding').fetchone())
            version=self._db.execute('PRAGMA user_version').fetchone()[0]
            good=integrity=='ok' and not foreign and scope==self.scope.key and version==1
            return StoreHealth(good,'sqlite-exact-reference',version,'ok' if good else 'integrity failure')
        except sqlite3.Error:
            return StoreHealth(False,'sqlite-exact-reference',0,'unavailable')

    def close(self): self._db.close()
    def __enter__(self): return self
    def __exit__(self,*args): self.close()
