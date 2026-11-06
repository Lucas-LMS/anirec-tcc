#!/usr/bin/env bash
set -euo pipefail
code="$(cd "$(dirname "$0")" && pwd)"
base="$(dirname "$code")"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
for model in random tfidf bm25 glove fasttext w2v-cbow w2v-sg minilm w2v-lee-cbow w2v-lee-sg; do
  py="$HOME/tcc-lab/.venv-sentences/bin/python"
  if [[ "$model" == w2v-* ]]; then py="$HOME/tcc-lab/.venv-word2vec-py312/bin/python"; fi
  mkdir -p "$base/results/retrieval/$model"
  /usr/bin/time -v -o "$base/results/retrieval/$model/resources.txt" "$py" -u "$code/03-encode.py" --model "$model"
done
