"""Private SQLite storage: provenance, original responses and treated text.

This stores only records actually used by the application, not an AniList mirror.
"""
import datetime,hashlib,json,sqlite3

class Repository:
    def __init__(self,path):
        self.path=str(path)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS media (
              source TEXT NOT NULL, source_id TEXT NOT NULL, mal_id INTEGER,
              title TEXT NOT NULL, raw_json TEXT NOT NULL, synopsis TEXT NOT NULL,
              fetched_at TEXT NOT NULL, sha256 TEXT NOT NULL,
              PRIMARY KEY(source,source_id));
              CREATE INDEX IF NOT EXISTS media_mal ON media(mal_id);
              CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY, kind TEXT NOT NULL, at TEXT NOT NULL,
              details_json TEXT NOT NULL);''')
    def connect(self):return sqlite3.connect(self.path,timeout=30)
    def put_many(self,source,rows):
        stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        records=[]
        for key,mal_id,title,original,synopsis in rows:
            raw=json.dumps(original,ensure_ascii=False,sort_keys=True)
            records.append((source,str(key),mal_id,title,raw,synopsis,stamp,hashlib.sha256(raw.encode()).hexdigest()))
        with self.connect() as db:
            db.executemany('''INSERT INTO media VALUES(?,?,?,?,?,?,?,?)
              ON CONFLICT(source,source_id) DO UPDATE SET mal_id=excluded.mal_id,
              title=excluded.title,raw_json=excluded.raw_json,synopsis=excluded.synopsis,
              fetched_at=excluded.fetched_at,sha256=excluded.sha256''',records)
    def recent_anilist(self,days=7):
        cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=days)).isoformat()
        with self.connect() as db:
            return {int(key):json.loads(raw) for key,raw in db.execute(
                "SELECT source_id,raw_json FROM media WHERE source='AniList' AND fetched_at>=?",(cutoff,))}
    def stats(self):
        with self.connect() as db:
            return dict(sources=dict(db.execute('SELECT source,COUNT(*) FROM media GROUP BY source')),
                        path=self.path)
    def dataset_report(self):
        with self.connect() as db:
            row=db.execute('SELECT version,created_at,protocol,input_hash,quality_json FROM dataset_runs ORDER BY created_at DESC LIMIT 1').fetchone()
            if not row:return dict(available=False)
            vectors=db.execute('SELECT COUNT(*) FROM dataset_vectors WHERE version=?',(row[0],)).fetchone()[0]
            return dict(available=True,version=row[0],created_at=row[1],protocol=row[2],input_hash=row[3],quality=json.loads(row[4]),vectors=vectors,source='AniList GraphQL')
