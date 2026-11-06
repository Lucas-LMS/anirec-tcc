#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
for model in dummy tfidf glove fasttext w2v-cbow w2v-sg minilm w2v-lee-cbow w2v-lee-sg; do
  case "$model" in
    w2v-*) py="$HOME/tcc-lab/.venv-word2vec-py312/bin/python" ;;
    *) py="$HOME/tcc-lab/.venv-sentences/bin/python" ;;
  esac
  mkdir -p "$root/resultados/benchmark-v1/$model"
  echo "Iniciando $model"
  /usr/bin/time -v -o "$root/resultados/benchmark-v1/$model/recursos-runner.txt" \
    "$py" "$root/codigo/07-benchmark-classicos.py" --model "$model" \
    > "$root/resultados/benchmark-v1/$model/console.log" 2>&1
  echo "Concluído $model"
done
