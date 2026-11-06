#!/usr/bin/env bash
# Autoria do laboratorio: infraestrutura propria; nao pertence aos autores dos modelos.
set -euo pipefail
[[ $(uname -s) == Linux ]] || { echo 'Requer Linux/Ubuntu (por exemplo, WSL).' >&2; exit 2; }
for tool in gcc g++ make python3 wget unzip perl git; do
  command -v "$tool" >/dev/null || { echo "Dependencia ausente: $tool. Consulte o guia." >&2; exit 2; }
done
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
SEED_ROOT=${SEED_ROOT:-/mnt/c/tcc-lab}
mkdir -p "$LAB_ROOT/manifests" "$LAB_ROOT/runs"
exec > >(tee -a "$LAB_ROOT/manifests/preparacao-linux.log") 2>&1
date -u +%FT%TZ
prepare_repo() {
  local name=$1 url=$2 revision=$3
  if [[ ! -e "$LAB_ROOT/$name" ]]; then
    if [[ -d "$SEED_ROOT/$name/.git" ]]; then
      cp -a "$SEED_ROOT/$name" "$LAB_ROOT/$name"
    else
      git -c core.autocrlf=false clone "$url" "$LAB_ROOT/$name"
      git -C "$LAB_ROOT/$name" checkout --detach "$revision"
    fi
  fi
  [[ $(git -C "$LAB_ROOT/$name" rev-parse HEAD) == "$revision" ]] || {
    echo "Revisao diferente em $name; nao sera alterada automaticamente." >&2; exit 2;
  }
  git -C "$LAB_ROOT/$name" diff --exit-code HEAD --
}
prepare_repo GloVe https://github.com/stanfordnlp/GloVe.git 52f7dbc512be3f72e9c11e7cbb19dfdfa4651e9c
prepare_repo fastText https://github.com/facebookresearch/fastText.git 5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe
python3 -m venv "$LAB_ROOT/.venv"
source "$LAB_ROOT/.venv/bin/activate"
python -m pip install numpy scipy
python -m pip freeze --all > "$LAB_ROOT/manifests/requirements-resolved.txt"
python -m pip inspect > "$LAB_ROOT/manifests/pip-inspect.json"
dpkg-query -W > "$LAB_ROOT/manifests/pacotes-linux.txt"
{
  uname -a
  cat /etc/os-release
  gcc --version
  g++ --version
  make --version
  python --version
  python -c 'import numpy, scipy; print("numpy", numpy.__version__); print("scipy", scipy.__version__)'
  git -C "$LAB_ROOT/GloVe" rev-parse HEAD
  git -C "$LAB_ROOT/fastText" rev-parse HEAD
} > "$LAB_ROOT/manifests/versoes.txt"
echo 'Preparacao concluida. Treinamento e avaliacao ainda nao foram executados.'
