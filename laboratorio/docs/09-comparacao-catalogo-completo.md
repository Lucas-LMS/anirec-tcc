# Comparação de embeddings no catálogo completo

## Escopo

O comparador ativo usa as 20.857 obras não adultas do snapshot AniList de 13/11/2026. As sinopses são o único texto usado para treinar os embeddings. Não são lidos perfis, listas privadas, recomendações comunitárias ou rótulos de avaliação.

Os quatro modelos foram treinados no mesmo corpus de sinopses. Cada sinopse vira um vetor pela média dos vetores das palavras, ponderada pelo IDF do catálogo e normalizada em L2. O conjunto é transdutivo: todas as sinopses públicas do snapshot participam do treinamento não supervisionado, sem uso de julgamentos de relevância.

| Modelo | Dimensão | Treino |
|---|---:|---|
| Word2Vec Skip-gram | 100 | Gensim, janela 5, `min_count=2`, negative sampling 5, 15 épocas, semente 20261118, 1 worker |
| Word2Vec CBOW | 100 | Mesmos parâmetros do Skip-gram, `sg=0` |
| fastText Skip-gram | 100 | Gensim, janela 5, `min_count=2`, negative sampling 5, subpalavras de 3 a 6 caracteres, 15 épocas |
| GloVe | 50 | Coocorrências simétricas em janela 5, ponderadas por distância inversa; `x_max=100`, `alpha=0.75`, taxa 0.05, 8 épocas |

As execuções anteriores de 3.413 obras e seus artefatos não foram reetiquetados. O manifesto histórico é `recomendador/online/lab/models-legacy-3413.json`; as quatro matrizes antigas continuam nos arquivos `*-bin` sem sufixo `-full`.

## Reproduzir

Instale as dependências fixadas em `requirements-full-models.txt` e execute:

```powershell
python -m pip install -r requirements-full-models.txt
python scripts/build_full_model_suite.py --glove-epochs 8
python scripts/build_site.py
python scripts/validate_distribution.py
```

O treinamento pode levar vários minutos em CPU. A saída gera quatro matrizes `*-full.bin` em `recomendador/online/lab/`, além do manifesto ativo `models.json`. Os hashes e coberturas de vocabulário são registrados no manifesto.

## Limites de interpretação

Este conjunto responde à comparação de quatro algoritmos treinados no mesmo domínio e snapshot. Seus resultados não são diretamente equivalentes aos resultados históricos de modelos externos de text8/fil9/GloVe. A métrica Sobreposição@10 continua medindo concordância com Skip-gram, não relevância humana. Para declarar que um método é melhor, é preciso avaliar os mesmos julgamentos de relevância para as 20.857 obras.
