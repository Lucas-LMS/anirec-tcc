/* Run from any directory: node scripts/research_content_facets.js */
const fs=require('fs'),path=require('path'),assert=require('assert'),root=path.resolve(__dirname,'..'),base=path.join(root,'recomendador'),ir=require(base+'/shared/ir-core.js'),series=require(base+'/shared/franchise-core.js'),facet=require(base+'/research/facet-content.js');
const read=p=>JSON.parse(fs.readFileSync(base+'/'+p)),catalog=read('online/catalog.json'),graph=series.build(read('online/franchises.json')),taxonomy=new Map(read('online/taxonomy.json').tags.map(t=>[t.name,t.category]));
const references=[143270,1575,9253,20464,21827,98444,19,199,457];
const report=[];
for(const id of references){
 const anchor=catalog.records.find(r=>r.anilist_id===id);if(!anchor)continue;
 const original=ir.rank({records:catalog.records,anchor,pure:true,topic_idf:catalog.topic_idf});
 const input=JSON.stringify(original.general),rows=facet.apply(original.general,anchor,taxonomy,catalog.topic_idf);
 assert.equal(input,JSON.stringify(original.general));
 assert.deepEqual(new Set(rows.map(r=>r.key)),new Set(original.general.map(r=>r.key)));
 for(const row of rows)assert(Number.isFinite(row.base_score)&&row.base_score>=0&&row.base_score<=1);
 assert.deepEqual(facet.apply(original.general,anchor,taxonomy,catalog.topic_idf,0).map(r=>r.base_score),original.general.map(r=>r.base_score));
 const before=series.group(original.general,graph,{anchor}),after=series.group(rows,graph,{anchor});
 const rank=list=>{const i=list.findIndex(r=>r.anilist_id===101014);return i<0?null:i+1;};
 report.push({anchor:anchor.title,anchor_id:id,applicable:rows.some(r=>r.facet_score!==null),eligible:rows.length,overlap_at_10:before.slice(0,10).filter(r=>after.slice(0,10).some(s=>r.series_group.id===s.series_group.id)).length,spyce_before:rank(before),spyce_after:rank(after),before:before.slice(0,20).map(r=>r.title),after:after.slice(0,20).map(r=>r.title)});
}
const result={status:'development hypothesis, not independent relevance validation or production change',parameters:{mix:.5,tag_cutoff:50,categories:['Theme-Action','Cast-Main Cast'],applicability:'Action genre and both anchor facets; otherwise baseline',profile:false,community:false},report};
fs.writeFileSync(base+'/data/content-facets-development.json',JSON.stringify(result,null,2));
console.log(JSON.stringify(report.map(({before,after,...r})=>r),null,2));
