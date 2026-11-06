"""Teste oficial do model card MiniLM multilingue mais verificacoes proprias.

Nenhum treino ou experimento de animes. Executa em CPU e registra revisao/pesos.
"""
import hashlib
import importlib.metadata
import json
import os
import pathlib
import sys
import time

import numpy as np
import torch
from huggingface_hub import HfApi, snapshot_download
from sentence_transformers import SentenceTransformer


def main():
    root, run = map(pathlib.Path, sys.argv[1:])
    model_id = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    target = root/'models'/'paraphrase-multilingual-MiniLM-L12-v2'
    if target.exists():
        raise FileExistsError('Modelo local ja existe; preservar antes de repetir')
    torch.set_num_threads(4)
    requested_revision = os.environ.get('MODEL_REVISION', 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42')
    info = HfApi().model_info(model_id, revision=requested_revision)
    revision = info.sha
    (run/'origem.json').write_text(json.dumps({'model_id': model_id, 'revision': revision}, indent=2))
    snapshot = snapshot_download(
        model_id, revision=revision, cache_dir=str(root/'cache'),
        allow_patterns=['*.json', '*.txt', '*.model', '*.safetensors', 'README.md'],
    )
    model = SentenceTransformer(snapshot, device='cpu', local_files_only=True, trust_remote_code=False)
    # Textos e uso encode fornecidos no model card dos autores.
    sentences = ['This is an example sentence', 'Each sentence is converted']
    started = time.perf_counter()
    embeddings = model.encode(sentences)
    encode_seconds = time.perf_counter()-started
    assert embeddings.shape == (2, 384)
    assert np.isfinite(embeddings).all() and (np.linalg.norm(embeddings, axis=1) > 0).all()
    model.save_pretrained(str(target))
    reloaded = SentenceTransformer(str(target), device='cpu', local_files_only=True, trust_remote_code=False)
    reloaded_embeddings = reloaded.encode(sentences)
    np.testing.assert_allclose(embeddings, reloaded_embeddings, rtol=1e-5, atol=1e-6)
    # Exemplo didatico proprio, nao benchmark ou dado do catalogo anime.
    query = 'Uma crianca brinca com um cachorro.'
    documents = ['A crianca se diverte com um cao.', 'O mercado financeiro fechou em alta.', 'A previsao anuncia chuva amanha.']
    query_vector = reloaded.encode([query])
    document_vectors = reloaded.encode(documents)
    scores = reloaded.similarity(query_vector, document_vectors)[0].tolist()
    assert int(np.argmax(scores)) == 0
    np.save(run/'embeddings-exemplo-oficial.npy', embeddings)
    files = []
    for path in sorted(target.rglob('*')):
        if path.is_file():
            with path.open('rb') as source:
                sha = hashlib.file_digest(source, 'sha256').hexdigest()
            files.append({'path': str(path.relative_to(target)), 'bytes': path.stat().st_size, 'sha256': sha})
    result = {
        'model_id': model_id, 'revision': revision, 'device': str(model.device),
        'dimension': model.get_sentence_embedding_dimension(), 'max_seq_length': model.max_seq_length,
        'official_example_sentences': sentences, 'official_example_shape': list(embeddings.shape),
        'encode_seconds_two_sentences': encode_seconds, 'local_reload_allclose': True,
        'own_example_query': query, 'own_example_documents': documents, 'own_example_scores': scores,
        'own_example_top_index': int(np.argmax(scores)), 'model_path': str(target), 'files': files,
        'versions': {name: importlib.metadata.version(name) for name in ['torch', 'sentence-transformers', 'transformers', 'huggingface-hub', 'numpy']},
        'note': 'Verificacao funcional e exemplo sintetico; nenhuma qualidade no dominio anime foi medida.',
    }
    (run/'resultados.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'files'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
