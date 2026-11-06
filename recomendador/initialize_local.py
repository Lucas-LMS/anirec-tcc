"""Initialize a new local dataset from public work metadata; never overwrites a profile."""
import json,os
from pathlib import Path
def main():
    root=Path(__file__).parent
    target=Path(os.environ.get('ANIREC_DATA_DIR',str(Path.home()/'tcc-lab/recomendador-private')));target.mkdir(parents=True,exist_ok=True)
    snapshot=target/'catalog-snapshot.json'
    if snapshot.exists():print('Snapshot existente preservado:',snapshot);return
    public=json.loads((root/'online/catalog.json').read_text(encoding='utf-8'))
    rows=[{'id':r['anilist_id'],'idMal':r.get('mal_id'),'type':'ANIME','isAdult':False,'status':r.get('status'),'averageScore':r.get('average_score'),'meanScore':r.get('mean_score'),'popularity':r.get('popularity'),'favourites':r.get('community_favourites'),'statisticsFetchedAt':r.get('statistics_fetched_at'),'title':{'english':r['title'],'romaji':r.get('romaji')},'description':r['text'],'genres':r['genres'],'tags':r['tags'],'coverImage':{'large':r.get('cover')},'siteUrl':r.get('url')} for r in public['records']]
    snapshot.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8');print('Inicializadas',len(rows),'obras públicas em',snapshot)
if __name__=='__main__':main()
