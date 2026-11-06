#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lab="$HOME/tcc-lab"
for model in tfidf glove fasttext w2v-cbow w2v-sg minilm w2v-lee-cbow w2v-lee-sg; do
  case "$model" in
    w2v-*) python="$lab/.venv-word2vec-py312/bin/python" ;;
    tfidf|minilm) python="$lab/.venv-sentences/bin/python" ;;
    *) python="$lab/.venv/bin/python" ;;
  esac
  target="$root/resultados/v1/$model"
  mkdir -p "$target"
  if [[ -f "$target/resultado.json" ]]; then
    echo "Resultado ja existe; preservando $model"
    continue
  fi
  echo "Executando $model"
  /usr/bin/time -v -o "$target/recursos.txt" "$python" "$root/codigo/03-codificar-modelo.py" --model "$model" --output "$target" > "$target/console.log" 2>&1
  echo '0' > "$target/exit-code.txt"
  echo "Concluido $model"
done
