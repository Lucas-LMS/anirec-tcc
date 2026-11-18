"""Train a comparable four-model suite and encode the complete public AniList catalog.

All word embeddings are trained unsupervised on the same frozen set of public,
non-adult AniList synopses. This is a new, domain-trained experiment; it does not
silently extend or relabel the historical 3,413-row pretrained-model artifacts.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
from gensim.models import FastText, Word2Vec
from numba import njit
from comparison_catalog import build_comparison_catalog

ROOT = Path(__file__).resolve().parents[1]
ONLINE = ROOT / 'recomendador' / 'online'
LAB = ONLINE / 'lab'
SEED = 20261118
WINDOW = 5
MIN_COUNT = 2
EPOCHS = 15


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tokenize(text: str) -> list[str]:
    return re.findall(r'[^\W\d_]+', unicodedata.normalize('NFKC', text or '').lower(), flags=re.UNICODE)


def unit(vector: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    return vector / length if length else np.zeros_like(vector)


def write_model(name: str, label: str, source: str, settings: dict, records: list[dict],
                documents: list[list[str]], vectors: dict[str, np.ndarray], dimensions: int,
                idf: dict, output_file: str) -> dict:
    started = time.perf_counter()
    matrix = np.zeros((len(records), dimensions), dtype='<f4')
    known_tokens = total_tokens = 0
    for i, doc in enumerate(documents):
        found = [(vectors[word], idf['idf'].get(word, idf['unseen'])) for word in doc if word in vectors]
        total_tokens += len(doc)
        known_tokens += len(found)
        if not found:
            continue
        weights = np.fromiter((item[1] for item in found), dtype=np.float32, count=len(found))
        values = np.stack([item[0] for item in found]).astype(np.float32, copy=False)
        matrix[i] = unit(np.average(values, axis=0, weights=weights).astype(np.float32))
    blob = matrix.tobytes(order='C')
    (LAB / output_file).write_bytes(blob)
    coverage = known_tokens / total_tokens if total_tokens else 0.0
    return {
        'id': name, 'label': label, 'file': f'lab/{output_file}', 'dimensions': dimensions,
        'rows': len(records), 'sha256': digest(blob), 'artifact_sha256': digest(blob),
        'source': source, 'settings': settings, 'mean_token_coverage': coverage,
        'zero_documents': int(np.count_nonzero(~np.any(matrix, axis=1))),
        'export_seconds': time.perf_counter() - started,
    }


@njit(cache=True)
def collect_unordered_pairs(flat: np.ndarray, offsets: np.ndarray, window: int, vocab_size: int):
    count = 0
    for d in range(len(offsets) - 1):
        length = offsets[d + 1] - offsets[d]
        for i in range(length):
            count += min(window, length - i - 1)
    packed = np.empty(count, dtype=np.int64)
    weights = np.empty(count, dtype=np.float32)
    k = 0
    for d in range(len(offsets) - 1):
        start, end = offsets[d], offsets[d + 1]
        for i in range(start, end):
            for distance in range(1, min(window, end - i - 1) + 1):
                a, b = flat[i], flat[i + distance]
                low, high = (a, b) if a < b else (b, a)
                packed[k] = low * vocab_size + high
                weights[k] = 1.0 / distance
                k += 1
    return packed, weights


@njit(cache=True)
def train_glove(rows, cols, counts, vocab_size, dimensions, epochs, seed, learning_rate, x_max, alpha):
    np.random.seed(seed)
    words = (np.random.random((vocab_size, dimensions)).astype(np.float32) - .5) / dimensions
    contexts = (np.random.random((vocab_size, dimensions)).astype(np.float32) - .5) / dimensions
    word_bias = np.zeros(vocab_size, dtype=np.float32)
    context_bias = np.zeros(vocab_size, dtype=np.float32)
    order = np.arange(len(rows))
    old_word = np.empty(dimensions, dtype=np.float32)
    old_context = np.empty(dimensions, dtype=np.float32)
    for epoch in range(epochs):
        np.random.shuffle(order)
        total_loss = 0.0
        for n in range(len(order)):
            p = order[n]
            i, j, x = rows[p], cols[p], counts[p]
            weight = (x / x_max) ** alpha if x < x_max else 1.0
            target = np.log(x)
            for direction in range(2):
                wi, ci = (i, j) if direction == 0 else (j, i)
                dot = 0.0
                for d in range(dimensions):
                    dot += words[wi, d] * contexts[ci, d]
                    old_word[d] = words[wi, d]
                    old_context[d] = contexts[ci, d]
                error = dot + word_bias[wi] + context_bias[ci] - target
                gradient = weight * error
                total_loss += weight * error * error
                for d in range(dimensions):
                    words[wi, d] -= learning_rate * gradient * old_context[d]
                    contexts[ci, d] -= learning_rate * gradient * old_word[d]
                word_bias[wi] -= learning_rate * gradient
                context_bias[ci] -= learning_rate * gradient
        print('GloVe epoch', epoch + 1, '/', epochs, 'loss', total_loss / (2 * len(rows)))
    return words + contexts


def train_glove_vectors(documents: list[list[str]], dimensions: int, epochs: int) -> tuple[dict, dict]:
    counts = collections.Counter(word for doc in documents for word in doc)
    words = sorted(word for word, count in counts.items() if count >= MIN_COUNT)
    index = {word: i for i, word in enumerate(words)}
    flat_parts = [np.fromiter((index[w] for w in doc if w in index), dtype=np.int32) for doc in documents]
    offsets = np.zeros(len(flat_parts) + 1, dtype=np.int64)
    for i, part in enumerate(flat_parts):
        offsets[i + 1] = offsets[i] + len(part)
    flat = np.concatenate(flat_parts)
    del flat_parts
    print(f'GloVe: {len(words):,} termos; {len(flat):,} tokens; calculando coocorrências…', flush=True)
    packed, weights = collect_unordered_pairs(flat, offsets, WINDOW, len(words))
    order = np.argsort(packed, kind='mergesort')
    packed, weights = packed[order], weights[order]
    starts = np.empty(len(packed), dtype=np.bool_)
    starts[0] = True
    starts[1:] = packed[1:] != packed[:-1]
    positions = np.flatnonzero(starts)
    unique = packed[positions]
    sums = np.add.reduceat(weights, positions)
    rows = (unique // len(words)).astype(np.int32)
    cols = (unique % len(words)).astype(np.int32)
    del packed, weights, order, starts, positions, unique
    print(f'GloVe: {len(rows):,} pares distintos; treinando {epochs} épocas…', flush=True)
    vectors = train_glove(rows, cols, sums.astype(np.float32), len(words), dimensions,
                          epochs, SEED, .05, 100.0, .75)
    del rows, cols, sums, flat, offsets
    return {word: vectors[i] for i, word in enumerate(words)}, {
        'algorithm': 'GloVe weighted least squares', 'dimensions': dimensions, 'window': WINDOW,
        'min_count': MIN_COUNT, 'epochs': epochs, 'x_max': 100.0, 'alpha': .75,
        'learning_rate': .05, 'seed': SEED, 'workers': 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glove-epochs', type=int, default=8)
    args = parser.parse_args()
    if args.glove_epochs < 1:
        parser.error('--glove-epochs deve ser positivo')
    LAB.mkdir(parents=True, exist_ok=True)
    build = json.loads((ONLINE / 'build-manifest.json').read_text(encoding='utf-8'))
    compressed = (ONLINE / build['catalog_file']).read_bytes()
    catalog_bytes = gzip.decompress(compressed) if build['catalog_file'].endswith('.gz') else compressed
    if digest(catalog_bytes) != build['sha256']:
        raise ValueError('Hash do catálogo não confere com o build-manifest.')
    catalog = json.loads(catalog_bytes)
    records = catalog['records']
    comparison_catalog = build_comparison_catalog(ONLINE)
    print(f"Catálogo de comparação: {comparison_catalog['compressed_bytes'] / 1048576:.1f} MiB", flush=True)
    idf = json.loads((ONLINE / 'idf.json').read_text(encoding='utf-8'))
    documents = [tokenize(row.get('text', '')) for row in records]
    if len(records) != build['count'] or not records:
        raise ValueError('O catálogo completo está vazio ou inconsistente.')
    print(f"Corpus: {len(records):,} obras, {sum(map(len, documents)):,} tokens; hash {build['sha256']}", flush=True)

    # Preserve the prior 3,413-row model suite and its exact checksums.
    old_manifest_path = LAB / 'models.json'
    old_manifest = json.loads(old_manifest_path.read_text(encoding='utf-8')) if old_manifest_path.exists() else None
    if old_manifest and len(old_manifest.get('row_keys', [])) == 3413:
        (LAB / 'models-legacy-3413.json').write_text(json.dumps(old_manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    model_specs = []
    for name, label, sg in [('skipgram', 'Word2Vec Skip-gram · AniList', 1), ('cbow', 'Word2Vec CBOW · AniList', 0)]:
        started = time.perf_counter()
        print('Treinando', label, flush=True)
        model = Word2Vec(sentences=documents, vector_size=100, window=WINDOW, min_count=MIN_COUNT,
                         workers=1, sg=sg, negative=5, sample=.001, epochs=EPOCHS, seed=SEED)
        vectors = {word: model.wv[word] for word in model.wv.index_to_key}
        settings = {'algorithm': 'Gensim Word2Vec', 'sg': sg, 'vector_size': 100, 'window': WINDOW,
                    'min_count': MIN_COUNT, 'negative': 5, 'sample': .001, 'epochs': EPOCHS,
                    'seed': SEED, 'workers': 1, 'training_corpus_sha256': build['sha256']}
        spec = write_model(name, label, 'https://radimrehurek.com/gensim/models/word2vec.html', settings,
                           records, documents, vectors, 100, idf, f'{name}-full.bin')
        spec['training_seconds'] = time.perf_counter() - started
        model_specs.append(spec)
        del model, vectors
        print(json.dumps(spec, ensure_ascii=False), flush=True)

    started = time.perf_counter()
    print('Treinando fastText Skip-gram · AniList', flush=True)
    fast = FastText(sentences=documents, vector_size=100, window=WINDOW, min_count=MIN_COUNT,
                    workers=1, sg=1, negative=5, sample=.001, epochs=EPOCHS, seed=SEED,
                    min_n=3, max_n=6, bucket=100_000)
    fast_vectors = {}
    for word in sorted({word for doc in documents for word in doc}):
        try:
            value = fast.wv.get_vector(word)
            if np.any(value):
                fast_vectors[word] = value
        except KeyError:
            pass
    fast_settings = {'algorithm': 'Gensim FastText Skip-gram', 'sg': 1, 'vector_size': 100,
                     'window': WINDOW, 'min_count': MIN_COUNT, 'negative': 5, 'sample': .001,
                     'epochs': EPOCHS, 'seed': SEED, 'workers': 1, 'min_n': 3, 'max_n': 6,
                     'bucket': 100_000, 'training_corpus_sha256': build['sha256']}
    spec = write_model('fasttext', 'fastText Skip-gram · AniList · subpalavras',
                       'https://radimrehurek.com/gensim/models/fasttext.html', fast_settings,
                       records, documents, fast_vectors, 100, idf, 'fasttext-full.bin')
    spec['training_seconds'] = time.perf_counter() - started
    model_specs.append(spec)
    del fast, fast_vectors
    print(json.dumps(spec, ensure_ascii=False), flush=True)

    started = time.perf_counter()
    glove_lookup, glove_settings = train_glove_vectors(documents, 50, args.glove_epochs)
    spec = write_model('glove', 'GloVe · AniList', 'https://nlp.stanford.edu/projects/glove/',
                       {**glove_settings, 'training_corpus_sha256': build['sha256']}, records,
                       documents, glove_lookup, 50, idf, 'glove-full.bin')
    spec['training_seconds'] = time.perf_counter() - started
    model_specs.append(spec)
    del glove_lookup
    print(json.dumps(spec, ensure_ascii=False), flush=True)

    manifest = {
        'built_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'corpus_sha256': build['sha256'],
        'row_keys': [row['key'] for row in records], 'models': model_specs,
        'policy': 'Full 20,857-row public non-adult AniList snapshot. All four embeddings trained unsupervised on the same snapshot synopses, then pooled with the same catalog IDF and L2 normalization. These domain-trained artifacts replace the 3,413-row historical pretrained-model comparison only in this active comparator.',
        'historical_manifest': 'models-legacy-3413.json', 'training_seed': SEED,
        'training_corpus': 'Complete public non-adult synopsis text from the frozen AniList snapshot; no private profiles or recommendation edges.',
        'comparison_catalog_manifest': 'comparison-catalog-manifest.json',
    }
    old_path = LAB / 'models-legacy-3413.json'
    if old_manifest is None and not old_path.exists():
        raise RuntimeError('Historical 3,413-row manifest was not preserved.')
    (LAB / 'models.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'models': len(model_specs), 'rows': len(records), 'corpus_sha256': build['sha256']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
