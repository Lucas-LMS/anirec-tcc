"""Package local evidence only. Never include credentials or large model weights."""
import datetime,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'output'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
sms=load(ROOT/'laboratorio/llms-20261105/resultados/comparacao/comparacao.json')
anime=load(ROOT/'laboratorio/anime-en-20261105/results/evaluation/comparison.json')
qa=load(ROOT/'laboratorio/anime-en-20261105/results/evaluation/qa.json')
layout=load(OUT/'comparacao-anime-en/qa-layout.json')
assert sms['complete'] and anime['complete'] and qa['complete'] and not layout['text_bounds_errors']
readme=OUT/'LEIA-ME-COMPARATIVOS.md'
readme.write_text('''# Entrega dos comparativos de 05/11/2026

SMS: 13 pipelines, mesmas 200 mensagens; relatório final em comparacao-sms/relatorio-comparacao-sms.pdf (46 páginas) e HTML. Anime: catálogo de 1.000 sinopses, 24 consultas em inglês; relatório em comparacao-anime-en/relatorio-anime-en.pdf (30 páginas) e HTML. Os HTMLs usam imagens da mesma pasta; manter esses arquivos juntos.

Recuperação no catálogo inteiro e reranking de cinco candidatos têm tabelas separadas. Referência de anime é proxy de gêneros, não avaliação humana de preferência. O melhor estático pontual no catálogo completo foi Word2Vec Skip-gram, candidato inicial de engenharia, não vencedor universal. MiniLM e LLMs são comparadores e não entrarão no produto final confirmado.

Os fontes e índices estão nos diretórios laboratorio correspondentes. O guia METRICAS_EXPLICADAS.md explica fórmulas, utilidade e limites. A demonstração em recomendador/demo_ir_estatico.py usa índices estáticos congelados e pesos aritméticos de favoritos fictícios; não é a interface final nem um benchmark de perfil real. Resultados ilustrativos estão em demo-ir-estatico.

Incluímos dados pequenos, requisições/respostas públicas do benchmark, logs, versões, protocolos, hashes e snapshots históricos. Não incluímos chaves, perfil pessoal, pesos grandes de modelos, corpora de treinamento ou ambientes Python. Os pesos permanecem nos caminhos documentados na máquina; este ZIP não é backup completo do WSL. O manual histórico de 29/10 continua em output/manual e não foi substituído.

Qwen SMS: um timeout após 185 respostas exigiu retomada dos 15 IDs restantes. Respostas anteriores preservadas; tempo total original ausente, latências concluídas e sensibilidade à falha documentadas. Versões preliminares foram preservadas. Um trecho que dizia RW pendente foi corrigido: Rare Words já tinha sido concluído em 29/10; ver ERRATA_DOCUMENTAL.md e documentação original. Não misturar Spearman RW, F1 SMS e nDCG anime.

Reexecutar avaliação/relatórios não faz inferência nem chamadas de API. Não sobrescrever evidências para repetir testes; criar outra rodada. O manifesto lista bytes/SHA-256 de cada arquivo selecionado, excluindo a si próprio. Extrair em pasta separada para inspecionar sem substituir o workspace atual.
''',encoding='utf-8')
directories=['laboratorio/llms-20261105','laboratorio/anime-en-20261105','output/comparacao-sms','output/comparacao-anime-en','output/demo-ir-estatico','laboratorio/manifests/rw']
individual=['laboratorio/README.md','laboratorio/docs/07-rare-words-resolucao.md','laboratorio/logs/execucoes/fasttext-rw-20261029T135536Z-BwFCmr/resultado-exato.json','recomendador/demo_ir_estatico.py','recomendador/EXEMPLO_RI_SEM_TREINAMENTO.md','output/LEIA-ME-COMPARATIVOS.md']
files=set()
manifest=OUT/'comparacao-anime-en/manifesto-entrega.json'
for directory in directories:
    for path in (ROOT/directory).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and path!=manifest:files.add(path)
files.update(ROOT/path for path in individual)
key_path=Path('C:/tcc-lab/secrets/groq-api-key.txt')
key=key_path.read_text(encoding='utf-8-sig').strip().encode() if key_path.exists() else None
items=[]
for path in sorted(files):
    assert path.resolve().is_relative_to(ROOT.resolve()) and path.stat().st_size<100_000_000
    blob=path.read_bytes()
    assert not key or key not in blob,'Credential occurrence: packaging blocked without exposing value.'
    items.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
manifest.write_text(json.dumps(dict(generated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sms_complete=True,anime_complete=True,independent_ranking_checks=qa['ranking_rows_checked'],layout_bounds_errors=0,credential_scan='No key occurrence in selected files',model_weights_included=False,personal_profile_included=False,files=items),ensure_ascii=False,indent=2),encoding='utf-8')
archive=OUT/'evidencias-comparativos-20261105.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(files|{manifest}):z.write(path,path.relative_to(ROOT).as_posix())
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
(OUT/'evidencias-comparativos-20261105.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps(dict(files=len(files)+1,zip_bytes=archive.stat().st_size,sha256=digest,credential_occurrences=0),indent=2))
