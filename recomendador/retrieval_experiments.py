"""Auditable BM25 and bounded community bonus. No fitting or learned weights."""
import collections,math,copy
from engine import tokenize
STOP=set('a an the and or of to in on at by for from with as is are was were be been being it its this that these those he she they his her their who which when where while into out up down about through after before during over under than then there here also very can could would should may might has have had do does did will just some any all each both more most other such only own one two'.split())
def bm25(records,text,k1=1.2,b=.75):
    records=[r for r in records if not r.get('is_adult')]
    docs=[collections.Counter(w for w in tokenize(r.get('text','')) if w not in STOP) for r in records];n=len(docs)
    df=collections.Counter(w for doc in docs for w in doc);average=sum(sum(d.values()) for d in docs)/(n or 1)
    query=sorted({w for w in tokenize(text) if w not in STOP and df[w]>1})
    idf={w:math.log(1+(n-df[w]+.5)/(df[w]+.5)) for w in query};upper=(k1+1)*sum(idf.values());result={}
    for row,doc in zip(records,docs):
        length=sum(doc.values());raw=sum(idf[w]*doc[w]*(k1+1)/(doc[w]+k1*(1-b+b*length/(average or 1))) for w in query if doc[w])
        matches=sorted((w for w in query if doc[w]),key=lambda w:(-idf[w],w))[:12]
        result[row['key']]={'raw':raw,'score':raw/upper if upper else 0.,'matched_terms':matches}
    return result

def study(result,records,profile_fingerprint=None,evaluation_excluded=None):
    variants=[('vectors','Vetores + temas','vectors',0),('bm25','Somente BM25','bm25',0),('hybrid','Híbrido BM25 + vetores','hybrid',0),('hybrid_community','Híbrido + comunidade 5%','hybrid',.05)];systems=[];pool={};evaluation_excluded=set(evaluation_excluded or [])
    for identity,label,strategy,weight in variants:
        value=apply(result,records,strategy,weight)
        if value['profile_active']:value['personalized']=[row for row in value['personalized'] if not row['is_seen'] and row['key'] not in evaluation_excluded]
        for mode in ['general','personalized']:
            for row in value[mode][:10]:pool[row['key']]={key:row.get(key) for key in ['key','title','text','genres','tags','url']}
        systems.append(dict(id=identity,label=label,params=value['params'],general=[dict(key=r['key'],score=r['base_score']) for r in value['general'][:10]],personalized=[dict(key=r['key'],score=r['personalized_score']) for r in value['personalized'][:10]]))
    return dict(format='anirec-human-study-v1',anchor=result['anchor'],candidate_count=result['candidate_count'],profile_active=result['profile_active'],pure=result['filters'].get('pure',False),profile_fingerprint=profile_fingerprint,similarity_pool_keys=sorted({r['key'] for system in systems for r in system['general']}),preference_pool_keys=sorted({r['key'] for system in systems for r in system['personalized']}),preference_policy='when profile active: unseen, not a manual favorite, and no score supplied in profile',systems=systems,pool=sorted(pool.values(),key=lambda r:r['key']))
def quality(row):
    for key in ['average_score','mean_score']:
        value=row.get(key)
        if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and 0<=value<=100:return value/100,key
    return None,None
def apply(result,records,strategy='vectors',community_weight=0.):
    if strategy not in {'vectors','hybrid','bm25'}:raise ValueError('Estratégia de recuperação inválida.')
    if not math.isfinite(community_weight) or not 0<=community_weight<=.1:raise ValueError('Bônus comunitário deve estar entre 0 e 0,10.')
    result=copy.deepcopy(result);lam=result['personalization'];beta={'vectors':0.,'hybrid':.2,'bm25':1.}[strategy]
    lexical=bm25(records,result['anchor']['text']) if beta else {}
    for row in result['general']:
        lex=lexical.get(row['key'],{'raw':0.,'score':0.,'matched_terms':[]});ref={'anchor_text':(1-beta)*.5*(row['anchor_cosine']+1)/2,'anchor_topics':(1-beta)*.5*row['anchor_topic_overlap'],'lexical':beta*lex['score']}
        reference=sum(ref.values());ptext=row['contributions']['profile_text'];ptopics=row['contributions']['profile_topics'];personal=(1-lam)*reference+ptext+ptopics
        q,source=quality(row);gb=community_weight*q*(1-reference) if q is not None else 0.;pb=community_weight*q*(1-personal) if q is not None else 0.
        row.update(baseline_reference_score=.5*(row['anchor_cosine']+1)/2+.5*row['anchor_topic_overlap'],base_score=reference+gb,personalized_score=personal+pb,bm25_raw=lex['raw'],bm25_normalized=lex['score'],lexical_matches=lex['matched_terms'],community_quality=q,community_source=source,general_components={**ref,'community':gb},personal_components={**{key:(1-lam)*value for key,value in ref.items()},'profile_text':ptext,'profile_topics':ptopics,'community':pb})
    result['general'].sort(key=lambda row:(-row['base_score'],row['key']));eligible={r['key'] for r in result['personalized']};result['personalized']=sorted((r for r in result['general'] if r['key'] in eligible),key=lambda row:(-row['personalized_score'],row['key']))
    g,p=result['general'],result['personalized'];ranks={r['key']:i+1 for i,r in enumerate(g)};personal_ranks={r['key']:i+1 for i,r in enumerate(p)}
    for row in result['diagnostics']:
        if row['reason']=='eligible':row.update(general_rank=ranks[row['key']],personal_rank=personal_ranks.get(row['key']))
    result['recommendation_sets']={'general_all':g[:10],'general_unseen':[r for r in g if not r['is_seen']][:10],'personal_all':p[:10],'personal_unseen':[r for r in p if not r['is_seen']][:10]}
    result['params']={**result['params'],'retrieval_strategy':strategy,'bm25_k1':1.2,'bm25_b':.75,'lexical_weight':beta,'community_weight':community_weight,'community_policy':'score + gamma * (weighted_score/100 or mean_fallback) * (1-score); missing score: no bonus'}
    return result
