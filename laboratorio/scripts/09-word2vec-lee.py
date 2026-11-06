"""Wrapper proprio do treinamento do tutorial oficial Gensim no corpus Lee.

CBOW usa os defaults da biblioteca; Skip-gram altera apenas sg=1.
Registra testes e avaliacao sem confundir este corpus pequeno com o catalogo anime.
"""
import hashlib
import json
import logging
import pathlib
import shutil
import sys
import time

import gensim
import numpy as np
from gensim import utils
from gensim.models import Word2Vec
from gensim.models.word2vec import FAST_VERSION
from gensim.test.utils import datapath


def sha256(path):
    with pathlib.Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


class MyCorpus:
    def __iter__(self):
        # Mesmo corpus e pre-processamento da secao Training Your Own Model.
        with open(datapath('lee_background.cor'), encoding='utf-8') as source:
            for line in source:
                yield utils.simple_preprocess(line)


def main():
    run = pathlib.Path(sys.argv[1])
    root = pathlib.Path(sys.argv[2])
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    data, models = root/'data', root/'models'
    data.mkdir(parents=True, exist_ok=True)
    models.mkdir(parents=True, exist_ok=True)
    corpus_path = pathlib.Path(datapath('lee_background.cor'))
    questions_path = pathlib.Path(datapath('questions-words.txt'))
    for path in [corpus_path, questions_path]:
        shutil.copy2(path, data/path.name)
    with questions_path.open(encoding='utf-8') as source:
        total_questions = sum(bool(line.strip()) and not line.startswith(':') for line in source)
    result = {
        'gensim_version': gensim.__version__, 'numpy_version': np.__version__,
        'python_version': sys.version, 'fast_version': FAST_VERSION,
        'source_tutorial': 'https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html',
        'corpus': {'name': corpus_path.name, 'bytes': corpus_path.stat().st_size,
                   'sha256': sha256(corpus_path), 'documents': sum(1 for _ in MyCorpus())},
        'questions': {'name': questions_path.name, 'sha256': sha256(questions_path), 'total': total_questions},
        'models': [],
    }
    for name, options in [('cbow', {}), ('skipgram', {'sg': 1})]:
        target = models/f'lee-{name}.model'
        if target.exists():
            raise FileExistsError(f'Preserve o modelo existente antes de repetir: {target}')
        started = time.perf_counter()
        model = Word2Vec(sentences=MyCorpus(), **options)
        elapsed = time.perf_counter()-started
        query = 'king' if 'king' in model.wv else model.wv.index_to_key[0]
        vector = model.wv[query].copy()
        assert vector.shape == (model.vector_size,) and np.isfinite(vector).all()
        unknown = 'zzztccnonexistenttoken20261029'
        try:
            model.wv[unknown]
        except KeyError:
            oov_checked = True
        else:
            raise AssertionError('Consulta OOV inesperadamente presente')
        model.save(str(target))
        reloaded = Word2Vec.load(str(target))
        np.testing.assert_array_equal(vector, reloaded.wv[query])
        reloaded.wv.save_word2vec_format(str(models/f'lee-{name}.vec'), binary=False)
        score, sections = reloaded.wv.evaluate_word_analogies(str(questions_path))
        total = sections[-1]
        correct, incorrect = len(total['correct']), len(total['incorrect'])
        covered = correct+incorrect
        (run/f'analogies-{name}.json').write_text(json.dumps(sections, indent=2), encoding='utf-8')
        entry = {
            'name': name, 'training_seconds': elapsed, 'vector_size': reloaded.vector_size,
            'vocabulary_size': len(reloaded.wv), 'corpus_count': reloaded.corpus_count,
            'parameters': {key: getattr(reloaded, key) for key in [
                'sg', 'window', 'min_count', 'workers', 'epochs', 'seed', 'negative', 'hs', 'sample', 'alpha', 'min_alpha']},
            'query': query, 'neighbors': reloaded.wv.most_similar(query, topn=5),
            'save_reload_identical_vector': True, 'oov_raises_keyerror': oov_checked,
            'analogy_correct': correct, 'analogy_covered': covered,
            'analogy_total': total_questions, 'coverage': covered/total_questions,
            'accuracy_on_covered': float(score) if covered else None,
            'model_path': str(target), 'model_sha256': sha256(target),
        }
        result['models'].append(entry)
        print(json.dumps(entry, indent=2), flush=True)
    (run/'resultados.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('CBOW e Skip-gram concluidos. Corpus didatico; nao e comparacao cientifica com os demais modelos.')


if __name__ == '__main__':
    main()
