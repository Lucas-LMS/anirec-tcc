"""Export one normalized research dataset version, excluding profile and cache.

Local artifact only. This is not an authorization to redistribute AniList data.
"""
import json,sqlite3
from pathlib import Path
from engine import DATA
from etl_dataset import SCHEMA

def main():
    source=sqlite3.connect(DATA/'anirec.sqlite3')
    version=source.execute('SELECT version FROM dataset_runs ORDER BY created_at DESC LIMIT 1').fetchone()[0]
    root=Path(__file__).parents[1]/'output/dataset-anilist';root.mkdir(parents=True,exist_ok=True)
    target=root/(version+'.sqlite3')
    destination=sqlite3.connect(target);destination.executescript(SCHEMA)
    counts={}
    tables=['dataset_runs','dataset_works','dataset_genres','dataset_tags','dataset_work_tags','dataset_vectors','dataset_community']
    with destination:
        for table in tables:
            rows=source.execute(f'SELECT * FROM {table} WHERE version=?',(version,)).fetchall()
            if rows:destination.executemany(f'INSERT OR REPLACE INTO {table} VALUES('+','.join('?'*len(rows[0]))+')',rows)
            counts[table]=len(rows)
        rows=source.execute('''SELECT r.* FROM dataset_raw r JOIN dataset_works w
          ON r.source_id=w.anilist_id AND r.sha256=w.raw_sha256 WHERE w.version=?''',(version,)).fetchall()
        destination.executemany('INSERT OR REPLACE INTO dataset_raw VALUES(?,?,?,?)',rows);counts['dataset_raw']=len(rows)
    integrity=destination.execute('PRAGMA integrity_check').fetchone()[0]
    destination.close();source.close()
    manifest=dict(version=version,file=target.name,tables=counts,integrity=integrity,profile_included=False,ratings_included=False,source='AniList',distribution='Local research artifact; broad redistribution permission pending',sampling_bias='User-rated works plus public sample and queries')
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest))

if __name__=='__main__':main()
