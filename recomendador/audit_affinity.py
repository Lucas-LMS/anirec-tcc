"""Compare alternative scales; no training and no claimed human accuracy."""
import json,math,statistics
from pathlib import Path
from engine import Engine,topics
from affinity import theme_affinity

def main():
    engine=Engine();_,preferences,_,_=engine.profile_signals();records=[]
    for item in engine.base_media.values():
        features=topics(item,True);details=theme_affinity(preferences,features)
        denominator=sum(abs(p['weight']) for p in preferences.values()) or 1
        old=max(0,min(1,sum(p['weight']*features[t]['weight'] for t,p in preferences.items() if t in features)/denominator))
        positive={t:p['weight'] for t,p in preferences.items() if p['weight']>0}
        norm=math.sqrt(sum(w*w for w in positive.values())*sum(v['weight']**2 for v in features.values()))
        cosine=sum(w*features[t]['weight'] for t,w in positive.items() if t in features)/norm if norm else 0
        records.append(dict(title=item['title'],global_signed=old,positive_only=details['positive_coverage'],separate_coverage=details['score'],positive_cosine=cosine,diagnostics=details))
    report=dict(scope='All active AniList documents, current local preference snapshot; not a relevance benchmark',methods={})
    for method in ['global_signed','positive_only','separate_coverage','positive_cosine']:
        values=sorted(r[method] for r in records)
        report['methods'][method]=dict(mean=statistics.mean(values),median=statistics.median(values),p90=values[int(.9*(len(values)-1))],minimum=min(values),maximum=max(values))
    report['examples']=[r for r in records if r['title'] in ['Noir','Gunslinger Girl','Lycoris Recoil','Sakura Trick']]
    out=Path(__file__).parents[1]/'output/prototipo/afinidade-v7';out.mkdir(exist_ok=True)
    (out/'comparacao-formulas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
