import json,sqlite3,tempfile,unittest
from pathlib import Path
from repository import Repository
from etl_dataset import build

class ETLTests(unittest.TestCase):
    def test_provenance_normalization_idempotence_and_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.sqlite3';repo=Repository(path)
            def row(i,text):return dict(id=i,idMal=47,type='ANIME',title=dict(english='Fixture'),description=text,genres=['Action','Action'],tags=[dict(name='Female Protagonist',rank=90)])
            first=row(1,'<p>Full &amp; original synopsis.</p>');second=row(2,'Different synopsis.')
            repo.put_many('AniList',[(1,47,'Fixture',first,''),(2,47,'Fixture',second,'')])
            repo.put_many('Kaggle',[(999,999,'Excluded',dict(id=999),'Excluded')])
            a=build(path);b=build(path)
            self.assertEqual(a['version'],b['version'])
            self.assertEqual(a['quality']['works'],2)
            self.assertEqual(a['quality']['duplicate_mal_id_groups'],1)
            self.assertEqual(a['quality']['genre_links'],2)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM dataset_works').fetchone()[0],2)
                self.assertEqual(db.execute('SELECT synopsis FROM dataset_works WHERE anilist_id=1').fetchone()[0],'Full & original synopsis.')
                self.assertIsNone(db.execute('SELECT season_year FROM dataset_works LIMIT 1').fetchone()[0])
            first['description']='Changed synopsis.'
            repo.put_many('AniList',[(1,47,'Fixture',first,'')]);c=build(path)
            self.assertNotEqual(a['version'],c['version'])
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM dataset_runs').fetchone()[0],2)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM dataset_raw').fetchone()[0],3)

if __name__=='__main__':unittest.main(verbosity=2)
