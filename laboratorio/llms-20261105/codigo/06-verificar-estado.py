"""Confere estado seguro de retomada e registra hashes dos arquivos da etapa."""
import ast
import hashlib
import json
import pathlib
import zipfile

root=pathlib.Path(__file__).resolve().parents[1]
installation=json.loads((root/'resultados/instalacao.json').read_text(encoding='utf-8'))
freeze=json.loads((root/'dados/freeze.json').read_text(encoding='utf-8'))
for name,expected in freeze['files_sha256'].items():
    assert hashlib.sha256((root/'dados'/name).read_bytes()).hexdigest()==expected,name
for key in ['smoke-llama','smoke-deepseek-thinking','smoke-qwen-official-sampling-thinking']:
    result=json.loads((root/'resultados'/f'{key}.json').read_text(encoding='utf-8'))
    assert result['success'] and len(result['requests'])==2
    assert all(row['expected_number_present'] for row in result['requests'])
for model in installation['models']:
    path=pathlib.Path(model['path']);assert path.exists() and path.stat().st_size==model['bytes']
for script in (root/'codigo').glob('*.py'):ast.parse(script.read_text(encoding='utf-8'),filename=str(script))
with zipfile.ZipFile(root/'dados/brutos/sms-spam-collection-kaggle.zip') as z:assert z.testzip() is None
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(root.rglob('*')) if p.is_file() and p.name!='manifesto-etapa.json'}
(root/'resultados/manifesto-etapa.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'OK: 3 LLMs com geração verificada; congelamento intacto; Python válido; ZIP íntegro; {len(manifest)} arquivos identificados.')
