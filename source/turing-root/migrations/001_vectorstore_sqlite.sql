-- Stage 3D reference schema. Each file is bound to exactly one scope.
BEGIN IMMEDIATE;
CREATE TABLE scope_binding (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 tenant_id TEXT NOT NULL CHECK(length(trim(tenant_id))>0),
 candidate_id TEXT NOT NULL CHECK(length(trim(candidate_id))>0),
 UNIQUE(tenant_id,candidate_id));
CREATE TRIGGER immutable_scope_update BEFORE UPDATE ON scope_binding BEGIN SELECT RAISE(ABORT,'immutable scope'); END;
CREATE TRIGGER immutable_scope_delete BEFORE DELETE ON scope_binding BEGIN SELECT RAISE(ABORT,'immutable scope'); END;
CREATE TABLE embedding_spaces (
 space_id TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
 revision TEXT NOT NULL, dimension INTEGER NOT NULL CHECK(dimension>0),
 normalized INTEGER NOT NULL CHECK(normalized IN (0,1)),
 document_prefix TEXT NOT NULL, query_prefix TEXT NOT NULL,
 configuration_json TEXT NOT NULL, input_strategy TEXT NOT NULL,
 UNIQUE(space_id,dimension));
CREATE TABLE sources (
 source_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, candidate_id TEXT NOT NULL,
 deleted INTEGER NOT NULL DEFAULT 0 CHECK(deleted IN (0,1)),
 FOREIGN KEY(tenant_id,candidate_id) REFERENCES scope_binding(tenant_id,candidate_id));
CREATE TABLE source_versions (
 evidence_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id),
 version INTEGER NOT NULL CHECK(version>0),
 state TEXT NOT NULL CHECK(state IN ('staged','active','superseded','deleted')),
 UNIQUE(source_id,version), UNIQUE(evidence_id,source_id,version));
CREATE UNIQUE INDEX one_active_version ON source_versions(source_id) WHERE state='active';
CREATE INDEX version_lifecycle ON source_versions(source_id,state);
CREATE TABLE chunk_references (
 chunk_revision_id TEXT PRIMARY KEY, chunk_id TEXT NOT NULL,
 evidence_id TEXT NOT NULL, source_id TEXT NOT NULL, evidence_version INTEGER NOT NULL,
 policy_id TEXT NOT NULL, source_type TEXT NOT NULL, evidence_type TEXT NOT NULL,
 origin TEXT NOT NULL, trust TEXT NOT NULL CHECK(trust='untrusted_data'),
 verification_state TEXT NOT NULL CHECK(verification_state='resolve_supports'),
 support_ids_json TEXT NOT NULL, provenance_event_ids_json TEXT NOT NULL,
 input_hashes_json TEXT NOT NULL,
 FOREIGN KEY(evidence_id,source_id,evidence_version) REFERENCES source_versions(evidence_id,source_id,version));
CREATE INDEX chunk_evidence ON chunk_references(evidence_id);
CREATE INDEX chunk_filters ON chunk_references(source_type,evidence_type,policy_id);
CREATE TABLE vector_records (
 embedding_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, candidate_id TEXT NOT NULL,
 space_id TEXT NOT NULL, dimension INTEGER NOT NULL,
 chunk_revision_id TEXT NOT NULL REFERENCES chunk_references(chunk_revision_id),
 cache_key TEXT NOT NULL, input_hash TEXT NOT NULL,
 vector BLOB NOT NULL CHECK(length(vector)=8*dimension),
 created_at TEXT NOT NULL, stored_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 tombstoned INTEGER NOT NULL DEFAULT 0 CHECK(tombstoned IN (0,1)), note TEXT NOT NULL,
 FOREIGN KEY(space_id,dimension) REFERENCES embedding_spaces(space_id,dimension),
 FOREIGN KEY(tenant_id,candidate_id) REFERENCES scope_binding(tenant_id,candidate_id));
CREATE INDEX vector_space_live ON vector_records(space_id,tombstoned,chunk_revision_id);
CREATE INDEX vector_chunk ON vector_records(chunk_revision_id);
CREATE TABLE purged_ids (embedding_id TEXT PRIMARY KEY);
CREATE VIEW stored_vectors AS
 SELECT v.*, c.chunk_id,c.evidence_id,c.source_id,c.evidence_version,c.policy_id,
 c.source_type,c.evidence_type,c.origin,c.trust,c.verification_state,
 c.support_ids_json,c.provenance_event_ids_json,
 CASE WHEN v.tombstoned=1 OR s.deleted=1 THEN 'deleted' ELSE sv.state END AS state
 FROM vector_records v JOIN chunk_references c USING(chunk_revision_id)
 JOIN source_versions sv ON sv.evidence_id=c.evidence_id
 JOIN sources s ON s.source_id=c.source_id;
PRAGMA user_version=1;
COMMIT;
