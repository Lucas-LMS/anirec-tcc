"""Activate collected AniList records as a new local retrieval snapshot.

Run with the HTTP server stopped. This is offline: collection is separate.
"""
import json,shutil
from engine import DATA
from repository import Repository

def main():
    rows=Repository(DATA/'anirec.sqlite3').recent_anilist(days=36500)
    records=[r for _,r in sorted(rows.items()) if r.get('type','ANIME')=='ANIME' and not r.get('isAdult')]
    target=DATA/'catalog-snapshot.json'
    if target.exists():shutil.copy2(target,DATA/'catalog-snapshot.previous.json')
    temp=target.with_suffix('.tmp');temp.write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8');temp.replace(target)
    print(f'Dataset ativo: {len(records)} obras AniList; snapshot anterior preservado.')
if __name__=='__main__':main()
