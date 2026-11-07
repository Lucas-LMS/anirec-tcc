"""Deterministic statistics for a complete imported library, not AniList top 30.

Runtime is estimated from progress, repeats and source duration. Missing data
remains missing. Overlapping tags/genres must never be summed as unique time.
"""
import collections
STARTED={'COMPLETED','CURRENT','REPEATING','DROPPED','PAUSED'}

def compute_statistics(records,entries,scope='COMPLETED'):
    if scope not in {'COMPLETED','STARTED','ALL','PLANNING'}:raise ValueError('Invalid statistics scope')
    by_id={r['anilist_id']:r for r in records if r.get('anilist_id')};unique={e.get('mediaId',(e.get('media') or {}).get('id')):e for e in entries};unique.pop(None,None);statuses=collections.Counter(e.get('status','UNKNOWN') for e in unique.values());selected=[e for e in unique.values() if scope=='ALL' or (e.get('status') in STARTED if scope=='STARTED' else e.get('status')==scope)];groups={'tags':{},'genres':{}};totals=dict(works=len(selected),rated=0,score_sum=0.,metadata_missing=0,watched_minutes_estimated=0,catalog_minutes_estimated=0,watched_unknown=0,catalog_unknown=0,inferred_completed_progress=0,repeats=0)
    for e in selected:
        id=e.get('mediaId',(e.get('media') or {}).get('id'));raw=e.get('media') or {};m={**by_id.get(id,{}),**{k:v for k,v in raw.items() if k in ['genres','tags','episodes','duration']}};score=float(e.get('score') or 0)
        if score>0:totals['rated']+=1;totals['score_sum']+=score
        if not m.get('genres') and not m.get('tags'):totals['metadata_missing']+=1
        duration=m.get('duration') if (m.get('duration') or 0)>0 else None;episodes=m.get('episodes') if (m.get('episodes') or 0)>0 else None;progress=e.get('progress');repeat=e.get('repeat') or 0;totals['repeats']+=repeat
        if progress is None and e.get('status')=='COMPLETED' and episodes is not None:progress=episodes;totals['inferred_completed_progress']+=1
        if e.get('status')=='PLANNING':watched=0
        else:watched=duration*(progress+repeat*(episodes or 0)) if duration is not None and progress is not None and (not repeat or episodes is not None) else None
        runtime=duration*episodes if duration is not None and episodes is not None else None
        for key,value in [('watched',watched),('catalog',runtime)]:
            if value is None:totals[key+'_unknown']+=1
            else:totals[key+'_minutes_estimated']+=value
        for kind,names in [('genres',m.get('genres',[])),('tags',[t['name'] for t in m.get('tags',[])])]:
            for name in set(names):
                r=groups[kind].setdefault(name,dict(name=name,count=0,rated_count=0,score_sum=0.,repeats=0,minutesWatched=0,catalog_minutes_estimated=0,watched_unknown=0,catalog_unknown=0));r['count']+=1;r['repeats']+=repeat
                if score>0:r['rated_count']+=1;r['score_sum']+=score
                if watched is None:r['watched_unknown']+=1
                else:r['minutesWatched']+=watched
                if runtime is None:r['catalog_unknown']+=1
                else:r['catalog_minutes_estimated']+=runtime
    result={'format':'anirec-own-library-statistics-v1','source':'local_list','scope':scope,'count':len(selected),'total_entries':len(unique),'status_counts':dict(statuses),'summary':totals,'needs_refresh':False}
    for kind in groups:
        rows=[]
        for r in groups[kind].values():
            score_sum=r.pop('score_sum');r['meanScore']=score_sum/r['rated_count'] if r['rated_count'] else None;r['viewings_count']=r['count']+r['repeats'];r['genre' if kind=='genres' else 'tag']=r['name'] if kind=='genres' else {'name':r['name']};rows.append(r)
        result[kind]=sorted(rows,key=lambda r:(-r['count'],r['name']))
    score_sum=totals.pop('score_sum');totals['meanScore']=score_sum/totals['rated'] if totals['rated'] else None;totals['viewings_count']=totals['works']+totals['repeats']
    return result
