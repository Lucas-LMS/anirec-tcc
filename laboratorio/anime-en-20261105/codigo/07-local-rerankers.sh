#!/usr/bin/env bash
set -euo pipefail
code="$(cd "$(dirname "$0")" && pwd)"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
for model in llama qwen-nothink qwen deepseek; do
  "$HOME/tcc-lab/.venv-groq/bin/python" -u "$code/06-rerank.py" --model "$model"
done
