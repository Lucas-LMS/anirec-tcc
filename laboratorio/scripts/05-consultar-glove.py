"""Exemplo proprio: carrega vetores textuais GloVe e consulta vizinhos por cosseno.

Nao e avaliador oficial nem experimento de relevancia de anime.
Requer apenas NumPy, instalado no ambiente de avaliacao do laboratorio.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vectors', required=True, type=Path)
    parser.add_argument('--word', required=True)
    parser.add_argument('--top-k', type=int, default=5)
    args = parser.parse_args()
    if args.top_k < 1:
        parser.error('--top-k deve ser positivo')
    words, rows = [], []
    with args.vectors.open(encoding='utf-8') as source:
        for line in source:
            fields = line.split()
            if not fields or fields[0] == '<unk>':
                continue
            words.append(fields[0])
            rows.append([float(value) for value in fields[1:]])
    if not rows:
        raise ValueError('Arquivo sem vetores')
    matrix = np.asarray(rows, dtype=np.float32)
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise ValueError('Vetores invalidos')
    index = {word: i for i, word in enumerate(words)}
    result = {'query': args.word, 'vocabulary_size': len(words), 'dimension': matrix.shape[1]}
    if args.word not in index:
        result.update(status='out_of_vocabulary', neighbors=[])
    else:
        norms = np.linalg.norm(matrix, axis=1)
        valid = norms > 0
        target = index[args.word]
        if not valid[target]:
            raise ValueError('Vetor de consulta nulo')
        matrix[valid] /= norms[valid, None]
        scores = matrix @ matrix[target]
        scores[~valid] = -np.inf
        scores[target] = -np.inf
        best = np.argsort(-scores)[:min(args.top_k, len(words) - 1)]
        result.update(status='ok', neighbors=[
            {'word': words[int(i)], 'cosine': float(scores[i])}
            for i in best if np.isfinite(scores[i])
        ])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
