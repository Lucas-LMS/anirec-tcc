"""Auditable interest coverage, separate from anime-to-anime similarity."""
def theme_affinity(preferences,item_topics):
    positive=sum(p['weight'] for p in preferences.values() if p['weight']>0)
    negative=sum(-p['weight'] for p in preferences.values() if p['weight']<0)
    positive_hit=sum(p['weight']*item_topics[t]['weight'] for t,p in preferences.items() if p['weight']>0 and t in item_topics)
    negative_hit=sum(-p['weight']*item_topics[t]['weight'] for t,p in preferences.items() if p['weight']<0 and t in item_topics)
    coverage=positive_hit/positive if positive else .5 if negative else 0.
    aversion=negative_hit/negative if negative else 0.
    score=max(0.,min(1.,coverage*(1-aversion)))
    explicit=[(t,p) for t,p in preferences.items() if p.get('source')=='preferência explícita']
    return dict(score=score,positive_coverage=coverage,negative_coverage=aversion,
                positive_weight=positive,negative_weight=negative,
                matched_explicit=[p['name'] for t,p in explicit if t in item_topics],
                explicit_count=len(explicit),
                matched_positive_count=sum(p['weight']>0 and t in item_topics for t,p in preferences.items()),
                positive_count=sum(p['weight']>0 for p in preferences.values()))
