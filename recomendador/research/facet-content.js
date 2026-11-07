/* Development hypothesis, NOT the production recommender. No community or profile input. */
'use strict';
function facetScore(anchor,candidate,taxonomy,idf){
  const norm=s=>s.normalize('NFKC').toLowerCase().trim();
  const categories=['Theme-Action','Cast-Main Cast'];
  if(!anchor.genres.includes('Action'))return null;
  const scores=[];
  for(const category of categories){
    const query=anchor.tags.filter(t=>t.rank>=50&&taxonomy.get(t.name)===category);
    if(!query.length)return null;
    const weight=t=>t.rank/100*Math.sqrt(idf[norm(t.name)]||1);
    const maximum=Math.max(...query.map(weight));
    const target=new Map(candidate.tags.map(t=>[t.name,t.rank/100]));
    const matched=Math.max(0,...query.map(t=>Math.min(t.rank/100,target.get(t.name)||0)*Math.sqrt(idf[norm(t.name)]||1)));
    scores.push(matched/maximum);
  }
  return Math.sqrt(scores[0]*scores[1]);
}
function apply(rows,anchor,taxonomy,idf,mix=.5){
  if(!Number.isFinite(mix)||mix<0||mix>1)throw Error('Invalid mixing weight');
  return rows.map(row=>{const facet=facetScore(anchor,row,taxonomy,idf);return {...row,content_baseline:row.base_score,facet_score:facet,base_score:facet===null?row.base_score:(1-mix)*row.base_score+mix*facet};}).sort((a,b)=>b.base_score-a.base_score||a.key.localeCompare(b.key));
}
module.exports={apply,facetScore};
