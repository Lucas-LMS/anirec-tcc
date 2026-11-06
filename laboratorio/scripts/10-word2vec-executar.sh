#!/usr/bin/env bash
# Runner proprio: treinamento/uso da API oficial Gensim; ambiente separado.
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$LAB_ROOT/.venv-word2vec-py312/bin/activate"
mkdir -p "$LAB_ROOT/Word2Vec/manifests" "$LAB_ROOT/runs"
run=$(mktemp -d "$LAB_ROOT/runs/word2vec-lee-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
exec > >(tee "$run/console.log") 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > "$run/exit-code.txt"; date -u +%FT%TZ > "$run/fim-utc.txt"' EXIT
date -u +%FT%TZ > "$run/inicio-utc.txt"
python -m pip freeze --all > "$LAB_ROOT/Word2Vec/manifests/requirements-resolved.txt"
python -m pip inspect > "$LAB_ROOT/Word2Vec/manifests/pip-inspect.json"
sha256sum "$scripts/09-word2vec-lee.py" > "$run/script-sha256.txt"
/usr/bin/time -v -o "$run/recursos.txt" python "$scripts/09-word2vec-lee.py" "$run" "$LAB_ROOT/Word2Vec"
echo "Evidencias: $run"
