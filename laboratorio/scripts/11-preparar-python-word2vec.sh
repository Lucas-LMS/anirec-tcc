#!/usr/bin/env bash
# CPython oficial instalado no diretorio do usuario; nao altera o Python Ubuntu.
set -euo pipefail
LAB_ROOT=${LAB_ROOT:-"$HOME/tcc-lab"}
prefix="$HOME/.local/tcc-python-3.12.16"
downloads="$LAB_ROOT/Word2Vec/downloads"
mkdir -p "$downloads" "$LAB_ROOT/Word2Vec/manifests"
cd "$downloads"
if [[ ! -f Python-3.12.16.tar.xz ]]; then
  wget --timeout=40 --tries=2 https://www.python.org/ftp/python/3.12.16/Python-3.12.16.tar.xz
fi
printf '%s\n' 'b5796915dc45ff745cfb4e990a7e7c93d6f546328a102ce31448d69ebc37575c  Python-3.12.16.tar.xz' | sha256sum -c -
if [[ ! -x "$prefix/bin/python3.12" ]]; then
  tar -xf Python-3.12.16.tar.xz
  cd Python-3.12.16
  ./configure --prefix="$prefix"
  make -j4
  make altinstall
fi
"$prefix/bin/python3.12" -c 'import ssl, sqlite3, bz2, lzma, ctypes; import sys; print(sys.version)'
"$prefix/bin/python3.12" -m venv "$LAB_ROOT/.venv-word2vec-py312"
source "$LAB_ROOT/.venv-word2vec-py312/bin/activate"
python -m pip install gensim==4.4.0 --report "$LAB_ROOT/Word2Vec/manifests/pip-install-report.json"
python -m pip freeze --all > "$LAB_ROOT/Word2Vec/manifests/requirements-resolved.txt"
python -m pip inspect > "$LAB_ROOT/Word2Vec/manifests/pip-inspect.json"
python -m pip download --no-deps --no-binary=gensim gensim==4.4.0 -d "$downloads"
sha256sum "$downloads"/*.tar.* > "$LAB_ROOT/Word2Vec/manifests/downloads-sha256.txt"
python -c 'import gensim; from gensim.models.word2vec import FAST_VERSION; print("gensim", gensim.__version__, "FAST_VERSION", FAST_VERSION)'
