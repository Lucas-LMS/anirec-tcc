"""Confere congelamento, integridade estrutural e links; registra hashes da entrega."""
import hashlib
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1]
freeze = json.loads((root/'dados/freeze.json').read_text(encoding='utf-8'))
for name, expected in freeze['files_sha256'].items():
    assert hashlib.sha256((root/'dados'/name).read_bytes()).hexdigest() == expected, name
result = json.loads((root/'resultados/resumo.json').read_text(encoding='utf-8'))
queries = json.loads((root/'dados/consultas.json').read_text(encoding='utf-8'))
catalog = json.loads((root/'dados/catalogo.json').read_text(encoding='utf-8'))
rankings = json.loads((root/'resultados/rankings.json').read_text(encoding='utf-8'))
assert len(queries) == 58 and len(catalog) == 39
assert result['winner_primary_pilot'] == 'minilm'
assert sum(row[0]['grade'] == 2 for row in rankings['minilm']['PT_EN']) == 47
for model, scenarios in rankings.items():
    for scenario, rows in scenarios.items():
        assert len(rows) == 58
        assert all(len(row) == 39 and len({x['id'] for x in row}) == 39 for row in rows)
page = (root/'relatorios/painel-comparacao.html').read_text(encoding='utf-8')
for link in re.findall(r'href="([^"]+)"', page):
    if not link.startswith('http'):
        assert (root/'relatorios'/link).exists(), link
files = [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in str(p)
         and p.name != 'manifesto-entrega.json']
manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
pdf = root.parents[1]/'output/pdf/relatorio-comparacao-anirec.pdf'
manifest['../../output/pdf/relatorio-comparacao-anirec.pdf'] = hashlib.sha256(pdf.read_bytes()).hexdigest()
(root/'resultados/manifesto-entrega.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'OK: freeze intacto; 47/58; rankings completos; links locais; {len(manifest)} hashes registrados.')
