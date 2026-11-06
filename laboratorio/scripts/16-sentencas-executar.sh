#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$LAB_ROOT/.venv-sentences/bin/activate"
mkdir -p "$LAB_ROOT/SentenceTransformers/manifests" "$LAB_ROOT/runs"
run=$(mktemp -d "$LAB_ROOT/runs/sentences-minilm-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
exec > >(tee "$run/console.log") 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > "$run/exit-code.txt"; date -u +%FT%TZ > "$run/fim-utc.txt"' EXIT
date -u +%FT%TZ > "$run/inicio-utc.txt"
python -m pip freeze --all > "$LAB_ROOT/SentenceTransformers/manifests/requirements-resolved.txt"
python -m pip inspect > "$LAB_ROOT/SentenceTransformers/manifests/pip-inspect.json"
sha256sum "$scripts/15-sentencas-minilm.py" > "$run/script-sha256.txt"
/usr/bin/time -v -o "$run/recursos.txt" python "$scripts/15-sentencas-minilm.py" "$LAB_ROOT/SentenceTransformers" "$run"
echo "Evidencias: $run"
