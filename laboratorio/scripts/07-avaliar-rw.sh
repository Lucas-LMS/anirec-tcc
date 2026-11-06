#!/usr/bin/env bash
# Avaliacao oficial fastText, separada para permitir retomar sem retreinar.
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
repo="$LAB_ROOT/fastText"
[[ -s "$repo/result/fil9.bin" ]] || { echo 'Treine primeiro o modelo fil9.'; exit 2; }
[[ $(git -C "$repo" rev-parse HEAD) == 5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe ]] || exit 2
git -C "$repo" diff --exit-code HEAD --
mkdir -p "$LAB_ROOT/runs"
run=$(mktemp -d "$LAB_ROOT/runs/fasttext-rw-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
exec > >(tee "$run/console.log") 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > "$run/exit-code.txt"; date -u +%FT%TZ > "$run/fim-utc.txt"' EXIT
date -u +%FT%TZ > "$run/inicio-utc.txt"
source "$LAB_ROOT/.venv/bin/activate"
cd "$repo"
if [[ ! -f data/rw/rw.txt ]]; then
  if [[ ! -f data/rw.zip ]]; then
    wget --timeout=20 --tries=2 -O data/rw.zip.part https://nlp.stanford.edu/~lmthang/morphoNLM/rw.zip
    unzip -t data/rw.zip.part
    mv data/rw.zip.part data/rw.zip
  fi
  unzip -t data/rw.zip
  unzip -n data/rw.zip -d data
fi
sha256sum result/fil9.bin data/rw/rw.txt > "$run/entradas-sha256.txt"
cut -f 1,2 data/rw/rw.txt | awk '{print tolower($0)}' | tr '\t' '\n' > "$run/queries.txt"
./fasttext print-word-vectors result/fil9.bin < "$run/queries.txt" > "$run/vectors.txt"
python eval.py -m "$run/vectors.txt" -d data/rw/rw.txt
sha256sum "$run/vectors.txt" > "$run/saidas-sha256.txt"
echo "Avaliacao RW concluida: $run"
