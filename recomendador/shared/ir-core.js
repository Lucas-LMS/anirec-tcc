/* Deterministic retrieval core. No DOM, network, fitting or learned ranking weights. */
(function (root) {
  'use strict';
  const norm = value => String(value).normalize('NFKC').toLowerCase().trim();
  const clamp = value => Math.max(0, Math.min(1, value));
  const dot = (a, b) => a.reduce((sum, x, i) => sum + x * b[i], 0);
  const unit = vector => { const length = Math.sqrt(dot(vector, vector)); return length ? vector.map(x => x / length) : vector; };
  const cosine = (a, b) => Math.max(-1, Math.min(1, dot(a, b)));
  const jaccard = (a, b) => { const union = new Set([...a, ...b]); return union.size ? [...new Set(a)].filter(x => b.includes(x)).length / union.size : 0; };
  const stop=new Set('a an the and or of to in on at by for from with as is are was were be been being it its this that these those he she they his her their who which when where while into out up down about through after before during over under than then there here also very can could would should may might has have had do does did will just some any all each both more most other such only own one two'.split(' '));
  const tokens=text=>(String(text||'').normalize('NFKC').toLowerCase().match(/\p{L}+/gu)||[]).filter(word=>!stop.has(word));
  const bmCache=new WeakMap();
  function bm25(records,text,k1=1.2,b=.75){
    let index=bmCache.get(records);
    if(!index){const usable=records.filter(row=>!row.is_adult),df=new Map(),docs=usable.map(row=>{const counts=new Map();for(const word of tokens(row.text))counts.set(word,(counts.get(word)||0)+1);for(const word of counts.keys())df.set(word,(df.get(word)||0)+1);return {counts,length:[...counts.values()].reduce((a,b)=>a+b,0)};});index={df,docs,rows:usable,average:docs.reduce((a,b)=>a+b.length,0)/(docs.length||1)};bmCache.set(records,index);}
    const query=[...new Set(tokens(text))].filter(word=>(index.df.get(word)||0)>1).sort(),idf=new Map(query.map(word=>[word,Math.log(1+(index.rows.length-index.df.get(word)+.5)/(index.df.get(word)+.5))])),upper=(k1+1)*[...idf.values()].reduce((a,b)=>a+b,0),result=new Map();
    index.rows.forEach((row,i)=>{const doc=index.docs[i];let raw=0;for(const word of query){const tf=doc.counts.get(word)||0;if(tf)raw+=idf.get(word)*tf*(k1+1)/(tf+k1*(1-b+b*doc.length/(index.average||1)));}result.set(row.key,{raw,score:upper?raw/upper:0,matched_terms:query.filter(word=>doc.counts.has(word)).sort((a,b)=>idf.get(b)-idf.get(a)||(a<b?-1:a>b?1:0)).slice(0,12)});});return result;
  }
  function communityQuality(row){for(const field of ['average_score','mean_score'])if(Number.isFinite(row[field])&&row[field]>=0&&row[field]<=100)return {value:row[field]/100,source:field};return {value:null,source:null};}
  function topics(item, spoilers = false) {
    const result = {};
    for (const name of item.genres || []) result[norm(name)] = { name, weight: 1 };
    for (const tag of item.tags || []) {
      if (!spoilers && (tag.isGeneralSpoiler || tag.isMediaSpoiler)) continue;
      result[norm(tag.name)] = { name: tag.name, weight: clamp((tag.rank || 0) / 100) };
    }
    return result;
  }
  function affinity(preferences, itemTopics) {
    let positive = 0, negative = 0, positiveHit = 0, negativeHit = 0;
    const explicit = [], matched = []; let positiveCount = 0, matchedPositive = 0;
    for (const [key, p] of Object.entries(preferences)) {
      const rank = itemTopics[key]?.weight || 0;
      if (p.weight > 0) { positive += p.weight; positiveHit += p.weight * rank; positiveCount++; if (rank) matchedPositive++; }
      if (p.weight < 0) { negative -= p.weight; negativeHit -= p.weight * rank; }
      if (p.source === 'preferência explícita') { explicit.push(p.name); if (rank) matched.push(p.name); }
    }
    const coverage = positive ? positiveHit / positive : negative ? .5 : 0;
    const aversion = negative ? negativeHit / negative : 0;
    return { score: clamp(coverage * (1 - aversion)), positive_coverage: coverage, negative_coverage: aversion,
      positive_weight: positive, negative_weight: negative, explicit_count: explicit.length,
      matched_explicit: matched, positive_count: positiveCount, matched_positive_count: matchedPositive };
  }
  function topicIdf(records) {
    const counts = {};
    for (const item of records) for (const key of Object.keys(topics(item, true))) counts[key] = (counts[key] || 0) + 1;
    return Object.fromEntries(Object.entries(counts).map(([key, count]) => [key, Math.log((records.length + 1) / (count + 1)) + 1]));
  }
  function thematic(a, b, idf) {
    const features = item => Object.fromEntries((item.tags || []).filter(t => t.rank >= 50).map(t => [norm(t.name), t.rank / 100 * (idf[norm(t.name)] || 1)]));
    const av = features(a), bv = features(b);
    const denominator = Math.sqrt(Object.values(av).reduce((s, x) => s + x * x, 0) * Object.values(bv).reduce((s, x) => s + x * x, 0));
    const tag = denominator ? Object.entries(av).reduce((s, [key, value]) => s + value * (bv[key] || 0), 0) / denominator : 0;
    const genre = jaccard(a.genres || [], b.genres || []);
    return { score: .85 * tag + .15 * genre, tag, genre };
  }
  function profile(records, ratings = {}, favorites = [], preferred = []) {
    const byKey = new Map(records.map(item => [item.key, item]));
    const validRatings = Object.entries(ratings).filter(([, s]) => Number.isFinite(s) && s > 0 && s <= 10);
    const values = validRatings.map(([, s]) => s), minimum = values.length ? Math.min(...values) : null, maximum = values.length ? Math.max(...values) : null;
    const neutral = values.length ? (minimum + maximum) / 2 : null, half = values.length ? (maximum - minimum) / 2 : 0;
    const weights = {};
    for (const [key, score] of validRatings) if (half && score !== neutral) weights[key] = (score - neutral) / half;
    for (const key of favorites) if (!(key in ratings)) weights[key] = 2;
    const dimensions=records.find(row=>row.vector?.length)?.vector.length||100;
    let positive = Array(dimensions).fill(0), negative = Array(dimensions).fill(0), hasPositive = false, hasNegative = false, total = 0, vectors = 0;
    const themes = {}, names = {};
    for (const [key, weight] of Object.entries(weights)) {
      const item = byKey.get(key); if (!item) continue;
      total += Math.abs(weight);
      if (item.vector?.some(x => x !== 0)) {
        if(item.vector.length!==dimensions)throw Error('Vetores de dimensões diferentes no mesmo perfil.');
        vectors++;
        if (weight > 0) { positive = positive.map((x, i) => x + weight * item.vector[i]); hasPositive = true; }
        else { negative = negative.map((x, i) => x + Math.abs(weight) * item.vector[i]); hasNegative = true; }
      }
      for (const [term, meta] of Object.entries(topics(item))) { themes[term] = (themes[term] || 0) + weight * meta.weight; names[term] = meta.name; }
    }
    const preferences = {};
    for (const [key, weight] of Object.entries(themes).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]) || a[0].localeCompare(b[0])).slice(0, 12))
      preferences[key] = { name: names[key], weight: weight / (total || 1), source: weight > 0 ? 'histórico: aproximação' : 'histórico: afastamento' };
    const inferred = Object.values(preferences).map(x => ({ ...x }));
    for (const name of preferred) preferences[norm(name)] = { name, weight: 1, source: 'preferência explícita' };
    return { positive: hasPositive ? unit(positive) : null, negative: hasNegative ? unit(negative) : null, preferences,
      active: hasPositive || hasNegative || Object.keys(preferences).length > 0,
      info: { rating_min: minimum === null ? null : minimum * 10, rating_max: maximum === null ? null : maximum * 10,
        rating_neutral: neutral === null ? null : neutral * 10, rated_count: values.length, neutral_count: values.filter(s => s === neutral).length,
        positive_count: Object.values(weights).filter(w => w > 0).length, negative_count: Object.values(weights).filter(w => w < 0).length,
        vector_count: vectors, inferred } };
  }
  function rank(options) {
    if(options.pure)options={...options,ratings:{},favorites:[],preferred:[],avoided:[],hidden:[],seenIds:[],personalization:0,exclude_seen:false};
    const { records, anchor, ratings = {}, favorites = [], preferred = [], avoided = [], seenIds = [], hidden = [], params = {} } = options;
    if(!anchor?.vector?.some(x=>x!==0))throw Error('A sinopse não forneceu termos com vetores utilizáveis. Escolha outro anime.');
    if(!anchor.vector.every(Number.isFinite))throw Error('Vetor da referência inválido.');
    const start = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const p = profile(options.profile_records || records, ratings, favorites, preferred), lambda = p.active ? Math.max(0, Math.min(.6, options.personalization ?? .35)) : 0;
    const threshold = options.personal_min_topics ?? .25, idf = options.topic_idf || topicIdf(records);
    const strategy=options.strategy||'vectors',beta={vectors:0,hybrid:.2,bm25:1}[strategy],gamma=options.community_weight??0;
    if(beta===undefined||!Number.isFinite(gamma)||gamma<0||gamma>.1)throw Error('Parâmetros experimentais inválidos.');
    const lexical=beta?bm25(records,anchor.text):new Map();
    const seen = new Set(seenIds.map(Number)), favoriteSet = new Set(favorites), rejected = new Set(hidden), forbidden = new Set(avoided.map(norm));
    const diagnostics = [], rows = [], audit = {};
    const reject = (item, reason, detail) => { audit[reason] = (audit[reason] || 0) + 1; diagnostics.push({ key: item.key, title: item.title, reason, detail }); };
    for (const item of records) {
      const known = seen.has(Number(item.anilist_id)) || favoriteSet.has(item.key);
      if (item.key === anchor.key) { reject(item, 'anchor'); continue; }
      if (rejected.has(item.key)) { reject(item, 'hidden'); continue; }
      if (item.is_adult) { reject(item, 'adult'); continue; }
      if (options.exclude_upcoming !== false && item.status === 'NOT_YET_RELEASED') { reject(item, 'upcoming'); continue; }
      if (options.require_genre && anchor.genres.length && !anchor.genres.some(g => item.genres.includes(g))) { reject(item, 'genre'); continue; }
      const features = topics(item, true), exclusions = [...forbidden].filter(t => t in features);
      if (exclusions.length) { reject(item, 'avoided_topic', exclusions); continue; }
      if (forbidden.size && options.require_tag_metadata && !item.tags?.length) { reject(item, 'missing_tags'); continue; }
      if (!item.vector?.some(x => x !== 0)) { reject(item, 'missing_vector'); continue; }
      if(item.vector.length!==anchor.vector.length||!item.vector.every(Number.isFinite))throw Error('Vetores incompatíveis no catálogo.');
      const text = (cosine(anchor.vector, item.vector) + 1) / 2, thematicScore = thematic(anchor, item, idf), details = affinity(p.preferences, features);
      const pos = p.positive ? cosine(p.positive, item.vector) : null, neg = p.negative ? cosine(p.negative, item.vector) : null;
      const profileText = pos !== null && neg !== null ? clamp(.5 + .5 * (pos - neg)) : pos !== null ? (pos + 1) / 2 : neg !== null ? (1 - neg) / 2 : null;
      const lex=lexical.get(item.key)||{raw:0,score:0,matched_terms:[]},quality=communityQuality(item),referenceComponents={anchor_text:(1-beta)*.5*text,anchor_topics:(1-beta)*.5*thematicScore.score,lexical:beta*lex.score};
      const base = Object.values(referenceComponents).reduce((a,b)=>a+b,0), personal = profileText !== null ? .7 * profileText + .3 * details.score : details.score,userScore=(1-lambda)*base+lambda*personal,gb=quality.value===null?0:gamma*quality.value*(1-base),pb=quality.value===null?0:gamma*quality.value*(1-userScore);
      const safe = topics(item), anchorSafe = topics(anchor);
      rows.push({ ...item, is_seen: known, base_score: base+gb, personalized_score: userScore+pb,baseline_reference_score:.5*text+.5*thematicScore.score,
        bm25_raw:lex.raw,bm25_normalized:lex.score,lexical_matches:lex.matched_terms,community_quality:quality.value,community_source:quality.source,
        general_components:{...referenceComponents,community:gb},personal_components:{...Object.fromEntries(Object.entries(referenceComponents).map(([key,value])=>[key,(1-lambda)*value])),profile_text:profileText===null?0:lambda*.7*profileText,profile_topics:lambda*(profileText===null?1:.3)*details.score,community:pb},
        anchor_cosine: 2 * text - 1, anchor_topic_overlap: thematicScore.score, anchor_tag_cosine: thematicScore.tag,
        profile_text_score: profileText, preference_affinity: details.score, affinity_details: details,
        common_topics: Object.entries(safe).filter(([t]) => t in anchorSafe).map(([, v]) => v.name).slice(0, 8),
        matched_preferences: Object.entries(p.preferences).filter(([t]) => t in features).map(([, meta]) => ({ name: meta.name, source: meta.source })).slice(0, 8),
        contributions: { anchor_text: (1 - lambda) * .5 * text, anchor_topics: (1 - lambda) * .5 * thematicScore.score,
          profile_text: profileText === null ? 0 : lambda * .7 * profileText, profile_topics: lambda * (profileText === null ? 1 : .3) * details.score } });
    }
    const order = field => (a, b) => b[field] - a[field] || a.key.localeCompare(b.key);
    const general = [...rows].sort(order('base_score')), personalized = rows.filter(r => !p.active || !lambda || r.anchor_topic_overlap >= threshold).sort(order('personalized_score'));
    const personalRank = new Map(personalized.map((r, i) => [r.key, i + 1]));
    general.forEach((r, i) => diagnostics.push({ key: r.key, title: r.title, reason: 'eligible', general_rank: i + 1, personal_rank: personalRank.get(r.key) || null }));
    const end = typeof performance !== 'undefined' ? performance.now() : Date.now(); audit.eligible = general.length;
    return { anchor, general, personalized, diagnostics, filter_audit: audit, profile_active: p.active, profile_info: p.info,
      personalization: lambda, params:{...params,retrieval_strategy:strategy,bm25_k1:1.2,bm25_b:.75,lexical_weight:beta,community_weight:gamma}, filters: { pure:!!options.pure,personal_min_topics: threshold,exclude_upcoming:options.exclude_upcoming!==false,require_genre:!!options.require_genre,require_tag_metadata:!!options.require_tag_metadata,exclude_seen:!!options.exclude_seen }, candidate_count: records.length,
      eligible_count: general.length, personal_eligible_count: personalized.length, unseen_count: general.filter(r => !r.is_seen).length,
      personal_unseen_count: personalized.filter(r => !r.is_seen).length, ranking_ms: end - start, total_ms: end - start,
      recommendation_sets: { general_all: general.slice(0, 10), general_unseen: general.filter(r => !r.is_seen).slice(0, 10),
        personal_all: personalized.slice(0, 10), personal_unseen: personalized.filter(r => !r.is_seen).slice(0, 10) } };
  }
  function study(options){
    const variants=[['vectors','Vetores + temas','vectors',0],['bm25','Somente BM25','bm25',0],['hybrid','Híbrido BM25 + vetores','hybrid',0],['hybrid_community','Híbrido + comunidade 5%','hybrid',.05]],runs=variants.map(([id,label,strategy,weight])=>({id,label,result:rank({...options,strategy,community_weight:weight})})),pool=new Map();
    for(const run of runs)for(const mode of ['general','personalized'])for(const row of (mode==='personalized'&&run.result.profile_active?run.result[mode].filter(row=>!row.is_seen&&!(options.ratings?.[row.key]>0)):run.result[mode]).slice(0,10))pool.set(row.key,{key:row.key,title:row.title,text:row.text,genres:row.genres,tags:row.tags,url:row.url});
    return {format:'anirec-human-study-v1',created_at:new Date().toISOString(),anchor:{key:options.anchor.key,title:options.anchor.title,text:options.anchor.text},profile_active:runs[0].result.profile_active,filters:runs[0].result.filters,personalization:runs[0].result.personalization,candidate_count:options.records.length,pure:!!options.pure,systems:runs.map(run=>({id:run.id,label:run.label,params:run.result.params,ranking_ms:run.result.ranking_ms,general:run.result.general.slice(0,10).map(row=>({key:row.key,score:row.base_score})),personalized:(run.result.profile_active?run.result.personalized.filter(row=>!row.is_seen&&!(options.ratings?.[row.key]>0)):run.result.personalized).slice(0,10).map(row=>({key:row.key,score:row.personalized_score}))})),similarity_pool_keys:[...new Set(runs.flatMap(run=>run.result.general.slice(0,10).map(row=>row.key)))],preference_pool_keys:[...new Set(runs.flatMap(run=>(run.result.profile_active?run.result.personalized.filter(row=>!row.is_seen&&!(options.ratings?.[row.key]>0)):run.result.personalized).slice(0,10).map(row=>row.key)))],preference_policy:'when profile active: unseen, not a manual favorite, and no score supplied in profile',pool:[...pool.values()].sort((a,b)=>a.key<b.key?-1:a.key>b.key?1:0)};
  }
  const api = { norm, unit, cosine, topics, affinity, topicIdf, thematic, profile, rank,bm25,communityQuality,study };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AniRecIR = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
