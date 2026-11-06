"""Codificacao e ranking congelados; nao carrega julgamentos de relevancia."""
import argparse
import collections
import hashlib
import json
import math
import pathlib
import re
import subprocess
import time
import unicodedata

import numpy as np

SCENARIOS = {'PT_EN': ('pt','en'), 'EN_EN': ('en','en'), 'PT_PT': ('pt','pt')}


def tokens(text):
    return re.findall(r'[^\W\d_]+', unicodedata.normalize('NFKC', text).casefold(), flags=re.UNICODE)


def normalized(matrix):
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return np.divide(matrix, norms, out=np.zeros_like(matrix), where=norms > 0)


def sha_file(path):
    with pathlib.Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    result_path = args.output/'resultado.json'
    if result_path.exists():
        raise FileExistsError('Resultado existente; usar nova execucao')
    catalog = json.loads((root/'dados/catalogo.json').read_text())
    queries = json.loads((root/'dados/consultas.json').read_text())
    frozen = json.loads((root/'dados/freeze.json').read_text())
    for filename, digest in frozen['files_sha256'].items():
        assert sha_file(root/'dados'/filename) == digest
    all_texts = list(dict.fromkeys(
        [item[f'description_{lang}'] for lang in ['en','pt'] for item in catalog]
        + [item[f'text_{lang}'] for lang in ['en','pt'] for item in queries]))
    wanted = set(token for text in all_texts for token in tokens(text))
    lab = pathlib.Path.home()/'tcc-lab'
    result = {'model': args.model, 'scenarios': {}, 'catalog_ids': [x['id'] for x in catalog],
              'query_ids': [x['id'] for x in queries], 'unique_texts': len(all_texts),
              'tokenizer': 'NFKC + casefold + letras Unicode; sem stemming ou stopwords',
              'data_sha256': frozen['files_sha256']}
    payload = {}
    clock = time.perf_counter()
    start = time.perf_counter()
    lookup, known, process = {}, set(), None
    dimension = None
    cached_text = None
    source_path = None
    if args.model == 'tfidf':
        from sklearn.feature_extraction.text import TfidfVectorizer
    elif args.model == 'minilm':
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(4)
        source_path = lab/'SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2'
        encoder = SentenceTransformer(str(source_path), device='cpu', local_files_only=True, trust_remote_code=False)
        dimension = encoder.get_sentence_embedding_dimension()
        lengths = [len(row) for row in encoder.tokenizer(all_texts, truncation=False)['input_ids']]
        assert max(lengths) <= encoder.max_seq_length, 'Truncamento detectado; interromper, nao ajustar depois dos rankings'
        result['token_lengths'] = {'max': max(lengths), 'min': min(lengths),
                                   'model_limit': encoder.max_seq_length, 'truncated': 0}
    elif args.model == 'glove':
        source_path = lab/'GloVe/vectors.txt'
        dimension = 50
        with source_path.open() as source:
            for line in source:
                word, _, numbers = line.partition(' ')
                if word in wanted:
                    lookup[word] = np.fromstring(numbers, sep=' ', dtype=np.float32)
        known = set(lookup)
    elif args.model == 'fasttext':
        source_path = lab/'fastText/result/fil9.bin'
        dimension = 100
        with (lab/'fastText/result/fil9.vec').open() as source:
            next(source)
            for line in source:
                word = line.partition(' ')[0]
                if word in wanted:
                    known.add(word)
        err = (args.output/'fasttext-stderr.txt').open('w')
        process = subprocess.Popen([str(lab/'fastText/fasttext'), 'print-word-vectors', str(source_path)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True, bufsize=1)
        def ask(word):
            process.stdin.write(word+'\n'); process.stdin.flush()
            fields = process.stdout.readline().split()
            if len(fields) != dimension+1 or fields[0] != word:
                raise RuntimeError(f'Resposta fastText invalida para {word}: {fields[:3]}')
            return np.asarray(fields[1:], dtype=np.float32)
        lookup['the'] = ask('the')  # primeiro retorno confirma carregamento do modelo
    elif args.model.startswith('w2v-'):
        from gensim.models import Word2Vec
        names = {
            'w2v-cbow': 'text8-cbow-100d.model', 'w2v-sg': 'text8-skipgram-100d.model',
            'w2v-lee-cbow': 'lee-cbow.model', 'w2v-lee-sg': 'lee-skipgram.model'}
        source_path = lab/'Word2Vec/models'/names[args.model]
        encoder = Word2Vec.load(str(source_path))
        dimension = encoder.vector_size
        known = {word for word in wanted if word in encoder.wv}
        lookup = {word: encoder.wv[word].copy() for word in known}
    else:
        raise ValueError(args.model)
    result['load_seconds'] = time.perf_counter()-start
    start = time.perf_counter()
    if args.model == 'minilm':
        vectors = encoder.encode(all_texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
        cached_text = dict(zip(all_texts, vectors))
    if args.model == 'fasttext':
        for word in sorted(wanted):
            if word not in lookup:
                lookup[word] = ask(word)
    result['lexical_or_text_cache_seconds'] = time.perf_counter()-start
    for scenario, (qlang, dlang) in SCENARIOS.items():
        docs = [row[f'description_{dlang}'] for row in catalog]
        questions = [row[f'text_{qlang}'] for row in queries]
        start = time.perf_counter()
        if args.model == 'tfidf':
            vectorizer = TfidfVectorizer(tokenizer=tokens, token_pattern=None, lowercase=False,
                                         ngram_range=(1,2), sublinear_tf=True, norm='l2')
            docs_matrix = vectorizer.fit_transform(docs)
            question_matrix = vectorizer.transform(questions)
            dmatrix, qmatrix = docs_matrix.toarray(), question_matrix.toarray()
            vocab = vectorizer.vocabulary_
            usable = lambda word: word in vocab
            lex_known = usable
        elif args.model == 'minilm':
            dmatrix = np.stack([cached_text[text] for text in docs])
            qmatrix = np.stack([cached_text[text] for text in questions])
            usable = lex_known = None
        else:
            counts = collections.Counter(word for text in docs for word in set(tokens(text)))
            idf = {word: math.log((1+len(docs))/(1+count))+1 for word,count in counts.items()}
            unseen_idf = math.log(1+len(docs))+1
            def encode(text):
                values, weights = [], []
                for word in tokens(text):
                    value = lookup.get(word)
                    if value is not None and np.linalg.norm(value) > 0:
                        values.append(value); weights.append(idf.get(word, unseen_idf))
                if not values:
                    return np.zeros(dimension, dtype=np.float32)
                return np.average(np.stack(values), axis=0, weights=weights)
            dmatrix = normalized([encode(text) for text in docs])
            qmatrix = normalized([encode(text) for text in questions])
            usable = lambda word: word in lookup and np.linalg.norm(lookup[word]) > 0
            lex_known = lambda word: word in known
        encoding_seconds = time.perf_counter()-start
        start = time.perf_counter()
        scores = np.clip(qmatrix @ dmatrix.T, -1, 1)
        ranking_seconds = time.perf_counter()-start
        assert scores.shape == (58,39) and np.isfinite(scores).all()
        payload[scenario] = scores
        payload[scenario+'_documents'] = dmatrix
        payload[scenario+'_queries'] = qmatrix
        all_query_tokens = [word for text in questions for word in tokens(text)]
        result['scenarios'][scenario] = {
            'query_language': qlang, 'catalog_language': dlang, 'dimension': dmatrix.shape[1],
            'encoding_cached_seconds': encoding_seconds, 'score_matrix_seconds': ranking_seconds,
            'zero_query_vectors': int((np.linalg.norm(qmatrix, axis=1) == 0).sum()),
            'zero_document_vectors': int((np.linalg.norm(dmatrix, axis=1) == 0).sum()),
            'usable_query_token_fraction': sum(usable(word) for word in all_query_tokens)/len(all_query_tokens) if usable else None,
            'in_vocabulary_query_token_fraction': sum(lex_known(word) for word in all_query_tokens)/len(all_query_tokens) if lex_known else None,
        }
    if process:
        process.stdin.close()
        process.stdout.close()
        assert process.wait(timeout=20) == 0
        err.close()
    result['worker_seconds_before_hash'] = time.perf_counter()-clock
    result['source_path'] = str(source_path) if source_path else 'TF-IDF fitted on catalog only'
    if source_path and source_path.is_file():
        result['model_sha256'] = sha_file(source_path)
    result['timing_note'] = 'Lote completo com cache; nao latencia online por consulta. load inclui imports e leitura; cache inclui termos das consultas.'
    np.savez_compressed(args.output/'matrizes.npz', **payload)
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
