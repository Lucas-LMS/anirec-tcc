#!/usr/bin/env bash
# Etapas separadas porque o servidor oficial RW esta inacessivel nesta rede.
# Parametros de embeddings copiados do word-vector-example.sh oficial v0.9.2.
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
repo="$LAB_ROOT/fastText"
[[ $(uname -s) == Linux ]] || exit 2
[[ $(git -C "$repo" rev-parse HEAD) == 5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe ]] || exit 2
git -C "$repo" diff --exit-code HEAD --
mode=${1:-}
[[ $mode == embeddings || $mode == cooking ]] || { echo 'Uso: bash 04-fasttext-etapas.sh embeddings|cooking'; exit 2; }
mkdir -p "$LAB_ROOT/runs"
run=$(mktemp -d "$LAB_ROOT/runs/fasttext-$mode-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
exec > >(tee "$run/console.log") 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > "$run/exit-code.txt"; date -u +%FT%TZ > "$run/fim-utc.txt"' EXIT
date -u +%FT%TZ > "$run/inicio-utc.txt"
source "$LAB_ROOT/.venv/bin/activate"
cd "$repo"
compiler=${FASTTEXT_CXX:-g++-12}
command -v "$compiler" >/dev/null || { echo "Compilador ausente: $compiler. Consulte o guia."; exit 2; }
"$compiler" --version > "$run/compilador.txt"
printf 'make CXX=%s\n' "$compiler" > "$run/compilacao.txt"
make "CXX=$compiler"
sha256sum fasttext > "$run/executavel-sha256.txt"
if [[ $mode == embeddings ]]; then
  [[ ! -e result/fil9.bin ]] || { echo 'Modelo existente; preserve a execucao anterior.'; exit 2; }
  [[ -s data/fil9 ]] || { echo 'Corpus fil9 ausente.'; exit 2; }
  mkdir -p result
  sha256sum data/fil9 > "$run/entradas-sha256.txt"
  printf '%s\n' './fasttext skipgram -input data/fil9 -output result/fil9 -lr 0.025 -dim 100 -ws 5 -epoch 1 -minCount 5 -neg 5 -loss ns -bucket 2000000 -minn 3 -maxn 6 -thread 4 -t 1e-4 -lrUpdateRate 100' > "$run/comando.txt"
  /usr/bin/time -v -o "$run/recursos.txt" ./fasttext skipgram -input data/fil9 -output result/fil9 -lr 0.025 -dim 100 -ws 5 -epoch 1 -minCount 5 -neg 5 -loss ns -bucket 2000000 -minn 3 -maxn 6 -thread 4 -t 1e-4 -lrUpdateRate 100
  printf 'king\nqueen\nunseenwordexample\n' > "$run/consultas.txt"
  ./fasttext print-word-vectors result/fil9.bin < "$run/consultas.txt" > "$run/vetores-consulta.txt"
  printf 'an adventure about friendship\n' | ./fasttext print-sentence-vectors result/fil9.bin > "$run/vetor-sentenca.txt"
  python - "$run" <<'PY'
import pathlib, sys, numpy as np
p = pathlib.Path(sys.argv[1])
rows = [line.split() for line in (p/'vetores-consulta.txt').read_text().splitlines()]
assert len(rows) == 3
vectors = np.array([[float(x) for x in row[1:]] for row in rows])
assert vectors.shape == (3, 100) and np.isfinite(vectors).all()
assert (np.linalg.norm(vectors, axis=1) > 0).all()
sentence = np.loadtxt(p/'vetor-sentenca.txt')
assert sentence.shape == (100,) and np.isfinite(sentence).all()
print('Teste funcional proprio: tres vetores 100d finitos e nao nulos; vetor de sentenca 100d finito.')
print('Isso nao e avaliacao semantica RW.')
PY
  sha256sum result/fil9.bin result/fil9.vec > "$run/saidas-sha256.txt"
  echo 'Treinamento oficial por etapas concluido. Avaliacao RW PENDENTE por indisponibilidade da origem.'
else
  cd "$LAB_ROOT/tutorial-cooking"
  [[ ! -e model_cooking.bin ]] || { echo 'Classificador existente; preserve antes de repetir.'; exit 2; }
  tar -xzf cooking.stackexchange.tar.gz
  [[ $(wc -l < cooking.stackexchange.txt) == 15404 ]] || exit 3
  head -n 12404 cooking.stackexchange.txt > cooking.train
  tail -n 3000 cooking.stackexchange.txt > cooking.valid
  sha256sum cooking.stackexchange.tar.gz cooking.train cooking.valid > "$run/entradas-sha256.txt"
  printf '%s\n' 'Tutorial oficial supervised-tutorial.html, primeiro classificador sem ajustes' > "$run/comando.txt"
  /usr/bin/time -v -o "$run/recursos.txt" "$repo/fasttext" supervised -input cooking.train -output model_cooking
  "$repo/fasttext" test model_cooking.bin cooking.valid | tee "$run/metricas-k1.txt"
  "$repo/fasttext" test model_cooking.bin cooking.valid 5 | tee "$run/metricas-k5.txt"
  printf 'Which baking dish is best to bake a banana bread ?\nWhy not put knives in the dishwasher?\n' | "$repo/fasttext" predict model_cooking.bin - > "$run/predicoes.txt"
  sha256sum model_cooking.bin > "$run/saidas-sha256.txt"
fi
echo "Evidencias: $run"
