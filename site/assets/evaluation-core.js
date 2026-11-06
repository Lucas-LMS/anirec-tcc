/* Human grades only. Missing judgments are never treated as irrelevant. */
(function(root){'use strict';
  const valid=value=>Number.isInteger(value)&&value>=0&&value<=3;
  function metrics(ranking,judgments,poolKeys){
    const keys=ranking.slice(0,10).map(row=>typeof row==='string'?row:row.key),k=keys.length,observed=keys.filter(key=>valid(judgments[key])).length,pool=[...new Set(poolKeys)],poolObserved=pool.filter(key=>valid(judgments[key])).length;
    let precision=null,ndcg=null,zeroRelevance=false;
    if(k&&observed===k){precision=keys.filter(key=>judgments[key]>=2).length/k;if(poolObserved===pool.length){const gain=(grade,i)=>(2**grade-1)/Math.log2(i+2),dcg=keys.reduce((sum,key,i)=>sum+gain(judgments[key],i),0),ideal=pool.map(key=>judgments[key]).sort((a,b)=>b-a).slice(0,k).reduce((sum,grade,i)=>sum+gain(grade,i),0);zeroRelevance=ideal===0;ndcg=ideal?dcg/ideal:null;}}
    return {k,judged_top_k:observed,top_k_complete:k>0&&observed===k,pool_judged:poolObserved,pool_total:pool.length,pool_complete:poolObserved===pool.length,precision,ndcg,zero_relevance_pool:zeroRelevance,relevance_threshold:2,gain:'2^grade-1',discount:'log2(rank+1)',ideal_scope:'judged union pool for this frozen query context'};
  }
  const api={metrics,valid};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AniRecEvaluation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
