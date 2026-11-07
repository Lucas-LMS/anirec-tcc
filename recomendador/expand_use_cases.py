"""One bounded acquisition pass for eight named recommendation scenarios.

No pagination/crawl: <=20 related and one <=50 discovery page per scenario.
Existing recently collected metadata is reused. No user-list data is exported.
"""
import argparse,datetime,json,shutil,time
from pathlib import Path
from anilist_client import AniListClient,MEDIA_FIELDS
from engine import DATA,clean
from repository import Repository

SCENARIOS=[(9756,'Madoka Magica','Mahou Shoujo',None),(35240,'Princess Principal',None,'Espionage'),(134,'Gunslinger Girl',None,'Girls With Guns'),(32979,'Flip Flappers',None,'Female Protagonist'),(52991,'Frieren','Adventure',None),(35839,'A Place Further than the Universe',None,'Coming of Age'),(27989,'Sound! Euphonium','Music',None),(17549,'Non Non Biyori',None,'Iyashikei')]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if not args.execute:print('Eight explicit scenarios; --execute required. No catalogue crawl.');return
    started=time.perf_counter();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();snapshot=DATA/'catalog-snapshot.json';before=json.loads(snapshot.read_text(encoding='utf-8'));records={r['id']:r for r in before if not r.get('isAdult') and r.get('type','ANIME')=='ANIME'};old_ids=set(records);client=AniListClient();repository=Repository(DATA/'anirec.sqlite3');events=[]
    def add(rows):
        additions=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows=[r for r in rows if r and not r.get('isAdult') and r.get('type','ANIME')=='ANIME']
        repository.put_many('AniList',[(r['id'],r.get('idMal'),(r.get('title') or {}).get('english') or (r.get('title') or {}).get('romaji') or str(r['id']),r,clean(r.get('description'))) for r in rows])
        for row in rows:
            if row['id'] not in records:additions.append(row['id'])
            records[row['id']]={**row,'statisticsFetchedAt':now}
        return additions
    for mal,label,genre,tag in SCENARIOS:
        anchor=next((r for r in records.values() if r.get('idMal')==mal),None)
        if anchor is None:
            anchor=client.query('query($id:Int!){Media(idMal:$id,type:ANIME){'+MEDIA_FIELDS+'}}',{'id':mal})['Media'];add([anchor])
        related=client.candidates(anchor['id']);new_related=add(related)
        discoveries=client.discover(genre,list(records),tag=tag);new_discovered=add(discoveries)
        event=dict(anchor_id=anchor['id'],anchor_title=label,genre=genre,tag=tag,related_returned=len(related),discovery_returned=len(discoveries),new_ids=sorted(set(new_related+new_discovered)));events.append(event);print(json.dumps({'anchor':label,'added':len(event['new_ids']),'total':len(records)}),flush=True)
    backup=DATA/'backups';backup.mkdir(exist_ok=True);shutil.copy2(snapshot,backup/('before-use-cases-'+stamp.replace(':','-')+'.json'));snapshot.write_text(json.dumps(list(records.values()),ensure_ascii=False),encoding='utf-8')
    report=dict(protocol='eight-explicit-use-cases-v11',started_at=stamp,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),before=len(old_ids),after=len(records),added=len(set(records)-old_ids),scenarios=events,elapsed_seconds=time.perf_counter()-started,full_catalog_permission_received=False,private_profile_included=False,source='AniList GraphQL',scope='Eight named use cases; first page only; reuse existing snapshot; not a catalogue crawl')
    (Path(__file__).parent/'data/use-case-expansion-v11.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
