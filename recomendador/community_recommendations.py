"""Optional pairwise recommendation evidence; absence never lowers a score."""
import copy,math

def apply(result,evidence,weight=.35,support_scale=20.):
    if not math.isfinite(weight) or not 0<=weight<=.5:raise ValueError('Invalid pairwise community weight')
    if not math.isfinite(support_scale) or support_scale<=0:raise ValueError('Invalid support scale')
    result=copy.deepcopy(result)
    votes={int(e['target_id']):float(e['rating']) for e in evidence.get('edges',[]) if e.get('target_id') and isinstance(e.get('rating'),(int,float)) and math.isfinite(e['rating'])}
    personal_keys={r['key'] for r in result['personalized']};matched=0
    for row in result['general']:
        rating=votes.get(row.get('anilist_id'));support=max(0.,rating or 0.);strength=support/(support+support_scale)
        base=row['base_score'];personal=row['personalized_score'];gb=weight*strength*(1-base);pb=weight*strength*(1-personal)
        row.update(content_base_score=base,content_personalized_score=personal,base_score=base+gb,personalized_score=personal+pb,
                   community_recommendation=dict(rating=rating,strength=strength,general_bonus=gb,personal_bonus=pb,anchor_id=evidence.get('anchor_id')))
        row.setdefault('general_components',dict(anchor_content=base))['pairwise_community']=gb
        row.setdefault('personal_components',dict(profile_content=personal))['pairwise_community']=pb
        if support:matched+=1
    result['general'].sort(key=lambda r:(-r['base_score'],r['key']))
    result['personalized']=sorted((r for r in result['general'] if r['key'] in personal_keys),key=lambda r:(-r['personalized_score'],r['key']))
    gr={r['key']:i+1 for i,r in enumerate(result['general'])};pr={r['key']:i+1 for i,r in enumerate(result['personalized'])}
    for row in result['diagnostics']:
        if row['reason']=='eligible':row.update(general_rank=gr[row['key']],personal_rank=pr.get(row['key']))
    result['community_recommendations']={k:v for k,v in evidence.items() if k!='edges'}|dict(enabled=True,weight=weight,support_scale=support_scale,observed_edges=len(votes),eligible_positive_matches=matched,policy='score + weight * max(0,net_votes)/(max(0,net_votes)+support_scale) * (1-score); missing/nonpositive evidence: unchanged')
    result['params'].update(pairwise_community_weight=weight,pairwise_support_scale=support_scale)
    g,p=result['general'],result['personalized'];result['recommendation_sets']=dict(general_all=g[:10],general_unseen=[r for r in g if not r['is_seen']][:10],personal_all=p[:10],personal_unseen=[r for r in p if not r['is_seen']][:10])
    return result
