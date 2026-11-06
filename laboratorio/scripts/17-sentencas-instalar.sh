#!/usr/bin/env bash
# Reproducao das versoes de topo observadas na instalacao inicial.
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
python312="$HOME/.local/tcc-python-3.12.16/bin/python3.12"
"$python312" -m venv "$LAB_ROOT/.venv-sentences"
source "$LAB_ROOT/.venv-sentences/bin/activate"
mkdir -p "$LAB_ROOT/SentenceTransformers/manifests"
python -m pip install 'torch==2.15.0+cpu' --index-url https://download.pytorch.org/whl/cpu --report "$LAB_ROOT/SentenceTransformers/manifests/pip-torch.json"
python -m pip install 'sentence-transformers==6.2.0' 'transformers==5.21.1' --report "$LAB_ROOT/SentenceTransformers/manifests/pip-sentences.json"
python -m pip freeze --all > "$LAB_ROOT/SentenceTransformers/manifests/requirements-resolved.txt"
python -m pip inspect > "$LAB_ROOT/SentenceTransformers/manifests/pip-inspect.json"
