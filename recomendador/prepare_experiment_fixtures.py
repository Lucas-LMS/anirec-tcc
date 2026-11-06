"""Synthetic-profile fixtures over public work metadata; no real notes."""
import json,tempfile
from pathlib import Path
from engine import Engine,public
from retrieval_experiments import apply
class Offline:
    def candidates(self,*args):return []
def main():
    with tempfile.TemporaryDirectory() as directory:
        e=Engine(client=Offline(),data_dir=directory);keys=['mal:47','mal:144','mal:387','mal:54'];e.base_keys=set(keys)
        for i,key in enumerate(keys):e.base_media[key].update(average_score=None if i==2 else 70+i*5,mean_score=75,popularity=10000,community_favourites=100)
        e.prune();e.onboarding(['Romance'],[],['mal:144']);base=e.recommend(keys[0],online=False,personal_min_topics=0)
        records=[dict(**public(e.media[key]),vector=e.vector(e.media[key]).tolist()) for key in sorted(keys)];fixtures=[]
        for strategy in ['vectors','hybrid','bm25']:
            for gamma in [0,.05,.1]:
                expected=apply(base,records,strategy,gamma)
                fixtures.append({'options':dict(records=records,anchor=next(r for r in records if r['key']==keys[0]),favorites=['mal:144'],preferred=['Romance'],personal_min_topics=0,topic_idf=e.topic_idf,strategy=strategy,community_weight=gamma),'expected':{r['key']:{field:r[field] for field in ['base_score','personalized_score','bm25_raw','bm25_normalized','community_quality']} for r in expected['general']}})
        target=Path(__file__).resolve().parents[1]/'tmp/experiments-fixtures.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(fixtures,ensure_ascii=False),encoding='utf-8');print('Experimental fixtures:',len(fixtures))
if __name__=='__main__':main()
