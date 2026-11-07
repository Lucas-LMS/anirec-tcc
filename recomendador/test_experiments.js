const assert=require('node:assert/strict'),fs=require('node:fs'),core=require('./shared/ir-core.js'),evaluation=require('./shared/evaluation-core.js');let maximum=0,comparisons=0;
for(const fixture of JSON.parse(fs.readFileSync(process.argv[2],'utf8'))){const result=core.rank(fixture.options);for(const row of result.general){for(const [key,value] of Object.entries(fixture.expected[row.key])){if(value===null)assert.equal(row[key],null);else{const d=Math.abs(value-row[key]);maximum=Math.max(maximum,d);comparisons++;assert.ok(d<1e-6,`${row.key}/${key}: ${d}`);}}for(const [field,components] of [['base_score','general_components'],['personalized_score','personal_components']])assert.ok(Math.abs(row[field]-Object.values(row[components]).reduce((a,b)=>a+b,0))<1e-10);}}
const fifty=core.profile([{key:'x',vector:Array(50).fill(.1),genres:[],tags:[]}],{},['x']);assert.equal(fifty.positive.length,50);assert.ok(fifty.positive.every(Number.isFinite));
const missing=evaluation.metrics(['a','b'],{a:3},['a','b']);assert.equal(missing.precision,null);assert.equal(missing.ndcg,null);
const complete=evaluation.metrics(['a','b'],{a:2,b:3},['a','b']);assert.equal(complete.precision,1);assert.ok(Math.abs(complete.ndcg-((3+7/Math.log2(3))/(7+3/Math.log2(3))))<1e-12);
const partial=evaluation.metrics(['a'],{a:3},['a','b']);assert.equal(partial.precision,1);assert.equal(partial.ndcg,null);
const zero=evaluation.metrics(['a'],{a:0},['a']);assert.equal(zero.precision,0);assert.equal(zero.ndcg,null);assert.equal(zero.zero_relevance_pool,true);
console.log(JSON.stringify({experimental_numeric_comparisons:comparisons,maximum_difference:maximum,glove_50d_profile:'passed',human_metrics_missing_ideal_zero_cases:'passed'}));

const tiny=['anchor','rated','favorite','unseen'].map(key=>({key,title:key,text:'police city investigation',vector:[1,0],genres:['Action'],tags:[]}));const holdout=core.study({records:tiny,anchor:tiny[0],ratings:{rated:8},favorites:['favorite'],preferred:['Action'],personal_min_topics:0});assert.deepEqual(holdout.preference_pool_keys,['unseen']);assert.ok(holdout.similarity_pool_keys.includes('rated'));console.log('Human preference holdout excludes supplied ratings and favorites: PASS');

// Missing or incompatible vectors must not produce convincing-looking rankings.
{ const anchor={key:'a',vector:[0,0],text:'empty',genres:[],tags:[]};assert.throws(()=>core.rank({records:[],anchor}),/sinopse/);anchor.vector=[1,0];assert.throws(()=>core.rank({records:[{key:'b',vector:[1,0,0],genres:[],tags:[]}],anchor}),/incompat/); }
