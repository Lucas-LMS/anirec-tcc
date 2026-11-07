"""All supported history themes: recurring exposure plus relative rating quality.

Counts indicate consumption, not proof of liking. No training or top-N truncation.
"""
import collections,math
from engine_utils import normalize_name

def history_preferences(records,ratings,favorites,seen_ids,statistics,neutral,half):
    seen=set(seen_ids);favorite=set(favorites);stats={};used=set()
    for row in records:
        key=row['key']
        if key in used or not (key in ratings or key in favorite or row.get('anilist_id') in seen):continue
        used.add(key);features={normalize_name(g):g for g in row.get('genres',[])}
        features.update({normalize_name(t['name']):t['name'] for t in row.get('tags',[])})
        score=ratings.get(key)
        for tag,name in features.items():
            value=stats.setdefault(tag,dict(name=name,count=0,sum_score=0.,rated=0,favorites=0,source_statistics='local metadata'))
            value['count']+=1
            if score is not None and score>0:value['sum_score']+=score;value['rated']+=1
            if key in favorite:value['favorites']+=1
    for values,field in [(statistics.get('tags',[]),'tag'),(statistics.get('genres',[]),'genre')]:
        for row in values:
            name=(row.get('tag') or {}).get('name') if field=='tag' else row.get('genre')
            if not name:continue
            tag=normalize_name(name);previous=stats.get(tag,{})
            stats[tag]=dict(name=name,count=row.get('count',0),mean_score=row.get('meanScore'),favorites=previous.get('favorites',0),source_statistics='lista importada: cálculo local' if statistics.get('source')=='local_list' else 'AniList statistics')
    n=max(len(used),statistics.get('count') or 0,max((r['count'] for r in stats.values()),default=0),1);result={}
    for tag,row in stats.items():
        count=row['count'];mean=row.get('mean_score') if 'mean_score' in row else row['sum_score']/row['rated'] if row['rated'] else None
        if mean is not None and mean<=0:mean=None
        frequency=math.log1p(count)/math.log1p(n);quality=max(-1,min(1,(mean-neutral)/half)) if mean is not None and neutral is not None and half else 0.
        reliability=count/(count+10) if count else 0;boost=min(.35,.15*row.get('favorites',0));weight=max(-1,min(1,reliability*(.65*frequency+.35*quality)+boost))
        if weight:result[tag]=dict(name=row['name'],weight=weight,source='histórico: aproximação' if weight>0 else 'histórico: afastamento',count=count,mean_score=mean,frequency=frequency,rating_quality=quality,reliability=reliability,source_statistics=row['source_statistics'])
    return result
