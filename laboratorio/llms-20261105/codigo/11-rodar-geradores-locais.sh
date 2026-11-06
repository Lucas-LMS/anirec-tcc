#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
for model in llama deepseek qwen; do
  mkdir -p "$root/resultados/benchmark-v1/$model"
  echo "Iniciando $model"
  /usr/bin/time -v -o "$root/resultados/benchmark-v1/$model/recursos-runner.txt" \
    "$HOME/tcc-lab/.venv-sentences/bin/python" -u "$root/codigo/09-benchmark-geradores.py" --model "$model"
  echo "Concluído $model"
done
