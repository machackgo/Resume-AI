import tempfile,unittest,sqlite3
from pathlib import Path
from test_reranking import Harness
from resume_pipeline.runtime import open_local_snapshot
from rag.domain import Scope

class SnapshotTests(Harness,unittest.TestCase):
    def test_read_replay_and_atomic_export(self):
        self.add('source','Implemented Python APIs with validation.')
        with tempfile.TemporaryDirectory() as work:
            kb=Path(work);root=kb/'candidate-vector-store';root.mkdir(mode=0o700)
            archived=root/self.store.path.name
            with sqlite3.connect(archived) as dest:self.store._db.backup(dest)
            archived.chmod(0o600)
            live=open_local_snapshot(kb,self.scope)
            try:
                self.assertNotEqual(live.path.parent,root)
                self.assertEqual(live.count(),1)
                self.assertEqual(live.get_embedding(self.records[0].record_id).record,self.records[0])
                live.export_snapshot(root)
            finally:live.close()
            self.assertFalse(live.path.exists())
            again=open_local_snapshot(kb,self.scope)
            try:self.assertEqual(again.count(),1)
            finally:again.close()
    def test_snapshot_cannot_be_rebound_to_foreign_candidate(self):
        self.add('source','Implemented Python APIs with validation.')
        with tempfile.TemporaryDirectory() as work:
            kb=Path(work);root=kb/'candidate-vector-store';root.mkdir(mode=0o700)
            archived=root/self.store.path.name
            with sqlite3.connect(archived) as dest:self.store._db.backup(dest)
            archived.chmod(0o600)
            with self.assertRaises(ValueError):open_local_snapshot(kb,Scope('tenant','foreign'))
