"""Synchronize the static deployment from maintained source; no network or secrets."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];source=root/'recomendador/online';target=root/'site';target.mkdir(exist_ok=True)
for p in source.rglob('*'):
    if not p.is_file() or 'assets' in p.relative_to(source).parts or p.name in {'app.js','browser-adapter.js','anilist-import.js'}:continue
    dest=target/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for folder in [target/'assets',source/'assets']:
    folder.mkdir(exist_ok=True)
    for p in list((root/'recomendador/shared').glob('*.js'))+list((root/'recomendador/shared').glob('*.css'))+[source/'browser-adapter.js',source/'anilist-import.js']:
        if p.name!='local-adapter.js':shutil.copy2(p,folder/p.name)
print('Site sincronizado em',target)
