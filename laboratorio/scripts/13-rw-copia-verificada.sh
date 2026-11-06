#!/usr/bin/env bash
set -euo pipefail
scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
output=$(cd -- "$scripts/.." && pwd)
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
source "$LAB_ROOT/.venv/bin/activate"
mkdir -p "$output/manifests/rw"
python "$scripts/12-auditar-rw.py" \
  /mnt/c/tcc-lab/fastText/data/rw-aws-regional.zip \
  /mnt/c/tcc-lab/fastText/data/rw-academic.txt \
  "$output/manifests/rw/amazon-notebook.ipynb" \
  "$output/manifests/rw/auditoria.json" \
  "$LAB_ROOT/fastText/data/rw"
cp /mnt/c/tcc-lab/fastText/data/rw-aws-regional.zip "$LAB_ROOT/fastText/data/rw-aws.zip"
# O avaliador oficial e o modelo permanecem os mesmos; nenhuma nova otimizacao.
bash "$scripts/07-avaliar-rw.sh"
