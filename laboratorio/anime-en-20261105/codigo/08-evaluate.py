"""Expected-tie ranking metrics and paired family bootstrap.

No new inference; qrels only enter this evaluation stage.
"""
import math,re
import numpy as np
from support import DATA,OUT,ROOT,SEED,read,load,save
def quality(scores,grades,strict_total,ideal_grades,forbidden):
    scores=np.round(np.asarray(scores,dtype=float),12);grades=np.asarray(grades);forbidden=np.asarray(forbidden,dtype=float)
    order=np.argsort(-scores,kind='stable');scores=scores[order];grades=grades[order];forbidden=forbidden[order]
    gains=2.**grades-1;strict=(grades==2).astype(float)
    expected_gain=np.zeros(len(scores));expected_strict=np.zeros(len(scores));expected_forbidden=np.zeros(len(scores));groups=[]
    start=0
    while start<len(scores):
        end=start+1
        while end<len(scores) and scores[end]==scores[start]:end+=1
        expected_gain[start:end]=gains[start:end].mean();expected_strict[start:end]=strict[start:end].mean();expected_forbidden[start:end]=forbidden[start:end].mean();groups.append((start,end,int(strict[start:end].sum())));start=end
    def mrr(k):
        for start,end,s in groups:
            if s:
                n=end-start;den=math.comb(n,s)
                return sum(math.comb(n-j,s-1)/den/(start+j) for j in range(1,min(n-s+1,k-start)+1)) if start<k else 0.
        return 0.
    k=min(5,len(scores));discount=1/np.log2(np.arange(2,k+2));ideal=sorted(2.**np.asarray(ideal_grades)-1,reverse=True)[:k];idcg=float(np.dot(ideal,discount));dcg=float(np.dot(expected_gain[:k],discount))
    return dict(ndcg5=dcg/idcg if idcg else 0.,zero_ideal_gain=idcg==0,hit1=float(expected_strict[0]),precision3=float(expected_strict[:3].sum()/3),mrr10=float(mrr(10)),mrr5=float(mrr(5)),recall10=float(expected_strict[:10].sum()/strict_total) if strict_total else 0.,violation1=float(expected_forbidden[0]))
def aggregate(model,stage,records,metadata,queries):
    fields=['ndcg5','hit1','precision3','mrr10','mrr5','recall10','violation1']
    result=dict(model=model,stage=stage,n=len(records),invalid=sum(r.get('invalid',False) for r in records),zero_ideal_gain=sum(r['zero_ideal_gain'] for r in records),metrics={key:float(np.mean([r[key] for r in records])) for key in fields},metadata=metadata,per_query=records)
    result['ndcg5_global_mean']=float(np.mean([r.get('ndcg5_global',r['ndcg5']) for r in records]))
    times=np.asarray([r['wall_seconds'] for r in records]);result['timing']=dict(mean_ms=float(times.mean()*1000),median_ms=float(np.median(times)*1000),p95_ms=float(np.quantile(times,.95)*1000))
    pipeline_times=np.asarray([r.get('pipeline_wall_seconds',r['wall_seconds']) for r in records]);result['timing']['pipeline_mean_ms']=float(pipeline_times.mean()*1000)
    families=sorted({q['family'] for q in queries});rng=np.random.default_rng(SEED)
    index={family:[i for i,q in enumerate(queries) if q['family']==family] for family in families}
    bootstrap=np.array([np.concatenate([index[f] for f in rng.choice(families,len(families))]) for _ in range(5000)])
    ndcg=np.asarray([r['ndcg5'] for r in records]);result['ndcg5_ci95']=np.quantile(ndcg[bootstrap].mean(axis=1),[.025,.975]).tolist()
    cohorts={}
    for name,condition in [('literal',lambda q:q['variant']=='literal'),('paraphrase',lambda q:q['variant']=='paraphrase'),('single_genre',lambda q:len(q['required'])==1 and not q['forbidden']),('combined_genres',lambda q:len(q['required'])==2),('negative_constraints',lambda q:bool(q['forbidden']))]:
        ix=[i for i,q in enumerate(queries) if condition(q)]
        cohorts[name]=dict(n=len(ix),**{key:float(np.mean([records[i][key] for i in ix])) for key in fields})
    result['cohorts']=cohorts
    return result
def main():
    catalog,queries,freeze=read();ids=[r['id'] for r in catalog];index={item:i for i,item in enumerate(ids)};by={r['id']:r for r in catalog};qrels=load(DATA/'qrels.json')
    pools=load(DATA/'shortlists.json');pool_by={r['id']:r for r in pools};all_results=[]
    for folder in sorted((OUT/'retrieval').iterdir()):
        if not (folder/'result.json').exists():continue
        scores=load(folder/'scores.json');assert [r['id'] for r in scores]==[q['id'] for q in queries];meta=load(folder/'result.json')
        rss=folder/'resources.txt'
        if rss.exists():
            match=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',rss.read_text())
            if match:meta['peak_rss_mib_process_max']=int(match[1])/1024
        full=[];pool_records=[]
        for q,row in zip(queries,scores):
            grades=[qrels[q['id']][item] for item in ids];strict_total=sum(g==2 for g in grades);forbidden=[bool(set(q['forbidden'])&set(r['genres'])) for r in catalog]
            common=dict(id=q['id'],wall_seconds=row['wall_seconds'])
            ranking=sorted(range(len(ids)),key=lambda i:(-round(row['scores'][i],12),int(ids[i])))
            full.append(dict(**common,**quality(row['scores'],grades,strict_total,grades,forbidden),zero_scores=not any(row['scores']),ranking=[ids[i] for i in ranking[:10]]))
            chosen=pool_by[q['id']]['tfidf_order'];ix=[index[item] for item in chosen];pg=[grades[i] for i in ix]
            result=quality([row['scores'][i] for i in ix],pg,strict_total,pg,[forbidden[i] for i in ix]);globalq=quality([row['scores'][i] for i in ix],pg,strict_total,grades,[forbidden[i] for i in ix])
            result['ndcg5_global']=globalq['ndcg5'];result['pool_strict_relevant']=sum(g==2 for g in pg)
            pool_rank=sorted(ix,key=lambda i:(-round(row['scores'][i],12),int(ids[i])))
            pool_records.append(dict(**common,**result,ranking=[ids[i] for i in pool_rank],timing_note='Full catalog query scoring reused; not separately measured five-item-only scoring.'))
        all_results.append(aggregate(folder.name,'full_retrieval',full,meta,queries));all_results.append(aggregate(folder.name,'shared_pool',pool_records,meta,queries))
    tfidf_times={r['id']:r['wall_seconds'] for r in load(OUT/'retrieval/tfidf/scores.json')}
    rerankroot=OUT/'reranking'
    if rerankroot.exists():
        for folder in sorted(rerankroot.iterdir()):
            if not (folder/'result.json').exists():continue
            predictions=load(folder/'predictions.json');assert [r['id'] for r in predictions]==[q['id'] for q in queries]
            raw=[];fallback=[]
            for q,row in zip(queries,predictions):
                pool=pool_by[q['id']];base_order=pool['tfidf_order'];pg=[qrels[q['id']][item] for item in base_order];strict_total=sum(g==2 for g in qrels[q['id']].values());invalid=row['prediction']=='invalid'
                order=base_order if invalid else [pool['candidate_map'][c] for c in row['prediction'].split(',')]
                assert len(order)==5 and set(order)==set(base_order)
                grades=[qrels[q['id']][item] for item in order];forbidden=[bool(set(q['forbidden'])&set(by[item]['genres'])) for item in order]
                result=quality([5,4,3,2,1],grades,strict_total,pg,forbidden);globalq=quality([5,4,3,2,1],grades,strict_total,list(qrels[q['id']].values()),forbidden)
                record=dict(id=q['id'],wall_seconds=row['wall_seconds'],pipeline_wall_seconds=row['wall_seconds']+tfidf_times[q['id']],invalid=invalid,finish_reason=row['finish_reason'],throttle_seconds=row['throttle_seconds'],**result,ndcg5_global=globalq['ndcg5'],ranking=order)
                fallback.append(record.copy())
                if invalid:
                    record.update({key:0. for key in ['ndcg5','hit1','precision3','mrr10','mrr5','recall10','ndcg5_global']})
                    # No actual recommendation: conservatively a constraint failure.
                    record['violation1']=1. if q['forbidden'] else 0.;record['ranking']=[]
                raw.append(record)
            metadata=load(folder/'result.json')
            if metadata.get('peak_rss_kib_server'):metadata['peak_rss_mib_process_max']=metadata['peak_rss_kib_server']/1024
            all_results.append(aggregate(folder.name,'shared_pool',raw,metadata,queries));all_results.append(aggregate(folder.name+'+tfidf-fallback','shared_pool',fallback,{**metadata,'fallback_count':sum(r['invalid'] for r in raw)},queries))
    for result in all_results:
        if result['model']=='random':
            result['catalog_coverage5']=None;result['genre_diversity5_valid_only']=None;continue
        unique=set();diversities=[]
        for row in result['per_query']:
            ranking=row['ranking'][:5];unique.update(ranking)
            if len(ranking)>=2:
                pairs=[]
                for i,a in enumerate(ranking):
                    for b in ranking[i+1:]:
                        ga=set(by[a]['genres']);gb=set(by[b]['genres']);pairs.append(1-len(ga&gb)/len(ga|gb))
                diversities.append(float(np.mean(pairs)))
        result['catalog_coverage5']=len(unique)/len(catalog)
        result['genre_diversity5_valid_only']=float(np.mean(diversities)) if diversities else None
    target=OUT/'evaluation';target.mkdir(exist_ok=True)
    complete=sum((OUT/'reranking'/m/'result.json').exists() for m in ['llama','qwen','qwen-nothink','deepseek','gptoss'])==5
    upper=[]
    for q in queries:
        pg=sorted([qrels[q['id']][item] for item in pool_by[q['id']]['tfidf_order']],reverse=True)
        upper.append(quality([5,4,3,2,1],pg,sum(g==2 for g in qrels[q['id']].values()),list(qrels[q['id']].values()),[False]*5)['ndcg5'])
    families=sorted({q['family'] for q in queries});family_ix={f:[i for i,q in enumerate(queries) if q['family']==f] for f in families};rng=np.random.default_rng(SEED)
    boot=np.array([np.concatenate([family_ix[f] for f in rng.choice(families,len(families))]) for _ in range(5000)])
    paired=[]
    for stage,reference in [('full_retrieval','w2v-cbow'),('shared_pool','tfidf')]:
        baseline=next(m for m in all_results if m['stage']==stage and m['model']==reference)
        for m in all_results:
            if m['stage']!=stage or m['model']==reference:continue
            diff=np.array([r['ndcg5'] for r in m['per_query']])-np.array([r['ndcg5'] for r in baseline['per_query']])
            paired.append(dict(stage=stage,reference=reference,model=m['model'],mean_difference=float(diff.mean()),ci95=np.quantile(diff[boot].mean(axis=1),[.025,.975]).tolist()))
    save(target/'comparison.json',dict(complete=complete,query_count=24,families=12,proxy_relevance=True,pool_global_ndcg5_upper_bound=float(np.mean(upper)),paired_differences=paired,models=all_results))
    for stage in ['full_retrieval','shared_pool']:
        print(stage)
        for r in sorted([x for x in all_results if x['stage']==stage],key=lambda x:-x['metrics']['ndcg5']):print(r['model'],round(r['metrics']['ndcg5'],4),'invalid',r['invalid'])
if __name__=='__main__':main()
