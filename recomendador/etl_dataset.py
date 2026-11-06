"""Versioned relational ETL over records already fetched from AniList.

No network calls, Kaggle data, model training or personal ratings in these tables.
Source selection can still reflect the user's history: record this sampling bias.
"""
import collections,datetime,hashlib,json,re,sqlite3
from pathlib import Path
from engine import DATA,clean,tokenize

SCHEMA='''
CREATE TABLE IF NOT EXISTS dataset_raw (
 source_id INTEGER NOT NULL, sha256 TEXT NOT NULL, raw_json TEXT NOT NULL,
 fetched_at TEXT NOT NULL, PRIMARY KEY(source_id,sha256));
CREATE TABLE IF NOT EXISTS dataset_runs (
 version TEXT PRIMARY KEY, created_at TEXT NOT NULL, protocol TEXT NOT NULL,
 input_hash TEXT NOT NULL, quality_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dataset_works (
 version TEXT NOT NULL, anilist_id INTEGER NOT NULL, mal_id INTEGER,
 title TEXT NOT NULL, title_romaji TEXT, title_english TEXT, format TEXT,
 season_year INTEGER, country TEXT, status TEXT, synopsis TEXT NOT NULL,
 synopsis_sha256 TEXT NOT NULL, raw_sha256 TEXT NOT NULL,
 word_count INTEGER NOT NULL, tag_count INTEGER NOT NULL,
 PRIMARY KEY(version,anilist_id));
CREATE INDEX IF NOT EXISTS dataset_year ON dataset_works(version,season_year);
CREATE TABLE IF NOT EXISTS dataset_genres (
 version TEXT NOT NULL, anilist_id INTEGER NOT NULL, genre TEXT NOT NULL,
 PRIMARY KEY(version,anilist_id,genre));
CREATE INDEX IF NOT EXISTS dataset_genre ON dataset_genres(version,genre);
CREATE TABLE IF NOT EXISTS dataset_tags (
 version TEXT NOT NULL, name TEXT NOT NULL, PRIMARY KEY(version,name));
CREATE TABLE IF NOT EXISTS dataset_work_tags (
 version TEXT NOT NULL, anilist_id INTEGER NOT NULL, tag_name TEXT NOT NULL,
 rank REAL NOT NULL, general_spoiler INTEGER NOT NULL, media_spoiler INTEGER NOT NULL,
 PRIMARY KEY(version,anilist_id,tag_name));
CREATE INDEX IF NOT EXISTS dataset_tag ON dataset_work_tags(version,tag_name);
CREATE TABLE IF NOT EXISTS dataset_vectors (
 version TEXT NOT NULL, anilist_id INTEGER NOT NULL, model TEXT NOT NULL,
 dimensions INTEGER NOT NULL, dtype TEXT NOT NULL, text_sha256 TEXT NOT NULL,
 corpus_sha256 TEXT NOT NULL, vector BLOB NOT NULL,
 PRIMARY KEY(version,anilist_id,model));
CREATE TABLE IF NOT EXISTS dataset_community (
 version TEXT NOT NULL,anilist_id INTEGER NOT NULL,average_score INTEGER,mean_score INTEGER,
 popularity INTEGER,favourites INTEGER,rating_count INTEGER,statistics_fetched_at TEXT,
 PRIMARY KEY(version,anilist_id));
'''

def build(path=None):
    db=sqlite3.connect(str(path or DATA/'anirec.sqlite3'))
    rows=db.execute("SELECT source_id,raw_json,fetched_at,sha256 FROM media WHERE source='AniList' ORDER BY CAST(source_id AS INTEGER)").fetchall()
    if not rows:raise ValueError('Não há registros AniList coletados. Nenhum download implícito será feito.')
    digest=hashlib.sha256(''.join(f'{key}:{sha}\n' for key,_,_,sha in rows).encode()).hexdigest()
    version='anilist-etl-v1-'+digest[:12]
    works=[];genres=[];tags=set();links=[];raws=[];community=[];ids=set();mal=collections.Counter();texts=collections.Counter();invalid=0
    for key,raw,stamp,sha in rows:
        item=json.loads(raw)
        if item.get('type','ANIME')!='ANIME':invalid+=1;continue
        identity=int(item['id'])
        if identity in ids:raise ValueError('ID AniList duplicado na entrada.')
        ids.add(identity);title=item.get('title') or {};text=clean(item.get('description'))
        text_hash=hashlib.sha256(text.encode()).hexdigest()
        if text:texts[text_hash]+=1
        if item.get('idMal'):mal[item['idMal']]+=1
        work_tags={t['name']:t for t in item.get('tags') or [] if t and t.get('name')}
        raws.append((identity,sha,raw,stamp))
        distribution=(item.get('stats') or {}).get('scoreDistribution')
        community.append((version,identity,item.get('averageScore'),item.get('meanScore'),item.get('popularity'),item.get('favourites'),sum(row.get('amount',0) for row in distribution) if distribution is not None else None,stamp))
        works.append((version,identity,item.get('idMal'),title.get('english') or title.get('romaji') or str(identity),title.get('romaji'),title.get('english'),item.get('format'),item.get('seasonYear'),item.get('countryOfOrigin'),item.get('status'),text,text_hash,sha,len(tokenize(text)),len(work_tags)))
        genres.extend((version,identity,g) for g in sorted(set(item.get('genres') or [])))
        for name,t in work_tags.items():
            tags.add(name);links.append((version,identity,name,max(0,min(100,float(t.get('rank') or 0))),int(bool(t.get('isGeneralSpoiler'))),int(bool(t.get('isMediaSpoiler')))))
    quality=dict(works=len(works),with_synopsis=sum(bool(r[10]) for r in works),with_tags=sum(r[14]>0 for r in works),with_genres=len({r[1] for r in genres}),with_year=sum(r[7] is not None for r in works),with_format=sum(r[6] is not None for r in works),distinct_tags=len(tags),genre_links=len(genres),tag_links=len(links),duplicate_nonempty_synopsis_groups=sum(v>1 for v in texts.values()),duplicate_mal_id_groups=sum(v>1 for v in mal.values()),excluded_non_anime=invalid)
    protocol='AniList records actually used by application: scored user works plus public popularity sample and searches. Selection bias; not representative, not full catalog. No personal scores exported. HTML stripped, entities decoded, whitespace normalized; entire source synopsis retained. Unknown fields remain NULL.'
    with db:
        db.executescript(SCHEMA)
        db.executemany('INSERT OR IGNORE INTO dataset_raw VALUES(?,?,?,?)',raws)
        db.execute('INSERT OR IGNORE INTO dataset_runs VALUES(?,?,?,?,?)',(version,datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol,digest,json.dumps(quality)))
        db.executemany('INSERT OR IGNORE INTO dataset_works VALUES('+','.join('?'*15)+')',works)
        db.executemany('INSERT OR IGNORE INTO dataset_community VALUES(?,?,?,?,?,?,?,?)',community)
        db.executemany('INSERT OR IGNORE INTO dataset_genres VALUES(?,?,?)',genres)
        db.executemany('INSERT OR IGNORE INTO dataset_tags VALUES(?,?)',[(version,t) for t in sorted(tags)])
        db.executemany('INSERT OR IGNORE INTO dataset_work_tags VALUES(?,?,?,?,?,?)',links)
    db.close()
    return dict(version=version,input_hash=digest,quality=quality,protocol=protocol)

def derive_vectors(report,path=None):
    from engine import Engine,PARAMS
    engine=Engine(data_dir=Path(path).parent if path else DATA)
    corpus_hash=hashlib.sha256(json.dumps(dict(idf=engine.idf,unseen=engine.unseen),sort_keys=True).encode()).hexdigest()
    db=sqlite3.connect(str(path or DATA/'anirec.sqlite3'))
    rows=db.execute('SELECT anilist_id,synopsis,synopsis_sha256 FROM dataset_works WHERE version=?',(report['version'],)).fetchall()
    records=[];zero=0
    for identity,text,text_hash in rows:
        vector=engine.vector(dict(key='anilist:'+str(identity),text=text))
        if not vector.any():zero+=1
        records.append((report['version'],identity,PARAMS['model'],100,'float32-little-endian',text_hash,corpus_hash,vector.astype('<f4').tobytes()))
    with db:db.executemany('INSERT OR REPLACE INTO dataset_vectors VALUES(?,?,?,?,?,?,?,?)',records)
    report['derived']=dict(vectors=len(records),zero_vectors=zero,dimensions=100,model=PARAMS['model'],idf_sha256=corpus_hash,trained=False)
    db.close()
    return report

if __name__=='__main__':
    report=derive_vectors(build())
    out=Path(__file__).parents[1]/'output/prototipo/dataset-etl.json'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
