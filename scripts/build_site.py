"""Synchronize the static deployment from maintained source; no network or secrets."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];source=root/'recomendador/online';target=root/'site';target.mkdir(exist_ok=True)
for page,template in [('index.html','page.html'),('pesquisa.html','research.html')]:
    html=(root/'recomendador/shared'/template).read_text(encoding='utf-8-sig')
    if template=='research.html':
        html=html.replace('class="pure-mode"','class="pure-mode research-mode"').replace('<nav class="row">','<nav class="row"><a href="index.html">← Voltar ao recomendador simples</a>',1)
    (source/page).write_text(html.replace('<!-- ADAPTER -->','<script src="assets/anilist-import.js"></script><script src="assets/browser-adapter.js"></script>'),encoding='utf-8')
    (root/'recomendador/web'/page).write_text(html.replace('<!-- ADAPTER -->','<script src="assets/local-adapter.js"></script>'),encoding='utf-8')
for p in source.rglob('*'):
    if not p.is_file() or 'assets' in p.relative_to(source).parts or p.name in {'app.js','browser-adapter.js','anilist-import.js'}:continue
    dest=target/p.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for folder in [target/'assets',source/'assets']:
    folder.mkdir(exist_ok=True)
    for p in list((root/'recomendador/shared').glob('*.js'))+list((root/'recomendador/shared').glob('*.css'))+[source/'browser-adapter.js',source/'anilist-import.js']:
        if p.name!='local-adapter.js':shutil.copy2(p,folder/p.name)
print('Site sincronizado em',target)
