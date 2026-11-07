"""Refresh aggregate public AniList statistics without changing saved notes.

Run with the local server stopped; --execute required. Backup stays private.
"""
import argparse,datetime,json,shutil
from anilist_client import AniListClient
from engine import DATA

def main():
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');args=p.parse_args()
    if not args.execute:print('Stop the local server, then run with --execute.');return
    path=DATA/'profile.json';profile=json.loads(path.read_text(encoding='utf-8'));name=profile.get('username')
    if not name:print('No imported username; no change.');return
    user=AniListClient().user(name);statistics=(user or {}).get('statistics')
    if not statistics:raise ValueError('Public statistics unavailable; saved profile preserved.')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();backup=DATA/'backups';backup.mkdir(exist_ok=True);shutil.copy2(path,backup/('profile-before-frequency-'+stamp.replace(':','-')+'.json'))
    before={k:v for k,v in profile.items() if k not in ['user','statistics_fetched_at']};profile['user']=profile.get('user') or {};profile['user']['statistics']=statistics;profile['statistics_fetched_at']=stamp
    assert before=={k:v for k,v in profile.items() if k not in ['user','statistics_fetched_at']}
    path.write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8');print('Aggregate statistics refreshed; notes, interests and favorites preserved. Private backup created.')

if __name__=='__main__':main()
