"""Validate public runtime completeness, relative links and absence of secrets."""
import gzip,hashlib,json,re,sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[1];site=root/'site'
for file in ['index.html','pesquisa.html','perfil.html','lab/profile-dashboard.js','assets/user-statistics.js','dataset.html','laboratorio.html','avaliacao.html','experimentos.html','assets/evaluation-core.js','lab/evaluation.js','lab/benchmark.js','lab/retrieval-benchmark.json','lab/comparison-worker.js','lab/comparison-catalog-manifest.json','lab/comparison-catalog.json.gz','franchises.json','assets/history-profile.js','assets/franchise-core.js','assets/app.js','assets/ir-core.js','lab/models.json','lab/models-legacy-3413.json','lab/catalog.json','lab/dataset.json','lab/corpus.sqlite3','lab/chart.umd.js']:assert (site/file).is_file(),file
build=json.loads((site/'build-manifest.json').read_text(encoding='utf-8'));catalog_path=site/build['catalog_file'];assert catalog_path.is_file(),catalog_path
catalog_bytes=catalog_path.read_bytes();catalog_bytes=gzip.decompress(catalog_bytes) if catalog_path.suffix=='.gz' else catalog_bytes
assert hashlib.sha256(catalog_bytes).hexdigest()==build['sha256'],'Public catalog hash mismatch'
catalog=json.loads(catalog_bytes.decode('utf-8'));assert len(catalog['records'])==build['count']==build['source_total_count']-build['adult_records_excluded']
assert len({r['anilist_id'] for r in catalog['records']})==len(catalog['records'])
assert not any(r.get('is_adult') for r in catalog['records'])
lab_catalog=json.loads((site/'lab/dataset.json').read_text(encoding='utf-8'));manifest=json.loads((site/'lab/models.json').read_text(encoding='utf-8'));legacy=json.loads((site/'lab/models-legacy-3413.json').read_text(encoding='utf-8'))
corpus_info=json.loads((site/'lab/comparison-catalog-manifest.json').read_text(encoding='utf-8'));corpus_blob=(site/corpus_info['file']).read_bytes();assert hashlib.sha256(corpus_blob).hexdigest()==corpus_info['compressed_sha256']
corpus_raw=gzip.decompress(corpus_blob);assert hashlib.sha256(corpus_raw).hexdigest()==corpus_info['sha256'];comparator=json.loads(corpus_raw.decode('utf-8'))
assert corpus_info['source_catalog_sha256']==build['sha256'] and len(comparator['records'])==build['count']
assert manifest['row_keys']==[r['key'] for r in comparator['records']],'Full-catalog model vectors do not match published catalog'
assert len(manifest['models'])==4 and all(model['rows']==build['count'] for model in manifest['models'])
assert legacy['row_keys']==[r['key'] for r in lab_catalog['rows']],'Historical model corpus does not match historical dataset'
for model in manifest['models']:assert hashlib.sha256((site/model['file']).read_bytes()).hexdigest()==model['sha256']
for model in legacy['models']:assert hashlib.sha256((site/model['file']).read_bytes()).hexdigest()==model['sha256']
for html in site.glob('*.html'):
    text=html.read_text(encoding='utf-8');assert 'href="/"' not in text,'Absolute root link breaks project Pages'
    for path in re.findall(r'(?:src|href)="([^"#]+)"',text):
        if path.startswith(('http:','https:','data:','mailto:')):continue
        assert (site/path).is_file(),f'{html.name}: missing {path}'
with sqlite3.connect(site/'lab/corpus.sqlite3') as db:
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert db.execute('SELECT COUNT(*) FROM works').fetchone()[0]==len(lab_catalog['rows'])
for p in root.rglob('*'):
    if not p.is_file() or any(part in {'.git','.venv','tmp','__pycache__'} for part in p.relative_to(root).parts):continue
    assert p.name not in {'profile.json','catalog-snapshot.json'},'Private state included'
    assert not re.search(rb'(?:gsk_[A-Za-z0-9]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)',p.read_bytes()),'Possible secret in '+str(p)
print('Distribution validated:',len(catalog['records']),'public works;',len(manifest['models']),'models')
