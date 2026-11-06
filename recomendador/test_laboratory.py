"""Integrity checks for exported public model/data artifacts."""
import hashlib,json,sqlite3,unittest
from pathlib import Path
import numpy as np
class LaboratoryTests(unittest.TestCase):
    def test_models_align_with_catalog_and_are_normalized(self):
        root=Path(__file__).parent/'online';catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'));manifest=json.loads((root/'lab/models.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['row_keys'],[r['key'] for r in catalog['records']]);self.assertEqual(hashlib.sha256((root/'catalog.json').read_bytes()).hexdigest(),manifest['corpus_sha256'])
        for model in manifest['models']:
            blob=(root/model['file']).read_bytes();self.assertEqual(hashlib.sha256(blob).hexdigest(),model['sha256']);values=np.frombuffer(blob,dtype='<f4').reshape(model['rows'],model['dimensions']);self.assertTrue(np.isfinite(values).all());lengths=np.linalg.norm(values,axis=1);self.assertTrue(np.all((lengths==0)|(np.abs(lengths-1)<1e-5)))
            self.assertEqual(int(sum(lengths==0)),3)
            if model['id']=='skipgram':np.testing.assert_allclose(values,np.asarray([r['vector'] for r in catalog['records']]),rtol=1e-5,atol=1e-6)
    def test_sqlite_matches_public_snapshot_without_user_tables(self):
        root=Path(__file__).parent/'online';catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
        with sqlite3.connect(root/'lab/corpus.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(db.execute('SELECT COUNT(*) FROM works').fetchone()[0],len(catalog['records']));self.assertEqual(set(r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")),{'works','genres','tags','vectors'});self.assertEqual(db.execute('SELECT COUNT(*) FROM vectors').fetchone()[0],4*len(catalog['records']))
if __name__=='__main__':unittest.main()
