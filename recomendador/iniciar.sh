#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
root="$(cd "$(dirname "$0")" && pwd)"
exec "$HOME/tcc-lab/.venv-word2vec-py312/bin/python" -u "$root/server.py" --port 8765
