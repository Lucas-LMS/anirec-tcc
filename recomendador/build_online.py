"""Build a public-safe static demo, excluding private profiles and AniList cache.

No training: export fixed document vectors for the same versioned AniList corpus.
"""
import hashlib,json,sqlite3,datetime
from pathlib import Path
from engine import Engine,PARAMS,public,DATA

def main():
    import tempfile
    # Export only whitelisted public work metadata. Never copy the profile or scores.
    source_rows=json.loads((DATA/'catalog-snapshot.json').read_text(encoding='utf-8'))
    fields={'id','idMal','type','status','format','seasonYear','countryOfOrigin','title','description','genres','tags','coverImage','siteUrl','isAdult','averageScore','meanScore','popularity','favourites','stats','statisticsFetchedAt'}
    safe_rows=[{key:value for key,value in row.items() if key in fields} for row in source_rows]
    with tempfile.TemporaryDirectory() as directory:
        (Path(directory)/'catalog-snapshot.json').write_text(json.dumps(safe_rows),encoding='utf-8')
        engine=Engine(data_dir=directory)
        with sqlite3.connect(DATA/'anirec.sqlite3') as db: dates=dict(db.execute("SELECT CAST(source_id AS INTEGER),fetched_at FROM media WHERE source='AniList'"))
        encoding_id=hashlib.sha256(json.dumps(dict(idf=engine.idf,unseen=engine.unseen),sort_keys=True).encode()).hexdigest()
        records=[dict(encoding_id=encoding_id,**{**public(engine.base_media[k]),'statistics_fetched_at':dates.get(engine.base_media[k].get('anilist_id'))},vector=engine.vector(engine.base_media[k]).tolist(),metadata_fetched_at=dates.get(engine.base_media[k].get('anilist_id')),is_adult=False) for k in sorted(engine.base_keys)]
        target=Path(__file__).parent/'online'
        target.mkdir(exist_ok=True)
        raw=json.dumps(dict(encoding_id=encoding_id,params=PARAMS,topic_idf=engine.topic_idf,records=records,source='AniList GraphQL; public work metadata only; selection protocol in source-manifest.json'),ensure_ascii=False,separators=(',',':')).encode()
        (target/'catalog.json').write_bytes(raw)
        manifest=dict(count=len(records),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),private_profile_included=False,anilist_cache_included=False,full_synopses=True,model=PARAMS['model'],version=PARAMS['version'])
        (target/'build-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        source=engine.__class__.__module__
        source_manifest=dict(source='AniList GraphQL',selection='Frozen research work-metadata snapshot from application usage, popularity sample and queries; selection bias, not the full catalogue',count=len(records),personal_ratings_included=False,usernames_included=False,source_metadata_sha256=hashlib.sha256(json.dumps(safe_rows,sort_keys=True).encode()).hexdigest())
        (target/'source-manifest.json').write_text(json.dumps(source_manifest,indent=2),encoding='utf-8')
        seeds=json.loads((Path(__file__).parent/'data/anilist-seed.json').read_text(encoding='utf-8'))
        by_ani={m.get('anilist_id'):m for m in records}
        (target/'popular.json').write_text(json.dumps([by_ani[r['id']] for r in seeds[:24] if r['id'] in by_ani],ensure_ascii=False),encoding='utf-8')
        taxonomy_path=Path(__file__).parent/'data/taxonomy.json'
        if not taxonomy_path.exists():raise ValueError('Colete a taxonomia oficial antes de publicar o onboarding.')
        (target/'taxonomy.json').write_bytes(taxonomy_path.read_bytes())
        # Full frozen word vocabulary enables client-side encoding of imported works.
        vocabulary=engine.words.index_to_key
        (target/'vocabulary.json').write_text(json.dumps(vocabulary,separators=(',',':')),encoding='utf-8')
        (target/'idf.json').write_text(json.dumps(dict(corpus_id=encoding_id,idf=engine.idf,unseen=engine.unseen),separators=(',',':')),encoding='utf-8')
        shards=[];step=16000
        for start in range(0,len(vocabulary),step):
            name=f'word-vectors-{start//step}.bin';blob=engine.words.vectors[start:start+step].astype('<f4').tobytes()
            (target/name).write_bytes(blob);shards.append(dict(file=name,start=start,count=min(step,len(vocabulary)-start),sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob)))
        (target/'model-manifest.json').write_text(json.dumps(dict(dimensions=100,dtype='float32-little-endian',words=len(vocabulary),shards=shards,model=PARAMS['model'],training_in_browser=False),indent=2),encoding='utf-8')
        (target/'.nojekyll').touch()
        print(json.dumps(manifest))

if __name__=='__main__':main()
