#!/usr/bin/env bash
# Wrapper do laboratorio. Mantem os scripts e parametros oficiais preservados.
set -euo pipefail
[[ $(uname -s) == Linux ]] || { echo 'Requer Linux/Ubuntu.' >&2; exit 2; }
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
case ${1:-} in
  glove) name=glove; repo="$LAB_ROOT/GloVe"; script=demo.sh
    revision=52f7dbc512be3f72e9c11e7cbb19dfdfa4651e9c; model=vectors.txt ;;
  fasttext) name=fasttext; repo="$LAB_ROOT/fastText"; script=word-vector-example.sh
    revision=5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe; model=result/fil9.bin ;;
  *) echo 'Uso: bash 02-executar-oficial.sh glove|fasttext' >&2; exit 2 ;;
esac
[[ -f "$LAB_ROOT/.venv/bin/activate" ]] || { echo 'Execute primeiro 01-preparar-linux.sh.' >&2; exit 2; }
[[ ! -e "$repo/$model" ]] || { echo 'Modelo ja existe. Preserve e versione a execucao anterior antes de repetir.' >&2; exit 2; }
[[ $(git -C "$repo" rev-parse HEAD) == "$revision" ]] || { echo 'Revisao divergente.' >&2; exit 2; }
git -C "$repo" diff --exit-code HEAD --
mkdir -p "$LAB_ROOT/runs"
run=$(mktemp -d "$LAB_ROOT/runs/$name-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
exec > >(tee "$run/console.log") 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > "$run/exit-code.txt"; date -u +%FT%TZ > "$run/fim-utc.txt"' EXIT
date -u +%FT%TZ > "$run/inicio-utc.txt"
source "$LAB_ROOT/.venv/bin/activate"
python -c 'import numpy, scipy; print("Dependencias de avaliacao importadas")'
cd "$repo"
if [[ $name == fasttext ]]; then
  compiler=${FASTTEXT_CXX:-g++-12}
  command -v "$compiler" >/dev/null || { echo "Compilador ausente: $compiler"; exit 2; }
  "$compiler" --version > "$run/compilador.txt"
  # GNU Make transmite esta atribuicao aos make invocados pelo script oficial.
  export MAKEFLAGS="${MAKEFLAGS:-} CXX=$compiler"
fi
download_zip() {
  local url=$1 target=$2
  if [[ ! -f "$target" ]]; then
    wget --timeout=40 --tries=2 -O "$target.part" "$url"
    unzip -t "$target.part"
    mv "$target.part" "$target"
  fi
  unzip -t "$target"
  sha256sum "$target" >> "$run/entradas-sha256.txt"
}
mkdir -p data
if [[ $name == glove ]]; then
  download_zip https://mattmahoney.net/dc/text8.zip data/text8.zip
  if [[ ! -f text8 ]]; then unzip data/text8.zip -d .; fi
  sha256sum text8 >> "$run/entradas-sha256.txt"
else
  download_zip https://mattmahoney.net/dc/enwik9.zip data/enwik9.zip
  if [[ ! -f data/enwik9 ]]; then unzip data/enwik9.zip -d data; fi
  download_zip https://nlp.stanford.edu/~lmthang/morphoNLM/rw.zip data/rw.zip
  if [[ ! -f data/rw/rw.txt ]]; then unzip data/rw.zip -d data; fi
  sha256sum data/enwik9 data/rw/rw.txt >> "$run/entradas-sha256.txt"
fi
printf 'cwd=%s\nrevision=%s\ncommand=bash -e -o pipefail %s\n' "$repo" "$revision" "$script" > "$run/comando.txt"
git status --short > "$run/git-status-inicial.txt"
sha256sum "$script" > "$run/script-sha256.txt"
if [[ -x /usr/bin/time ]]; then
  /usr/bin/time -v -o "$run/recursos.txt" bash -e -o pipefail "$script"
else
  bash -e -o pipefail "$script"
fi
[[ -s "$model" ]] || { echo 'Modelo esperado ausente ou vazio.' >&2; exit 3; }
if [[ $name == fasttext ]]; then
  [[ -s result/fil9.vec && -s result/vectors.txt ]] || exit 3
  sha256sum result/fil9.bin result/fil9.vec result/vectors.txt > "$run/saidas-sha256.txt"
else
  [[ -s vocab.txt ]] || exit 3
  sha256sum vectors.txt vocab.txt > "$run/saidas-sha256.txt"
fi
echo "Execucao encerrada com sucesso; conferir metricas e cobertura no log: $run"
