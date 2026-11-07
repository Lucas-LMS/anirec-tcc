/* Official relation graph only. No title guessing and no ranking-model changes. */
(function(root){'use strict';
  const allowed=new Set(['PREQUEL','SEQUEL','SIDE_STORY','SUMMARY','COMPILATION','CONTAINS']);
  function build(data){const parent=new Map(),prequels=new Map();const find=id=>{id=String(id);if(!parent.has(id))parent.set(id,id);let x=id;while(parent.get(x)!==x)x=parent.get(x);while(parent.get(id)!==id){const next=parent.get(id);parent.set(id,x);id=next;}return x;};
    for(const edge of data?.edges||[])if(allowed.has(edge.type)){const a=find(edge.from),b=find(edge.to);if(a!==b)parent.set(a<b?b:a,a<b?a:b);if(edge.type==='PREQUEL'){if(!prequels.has(String(edge.from)))prequels.set(String(edge.from),new Set());prequels.get(String(edge.from)).add(String(edge.to));}if(edge.type==='SEQUEL'){if(!prequels.has(String(edge.to)))prequels.set(String(edge.to),new Set());prequels.get(String(edge.to)).add(String(edge.from));}}
    return {key:item=>find(item.anilist_id??item),nodes:data?.nodes||{},prequels,source:data?.source||'unavailable'};
  }
  function group(rows,index,options={}){const key=row=>row.anilist_id?index.key(row):row.key,anchorGroup=options.anchor?.anilist_id?index.key(options.anchor):null,known=new Set((options.knownIds||[]).map(id=>index.key(id))),knownIndividual=new Set((options.knownIds||[]).map(String)),groups=new Map();
    for(const row of rows)if(row.is_seen)known.add(key(row));
    for(const row of rows){const id=key(row);if(id===anchorGroup)continue;if(!groups.has(id))groups.set(id,[]);groups.get(id).push(row);}
    const result=[];for(const [id,members] of groups){if(options.unseen&&known.has(id))continue;const ids=new Set(members.map(r=>String(r.anilist_id))),date=row=>{const d=index.nodes[String(row.anilist_id)]?.startDate;return d?.year?d.year*10000+(d.month||1)*100+(d.day||1):99999999;};const entry=[...members].sort((a,b)=>{const ap=[...(index.prequels.get(String(a.anilist_id))||[])].some(v=>ids.has(v)),bp=[...(index.prequels.get(String(b.anilist_id))||[])].some(v=>ids.has(v));return date(a)-date(b)||Number(ap)-Number(bp)||String(a.key).localeCompare(String(b.key));})[0];const needsPrequel=[...(index.prequels.get(String(entry.anilist_id))||[])].some(id=>!ids.has(id)&&!knownIndividual.has(id));if(options.unseen&&needsPrequel)continue;result.push({...entry,needs_prequel:needsPrequel,is_seen:known.has(id),series_group:{id,best:members[0],members:[...members].sort((a,b)=>date(a)-date(b)||a.key.localeCompare(b.key)),known:known.has(id)}});}
    return result;
  }
  const api={build,group,allowed:[...allowed]};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AniRecSeries=api;
})(typeof globalThis!=='undefined'?globalThis:this);
