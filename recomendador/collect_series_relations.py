"""Collect lightweight official relations only for IDs already in our snapshot.

No recursive collection of descriptions or catalogue pagination. Neighbours are
auxiliary graph nodes, not newly ranked dataset documents.
"""
import argparse,datetime,hashlib,json,time
from pathlib import Path
from anilist_client import AniListClient
from engine import DATA

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    if not args.execute:print('Explicit --execute required; existing snapshot IDs only.');return
    root=Path(__file__).parent;out=root/'online';snapshot=json.loads((DATA/'catalog-snapshot.json').read_text());ids=sorted(r['id'] for r in snapshot if not r.get('isAdult') and r.get('type','ANIME')=='ANIME');client=AniListClient();nodes={};edges=[];queried=[];start=time.perf_counter()
    fields='id type title{english romaji} format status startDate{year month day}'
    query='query($ids:[Int]){Page(page:1,perPage:50){media(id_in:$ids,type:ANIME){'+fields+' relations{edges{relationType node{'+fields+'}}}}}}'
    for offset in range(0,len(ids),50):
        rows=client.query(query,{'ids':ids[offset:offset+50]})['Page']['media']
        for row in rows:
            queried.append(row['id']);nodes[str(row['id'])]={k:v for k,v in row.items() if k!='relations'}
            for edge in row['relations']['edges']:
                n=edge['node']
                if n.get('type')=='ANIME':nodes.setdefault(str(n['id']),n);edges.append({'from':row['id'],'to':n['id'],'type':edge['relationType']})
        print(json.dumps({'relations_processed':min(offset+50,len(ids)),'total':len(ids),'edges':len(edges)}),flush=True)
    missing=sorted(set(ids)-set(queried))
    report={'format':'anirec-official-relations-v1','source':'AniList GraphQL Media.relations','fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'queried_count':len(queried),'missing_ids':missing,'catalog_sha256':hashlib.sha256((out/'catalog.json').read_bytes()).hexdigest(),'nodes':nodes,'edges':edges,'recursive_fetch':False,'elapsed_seconds':time.perf_counter()-start}
    (out/'franchises.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')),encoding='utf-8');(root/'data/series-relations-protocol-v12.json').write_text(json.dumps({k:v for k,v in report.items() if k not in ['nodes','edges']}|{'auxiliary_node_count':len(nodes),'edge_count':len(edges)},indent=2),encoding='utf-8');print(json.dumps({'complete':True,'queries':len(queried),'nodes':len(nodes),'edges':len(edges),'missing_ids':missing}),flush=True)

if __name__=='__main__':main()
