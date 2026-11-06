"""Public-only fixtures for Python/JavaScript formula parity. No real user scores."""
import json,tempfile,shutil
from pathlib import Path
from engine import Engine,DATA,public

def main():
    with tempfile.TemporaryDirectory() as directory:
        shutil.copy2(DATA/'catalog-snapshot.json',Path(directory)/'catalog-snapshot.json')
        engine=Engine(data_dir=directory)
        keys=['mal:47','mal:144','mal:387','mal:54']
        keys.append(next(k for k in sorted(engine.base_keys) if k not in keys))
        records=[dict(**public(engine.base_media[k]),vector=engine.vector(engine.base_media[k]).tolist()) for k in keys]
        cohorts=[]
        for name,ratings,favorites,preferred in [('scored',{keys[0]:5,keys[1]:7.5,keys[2]:10},[keys[3]],['Yuri','Action']),('favorites_only',{},keys[1:4],['Comedy','Fantasy']),('empty',{},[],[]),('unrated_seen',{},[],['Action'])]:
            engine.profile=dict(username=None,user=None,entries=[dict(mediaId=engine.base_media[k]['anilist_id'],status='COMPLETED',score=score*10,media=dict(id=engine.base_media[k]['anilist_id'],idMal=engine.base_media[k]['mal_id'])) for k,score in ratings.items()],manual_favorites=[engine.base_media[k].copy() for k in favorites],preferred=preferred,avoided=[],rejected=[])
            if name=='unrated_seen':engine.profile['entries'].append(dict(mediaId=engine.base_media[keys[4]]['anilist_id'],status='COMPLETED',score=0,media=dict(id=engine.base_media[keys[4]]['anilist_id'],idMal=engine.base_media[keys[4]]['mal_id'])))
            engine.restore_profile_media()
            result=engine.recommend(keys[0],online=False,exclude_seen=False,personal_min_topics=0)
            expected={r['key']:{field:r[field] for field in ['base_score','personalized_score','anchor_topic_overlap','preference_affinity','profile_text_score','is_seen']} for r in result['general'] if r['key'] in keys}
            cohorts.append(dict(name=name,input=dict(records=records,anchor=records[0],ratings=ratings,favorites=favorites,preferred=preferred,seenIds=[engine.base_media[k]['anilist_id'] for k in ratings]+([engine.base_media[keys[4]]['anilist_id']] if name=='unrated_seen' else []),topic_idf=engine.topic_idf,personal_min_topics=0),expected=expected))
        target=Path(__file__).parents[1]/'tmp/parity-v7.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(cohorts,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print('Fixtures públicas:',len(cohorts))
if __name__=='__main__':main()
