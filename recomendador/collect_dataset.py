"""Explicit educational sample, not a full AniList mirror. Resumable by query cache.
Public seed is four popularity pages plus four known regression anchor works.
No user lists, notes or identifiers are exported.
"""
import json,hashlib,datetime
from pathlib import Path
from anilist_client import AniListClient,MEDIA_FIELDS

def main():
    client=AniListClient();rows={}
    for page in range(1,5):
        query='query($page:Int!){Page(page:$page,perPage:50){media(type:ANIME,isAdult:false,status_not:NOT_YET_RELEASED,sort:POPULARITY_DESC){'+MEDIA_FIELDS+'}}}'
        for row in client.query(query,dict(page=page))['Page']['media']:rows[row['id']]=row
    for mal in [47,144,387,54]:
        row=client.query('query($mal:Int!){Media(idMal:$mal,type:ANIME){'+MEDIA_FIELDS+'}}',dict(mal=mal))['Media']
        if row:rows[row['id']]=row
    target=Path(__file__).parent/'data';target.mkdir(exist_ok=True)
    raw=json.dumps(list(rows.values()),ensure_ascii=False,sort_keys=True,indent=2).encode()
    (target/'anilist-seed.json').write_bytes(raw)
    manifest=dict(source='AniList GraphQL',url='https://graphql.anilist.co',collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),selection='First four popularity pages (ANIME, non-adult, not upcoming), plus MAL 47/144/387/54 regression anchors',count=len(rows),sha256=hashlib.sha256(raw).hexdigest(),sampling_bias='Popularity sample, not representative of all anime',no_user_data=True,full_catalog=False)
    (target/'dataset-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest))
if __name__=='__main__':main()
