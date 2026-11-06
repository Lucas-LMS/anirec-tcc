#!/usr/bin/env bash
# Copia evidencias concluidas do Linux para a documentacao Windows/OneDrive.
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
OUTPUT_ROOT=${OUTPUT_ROOT:-'/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio'}
mkdir -p "$OUTPUT_ROOT/logs/execucoes" "$OUTPUT_ROOT/manifests/linux"
dpkg-query -W > "$LAB_ROOT/manifests/pacotes-linux.txt"
g++-12 --version > "$LAB_ROOT/manifests/compilador-fasttext.txt"
cp -a "$LAB_ROOT/manifests/." "$OUTPUT_ROOT/manifests/linux/"
if [[ -d "$LAB_ROOT/Word2Vec/manifests" ]]; then
  mkdir -p "$OUTPUT_ROOT/manifests/word2vec"
  cp -a "$LAB_ROOT/Word2Vec/manifests/." "$OUTPUT_ROOT/manifests/word2vec/"
fi
if [[ -d "$LAB_ROOT/SentenceTransformers/manifests" ]]; then
  mkdir -p "$OUTPUT_ROOT/manifests/sentence-transformers"
  cp -a "$LAB_ROOT/SentenceTransformers/manifests/." "$OUTPUT_ROOT/manifests/sentence-transformers/"
fi
for run in "$LAB_ROOT"/runs/*; do
  if [[ -d $run && -f $run/exit-code.txt ]]; then
    cp -a "$run" "$OUTPUT_ROOT/logs/execucoes/"
  fi
done
source "$LAB_ROOT/.venv/bin/activate"
python - "$LAB_ROOT" "$OUTPUT_ROOT" <<'PY'
import datetime, hashlib, json, pathlib, subprocess, sys
lab, output = map(pathlib.Path, sys.argv[1:])
runs = []
for run in sorted((lab/'runs').iterdir()):
    status = run/'exit-code.txt'
    if status.exists():
        runs.append({'id': run.name, 'exit_code': int(status.read_text().strip()),
                     'path_linux': str(run), 'path_evidence': 'logs/execucoes/'+run.name})
models = []
for name, relative, prefix, rw in [
    ('GloVe-text8-50d', 'GloVe/vectors.txt', 'glove-', False),
    ('fastText-fil9-100d', 'fastText/result/fil9.bin', 'fasttext-embeddings-', True),
    ('fastText-cooking-supervised', 'tutorial-cooking/model_cooking.bin', 'fasttext-cooking-', False),
    ('Word2Vec-Lee-CBOW', 'Word2Vec/models/lee-cbow.model', 'word2vec-lee-', False),
    ('Word2Vec-Lee-Skipgram', 'Word2Vec/models/lee-skipgram.model', 'word2vec-lee-', False),
    ('MiniLM-multilingual-sentences-384d', 'SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2', 'sentences-minilm-', False),
]:
    file = lab/relative
    complete = any(run['id'].startswith(prefix) and run['exit_code'] == 0 for run in runs)
    rw_complete = any(run['id'].startswith('fasttext-rw-') and run['exit_code'] == 0 for run in runs)
    entry = {'name': name, 'path_linux': str(file), 'successful_run': complete,
             'rw_evaluation_pending': bool(rw and not rw_complete)}
    if rw and rw_complete:
        entry['rw_provenance'] = 'AWS mirror; word pairs and mean scores corroborated. See manifests/rw/auditoria.json.'
    if complete and file.is_file():
        with file.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        entry.update(bytes=file.stat().st_size, sha256=digest)
    if complete and file.is_dir():
        files = []
        for part in sorted(file.rglob('*')):
            if part.is_file():
                with part.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                files.append({'path': str(part.relative_to(file)), 'bytes': part.stat().st_size, 'sha256': digest})
        entry.update(files=files, bytes=sum(part['bytes'] for part in files))
    models.append(entry)
repos = []
for name in ['GloVe', 'fastText']:
    path = lab/name
    commit = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    changes = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=no'], text=True)
    repos.append({'name': name, 'commit': commit, 'tracked_changes': changes.splitlines()})
result = {'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'note': 'Estado Linux atual. artefatos.json preserva o inventario inicial Windows.',
          'runs': runs, 'models': models, 'repositories': repos}
(output/'manifests'/'estado-linux-atual.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('Evidencias de execucoes concluidas exportadas; modelos volumosos permanecem no Linux.')
PY
