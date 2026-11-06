"""Acquire one public Kaggle file, not the large user-rating tables.

No model inference. Preserve the exact download and publisher metadata.
"""
import hashlib,json,urllib.request,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw';RAW.mkdir(parents=True,exist_ok=True)
REF='hernan4444/anime-recommendation-database-2020'
sources={
 'kaggle-metadata.json':f'https://www.kaggle.com/api/v1/datasets/view/{REF}',
 'publisher-readme.md':'https://raw.githubusercontent.com/Hernan4444/MyAnimeList-Database/master/readme.md',
 'anime_with_synopsis.download':f'https://www.kaggle.com/api/v1/datasets/download/{REF}/anime_with_synopsis.csv',
}
manifest=[]
for name,url in sources.items():
    path=RAW/name
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'TCC research/1.0'})
        with urllib.request.urlopen(req,timeout=120) as response:
            blob=response.read(30_000_001)
            assert len(blob)<=30_000_000,'Unexpected large download; stop.'
            path.write_bytes(blob)
    blob=path.read_bytes();manifest.append(dict(file=name,url=url,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
    if name.endswith('.download'):
        if zipfile.is_zipfile(io.BytesIO(blob)):
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                names=z.namelist();assert len(names)==1 and names[0].endswith('.csv'),names
                (RAW/'anime_with_synopsis.csv').write_bytes(z.read(names[0]))
        else:
            assert b'MAL_ID' in blob[:300],blob[:50]
            (RAW/'anime_with_synopsis.csv').write_bytes(blob)
(RAW/'acquisition.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
