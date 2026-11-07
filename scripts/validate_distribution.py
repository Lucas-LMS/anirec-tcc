"""Validate public runtime completeness, relative links and absence of secrets."""
import hashlib,json,re,sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[1];site=root/'site'
for file in ['index.html','pesquisa.html','dataset.html','laboratorio.html','avaliacao.html','experimentos.html','assets/evaluation-core.js','lab/evaluation.js','lab/benchmark.js','lab/retrieval-benchmark.json','catalog.json','assets/app.js','assets/ir-core.js','lab/models.json','lab/corpus.sqlite3','lab/chart.umd.js']:assert (site/file).is_file(),file
catalog=json.loads((site/'catalog.json').read_text(encoding='utf-8'));manifest=json.loads((site/'lab/models.json').read_text(encoding='utf-8'))
assert manifest['row_keys']==[r['key'] for r in catalog['records']]
for model in manifest['models']:assert hashlib.sha256((site/model['file']).read_bytes()).hexdigest()==model['sha256']
for html in site.glob('*.html'):
    text=html.read_text(encoding='utf-8');assert 'href="/"' not in text,'Absolute root link breaks project Pages'
    for path in re.findall(r'(?:src|href)="([^"#]+)"',text):
        if path.startswith(('http:','https:','data:','mailto:')):continue
        assert (site/path).is_file(),f'{html.name}: missing {path}'
with sqlite3.connect(site/'lab/corpus.sqlite3') as db:
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert db.execute('SELECT COUNT(*) FROM works').fetchone()[0]==len(catalog['records'])
for p in root.rglob('*'):
    if not p.is_file() or any(part in {'.git','.venv','tmp','__pycache__'} for part in p.relative_to(root).parts):continue
    assert p.name not in {'profile.json','catalog-snapshot.json'},'Private state included'
    assert not re.search(rb'(?:gsk_[A-Za-z0-9]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)',p.read_bytes()),'Possible secret in '+str(p)
print('Distribution validated:',len(catalog['records']),'public works;',len(manifest['models']),'models')
