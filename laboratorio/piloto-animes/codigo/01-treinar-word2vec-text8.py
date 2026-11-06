"""Treino adicional anterior aos rankings: nao ajusta com os dados anime."""
import hashlib
import json
import logging
import pathlib
import time

import gensim
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
from gensim.models.word2vec import Text8Corpus


class Progress(CallbackAny2Vec):
    def __init__(self, name):
        self.name, self.epoch = name, 0
    def on_epoch_end(self, model):
        self.epoch += 1
        print(f'{self.name}: epoca {self.epoch}/{model.epochs}', flush=True)


def main():
    root = pathlib.Path.home()/'tcc-lab'
    corpus = root/'GloVe/text8'
    with corpus.open('rb') as source:
        sha = hashlib.file_digest(source, 'sha256').hexdigest()
    assert sha == '6e890197040d37d85beb962ae1f041ff1d9a9ca8d20c7d99c85027eebf51dca7'
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    report = {'corpus': str(corpus), 'corpus_sha256': sha, 'gensim': gensim.__version__, 'models': []}
    for name, sg in [('cbow', 0), ('skipgram', 1)]:
        target = root/f'Word2Vec/models/text8-{name}-100d.model'
        if target.exists():
            raise FileExistsError(f'Modelo ja existe: {target}')
        started = time.perf_counter()
        model = Word2Vec(sentences=Text8Corpus(str(corpus)), vector_size=100, window=5,
                         min_count=5, workers=4, epochs=5, sg=sg, seed=20261029,
                         negative=5, sample=0.001, callbacks=[Progress(name)])
        seconds = time.perf_counter()-started
        model.save(str(target))
        with target.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        report['models'].append({'name': name, 'path': str(target), 'sha256': digest,
                                 'vocabulary': len(model.wv), 'seconds': seconds,
                                 'dimension': model.vector_size, 'epochs': model.epochs, 'sg': sg})
    (root/'Word2Vec/manifests/text8-piloto.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
