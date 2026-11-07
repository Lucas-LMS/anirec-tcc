"""Rebuildable public SQLite proof from the exact published catalog, not user tables."""
from pathlib import Path
import sqlite3,json,hashlib
def main():
    lab=Path(__file__).parent/'online/lab';data=json.loads((lab/'dataset.json').read_text(encoding='utf-8'));catalog=json.loads((lab.parent/'catalog.json').read_text(encoding='utf-8'));models=json.loads((lab/'models.json').read_text(encoding='utf-8'))
    target=lab/'corpus.sqlite3'
    with sqlite3.connect(target) as db:
        db.executescript('DROP TABLE IF EXISTS works; DROP TABLE IF EXISTS genres; DROP TABLE IF EXISTS tags; DROP TABLE IF EXISTS vectors; CREATE TABLE works(anilist_id INTEGER PRIMARY KEY,title TEXT,year INTEGER,format TEXT,status TEXT,synopsis TEXT,word_count INTEGER,source TEXT,fetched_at TEXT,average_score INTEGER,mean_score INTEGER,popularity INTEGER,community_favourites INTEGER,rating_count INTEGER,statistics_fetched_at TEXT,episodes INTEGER,duration INTEGER); CREATE TABLE genres(anilist_id INTEGER,genre TEXT,PRIMARY KEY(anilist_id,genre)); CREATE TABLE tags(anilist_id INTEGER,name TEXT,rank INTEGER,spoiler INTEGER,PRIMARY KEY(anilist_id,name)); CREATE TABLE vectors(anilist_id INTEGER,model TEXT,dimensions INTEGER,vector_f32 BLOB,PRIMARY KEY(anilist_id,model));')
        for r in data['rows']:db.execute('INSERT INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(r['anilist_id'],r['title'],r['year'],r['format'],r['status'],r['synopsis'],r['words'],'AniList',r['metadata_fetched_at'],r.get('average_score'),r.get('mean_score'),r.get('popularity'),r.get('community_favourites'),r.get('rating_count'),r.get('statistics_fetched_at'),r.get('episodes'),r.get('duration')))
        for r in catalog['records']:
            db.executemany('INSERT OR IGNORE INTO genres VALUES(?,?)',[(r['anilist_id'],g) for g in r['genres']]);db.executemany('INSERT OR IGNORE INTO tags VALUES(?,?,?,?)',[(r['anilist_id'],t['name'],t.get('rank'),bool(t.get('isGeneralSpoiler') or t.get('isMediaSpoiler'))) for t in r['tags']])
        for m in models['models']:
            blob=(lab.parent/m['file']).read_bytes();width=m['dimensions']*4
            db.executemany('INSERT INTO vectors VALUES(?,?,?,?)',[(r['anilist_id'],m['id'],m['dimensions'],blob[i*width:(i+1)*width]) for i,r in enumerate(catalog['records'])])
        relations=json.loads((lab.parent/'franchises.json').read_text(encoding='utf-8'))
        db.executescript('DROP TABLE IF EXISTS series_relations; DROP TABLE IF EXISTS series_nodes; CREATE TABLE series_nodes(anilist_id INTEGER PRIMARY KEY,title TEXT,format TEXT,status TEXT,year INTEGER,month INTEGER,day INTEGER); CREATE TABLE series_relations(source_anilist_id INTEGER REFERENCES series_nodes(anilist_id),target_anilist_id INTEGER REFERENCES series_nodes(anilist_id),relation_type TEXT,PRIMARY KEY(source_anilist_id,target_anilist_id,relation_type));')
        for node in relations['nodes'].values():
            title=node.get('title') or {};date=node.get('startDate') or {};db.execute('INSERT INTO series_nodes VALUES(?,?,?,?,?,?,?)',(node['id'],title.get('english') or title.get('romaji'),node.get('format'),node.get('status'),date.get('year'),date.get('month'),date.get('day')))
        db.executemany('INSERT OR IGNORE INTO series_relations VALUES(?,?,?)',[(e['from'],e['to'],e['type']) for e in relations['edges']])
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        queries=[]
        for label,sql in [('Contagem e ausência de sinopses','SELECT COUNT(*) AS works, SUM(word_count=0) AS missing_synopsis FROM works;'),('Gêneros mais frequentes','SELECT genre,COUNT(*) AS works FROM genres GROUP BY genre ORDER BY works DESC LIMIT 12;'),('Exemplo de busca com gênero',"SELECT w.anilist_id,w.title,w.word_count FROM works w JOIN genres g USING(anilist_id) WHERE g.genre='Action' AND w.title LIKE '%Lycoris%' ORDER BY w.title;"),('Integridade dos vetores','SELECT model,dimensions,COUNT(*) AS vectors FROM vectors GROUP BY model,dimensions;'),('Cobertura comunitária','SELECT COUNT(average_score) AS weighted_scores,COUNT(mean_score) AS mean_scores,COUNT(popularity) AS popularity,COUNT(community_favourites) AS favourites FROM works;'),('Relações oficiais de SPY x FAMILY',"SELECT r.relation_type,n.anilist_id,n.title FROM series_relations r JOIN series_nodes n ON n.anilist_id=r.target_anilist_id WHERE r.source_anilist_id=140960 ORDER BY r.relation_type,n.title;"),('Chaves órfãs','SELECT COUNT(*) AS orphan_genres FROM genres g LEFT JOIN works w USING(anilist_id) WHERE w.anilist_id IS NULL;')]:
            cursor=db.execute(sql);cols=[x[0] for x in cursor.description];queries.append({'label':label,'sql':sql,'results':[dict(zip(cols,row)) for row in cursor.fetchall()]})
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.commit()
    output={'queries':queries,'database_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'snapshot_sha256':data['sha256']};(lab/'queries.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'database_bytes':target.stat().st_size,'works':len(data['rows']),'queries':len(queries)}))
if __name__=='__main__':main()
