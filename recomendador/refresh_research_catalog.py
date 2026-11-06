"""Bounded scenario-driven catalog expansion and metadata refresh. No catalog crawl."""
import argparse,datetime,json,shutil,sqlite3,time
from pathlib import Path
from anilist_client import AniListClient,MEDIA_FIELDS
from engine import DATA,clean
from repository import Repository

ANCHORS=[(50709,'Lycoris Recoil'),(9253,'Steins;Gate'),(33352,'Violet Evergarden'),(34798,'Laid-Back Camp'),(20583,'Haikyu!!'),(19,'Monster'),(199,'Spirited Away'),(457,'Mushishi')]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    if not args.execute:print('Explicit execution required: --execute. Eight anchor scenarios, at most 20 related + 50 genre candidates each.');return
    start=time.time();client=AniListClient();repository=Repository(DATA/'anirec.sqlite3')
    with repository.connect() as db:existing={int(key):json.loads(raw) for key,raw in db.execute("SELECT source_id,raw_json FROM media WHERE source='AniList'")}
    snapshot=DATA/'catalog-snapshot.json';before=json.loads(snapshot.read_text(encoding='utf-8'));eligible=lambda r:r.get('type','ANIME')=='ANIME' and not r.get('isAdult')
    records={r['id']:r for r in existing.values() if eligible(r)};events=[];stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for mal,title in ANCHORS:
        anchor=next((r for r in records.values() if r.get('idMal')==mal),None)
        if anchor is None:anchor=client.query('query($id:Int!){Media(idMal:$id,type:ANIME){'+MEDIA_FIELDS+'}}',{'id':mal})['Media'];records[anchor['id']]=anchor
        related=client.candidates(anchor['id']);genre=(anchor.get('genres') or [None])[0];discovered=client.discover(genre,list(records)) if genre else []
        additions=[]
        for row in related+discovered:
            if eligible(row):
                if row['id'] not in records:additions.append(row['id'])
                records[row['id']]=row
        events.append({'anchor_id':anchor['id'],'anchor_title':title,'genre':genre,'related_returned':len(related),'discovery_returned':len(discovered),'new_ids':sorted(set(additions))});print(json.dumps({'stage':'expand','anchor':title,'added':len(set(additions)),'pool':len(records)}),flush=True)
    # One pass over IDs already in the working set, not pages of the service catalog.
    ids=sorted(records);refreshed={}
    for i in range(0,len(ids),50):
        result=client.query('query($ids:[Int]){Page(page:1,perPage:50){media(type:ANIME,id_in:$ids){'+MEDIA_FIELDS+'}}}',{'ids':ids[i:i+50]})['Page']['media']
        for row in result:
            if eligible(row):refreshed[row['id']]={**row,'statisticsFetchedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        repository.put_many('AniList',[(r['id'],r.get('idMal'),(r.get('title') or {}).get('english') or (r.get('title') or {}).get('romaji') or str(r['id']),r,clean(r.get('description'))) for r in result])
        print(json.dumps({'stage':'refresh','processed':min(i+50,len(ids)),'total':len(ids)}),flush=True)
    # Preserve previous metadata for unavailable IDs, explicitly report failed refresh.
    missing=sorted(set(records)-set(refreshed));records.update(refreshed)
    backup=DATA/'backups';backup.mkdir(exist_ok=True);shutil.copy2(snapshot,backup/('catalog-before-research-'+stamp.replace(':','-')+'.json'))
    snapshot.write_text(json.dumps(list(records.values()),ensure_ascii=False),encoding='utf-8')
    report={'protocol':'eight-anchor-expansion-v1','started_at':stamp,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_public_snapshot':len(before),'before_cached_nonadult':sum(eligible(r) for r in existing.values()),'after_public_snapshot':len(records),'new_vs_snapshot':len(set(records)-{r['id'] for r in before}),'fields':['averageScore','meanScore','popularity','favourites','scoreDistribution'],'non_null':{k:sum(r.get(k) is not None for r in records.values()) for k in ['averageScore','meanScore','popularity','favourites']},'not_refreshed_ids':missing,'scenarios':events,'elapsed_seconds':time.time()-start,'full_catalog_permission_received':False,'private_profile_included':False}
    target=Path(__file__).parent/'data/research-expansion.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
