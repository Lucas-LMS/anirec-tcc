# Comunidade, BM25 e avaliação humana — versão de 06/11/2026

Este documento registra uma nova experiência de Recuperação da Informação. Não há treinamento, ajuste automático de pesos ou chamadas a LLMs. A representação principal continua sendo Word2Vec Skip-gram, 100 dimensões, com média dos vetores das palavras ponderada por IDF. As sinopses completas em inglês continuam sendo usadas. BM25 é uma alternativa lexical adicional, não outro modelo de linguagem.

## 1. Dataset ampliado e rastreável

O snapshot público passou de **2.495 para 3.053 obras**, aumento de **558 (22,4%)**. Dessas adições, 148 já estavam no cache operacional e 410 foram obtidas na ampliação delimitada desta etapa. Há 3.050 sinopses não vazias e 12.212 vetores documentais no banco público: quatro representações por obra. Os três documentos sem texto utilizável têm vetores zero.

A coleta foi associada a oito situações concretas de teste: Lycoris Recoil, Steins;Gate, Violet Evergarden, Laid-Back Camp, Haikyu!!, Monster, Spirited Away e Mushishi. Para cada referência, consultamos até 20 recomendações relacionadas e uma página de até 50 descobertas por gênero, excluindo IDs já conhecidos. Depois atualizamos os metadados das obras do conjunto em lotes de até 50 IDs. O script é `refresh_research_catalog.py`; requer `--execute` explícito e não varre o catálogo inteiro. O protocolo, IDs e contagens estão em [research-expansion.json](../data/research-expansion.json).

A etapa de rede levou aproximadamente **222 segundos**, entre 19:22 e 19:26 de 06/11/2026, horário de São Paulo. Isso não inclui reconstrução dos quatro vetores documentais, banco, testes e publicação. O cliente espaça requisições em 2,2 segundos e trata respostas 429. Não é um processo contínuo de coleta.

O pedido de autorização para um catálogo integral continua sem resposta nesta data. Esta ampliação por cenários de uso não equivale a uma autorização para espelhar todo o AniList. O dataset tem viés de uso, gênero e popularidade; não é amostra aleatória. Novas versões podem crescer com cenários documentados e permissão compatível. O SQLite não impõe um teto de 3.053 obras; para catálogos muito maiores, o custo de transferência e cálculo no navegador exigirá índice/consulta paginados.

O banco operacional privado tem 3.065 registros, incluindo 12 registros adultos previamente existentes que não são distribuídos no catálogo público. Não confundir esse total com o público. O ETL privado gerou a versão `anilist-etl-v1-55f1b347ecb2`; preserva texto original, texto tratado, proveniência e relações. As notas pessoais ficam fora do repositório.

### Campos comunitários agora presentes

| Campo AniList | Campo público | Significado e uso |
|---|---|---|
| `averageScore` | `average_score` | Nota média ponderada informada pelo AniList, escala 0–100. Fonte prioritária do bônus opcional. |
| `meanScore` | `mean_score` | Média informada pelo serviço, escala 0–100. Alternativa quando a ponderada está ausente. |
| `popularity` | `popularity` | Quantidade de usuários com a obra na lista. Informativa; não é contagem de avaliações. |
| `favourites` | `community_favourites` | Quantidade de favoritos. Informativa; não é porcentagem de aprovação. |
| `stats.scoreDistribution` | `rating_count` | Soma das quantidades da distribuição de notas retornada. Não substituir por popularidade. |
| instante de coleta | `statistics_fetched_at` | Data da observação dessas estatísticas, que mudam com o tempo. |

Há notas ponderadas e médias em **3.052/3.053** obras; popularidade e favoritos em todas. Ausência permanece `null`, não zero. O banco público `lab/corpus.sqlite3` possui esses campos em `works`, além das tabelas relacionais de gêneros, tags e vetores. O ETL mantém uma tabela `dataset_community` separada. O Atlas permite ordenar e inspecionar esses valores, sinopses e consultas SQL reais.

Exemplo de consulta no banco público:

```sql
SELECT title, average_score, mean_score, popularity,
       community_favourites, rating_count, statistics_fetched_at
FROM works
WHERE average_score IS NOT NULL
ORDER BY average_score DESC, title
LIMIT 20;
```

Isso encontra obras bem avaliadas, mas não prova semelhança com uma referência.

## 2. Como a comunidade participa sem dominar

O modo inicial continua **Vetores + temas, bônus comunitário desligado**. É a referência experimental preservada. O usuário pode escolher bônus máximo de 5% ou 10% na interface.

Definimos `q = average_score / 100`; se ausente, usamos `mean_score / 100`. Nunca somamos as duas, pois medem avaliações relacionadas. Não conhecemos nem reproduzimos a fórmula interna de ponderação do AniList. Popularidade e favoritos não entram na ordenação nesta etapa.

Para um índice de relevância `s` entre 0 e 1:

```python
def acrescentar_comunidade(s, nota_ponderada, nota_media, gamma=0.05):
    nota = nota_ponderada if nota_ponderada is not None else nota_media
    if nota is None:
        return s
    q = nota / 100.0
    bonus = gamma * q * (1.0 - s)
    return s + bonus

print(acrescentar_comunidade(0.70, 81, 81))  # 0.71215
```

Com `s=0,70`, nota 81 e `gamma=0,05`, a contribuição é **0,01215**, não 81 pontos nem 5 pontos fixos. O acréscimo máximo é limitado por gamma e não empurra o índice além de 1. Uma obra desconhecida ou pouco popular não recebe penalidade adicional por isso. Ainda assim há possível viés contra obras sem nota; por esse motivo o bônus é opcional e precisa de avaliação humana.

O bônus é aplicado separadamente ao índice Geral e ao personalizado. Suas notas continuam formando o perfil individual: todas as notas disponíveis são consideradas, e o ponto neutro fica entre mínimo e máximo observados. A combinação pessoal padrão continua 65% referência e 35% perfil. O bônus comunitário não substitui sua opinião nem transforma nota global em afinidade pessoal. A interface mostra a contribuição de cada parcela.

## 3. BM25 junto dos vetores

A média de vetores aproxima relações entre palavras, mas pode diluir termos específicos. BM25 recompensa termos compartilhados, dá maior importância a palavras menos frequentes no corpus, satura repetições e considera comprimento do documento. Não entende enredo, ironia ou negação. Usamos a sinopse inteira da referência como consulta, não só o título.

Parâmetros fixos: **k1=1,2; b=0,75**. A tokenização e lista explícita de palavras funcionais estão em `retrieval_experiments.py` e `shared/ir-core.js`. A consulta utiliza termos únicos que aparecem em mais de um documento; isso evita que termos exclusivos da própria referência consumam a normalização sem recuperar outras obras. O índice lexical exclui documentos adultos.

Para cada termo `t`, documento `d`, número de documentos `N` e frequência documental `df`:

```text
IDF(t) = ln(1 + (N - df(t) + 0,5) / (df(t) + 0,5))
BM25(d,q) = soma IDF(t) × tf(t,d) × (k1+1)
                         / [tf(t,d) + k1 × (1-b + b × |d|/comprimento_médio)]
```

Para combinar escalas, dividimos o valor bruto pelo limite superior `(k1+1) × soma IDF(t)` dos termos da consulta. Não usamos o melhor resultado como divisor: ele não vira artificialmente 1. O valor normalizado é um índice, não uma probabilidade. A explicação de cada recomendação mostra valor bruto e termos encontrados.

| Estratégia selecionável | Composição da referência |
|---|---|
| Vetores + temas | 50% sinopse vetorial + 50% temas |
| Híbrido | 40% sinopse vetorial + 40% temas + 20% BM25 normalizado |
| Somente BM25 | 100% BM25; diagnóstico lexical |

O cosseno textual é convertido por `(cos+1)/2`. Temas mantêm 85% cosseno de tags ponderadas e 15% Jaccard dos gêneros. O personalizado combina a referência escolhida com as mesmas parcelas do perfil anterior. BM25 não treina nem altera os embeddings. As duas implementações Python/JavaScript são verificadas numericamente.

Exemplo usando o código real:

```python
from retrieval_experiments import bm25

documentos = [
    {"key": "a", "text": "Girls protect a city as secret agents."},
    {"key": "b", "text": "Secret agents investigate a conspiracy."},
    {"key": "c", "text": "Friends cook and camp in the mountains."},
]
valores = bm25(documentos, "Girls work as secret agents.")
for chave, resultado in valores.items():
    print(chave, resultado["raw"], resultado["score"], resultado["matched_terms"])
```

Cada documento é um dicionário com ID estável e texto completo. O retorno separa score bruto, normalizado e termos encontrados. No aplicativo usamos as sinopses tratadas do snapshot real.

## 4. Comparação automática: mudança não significa melhora

O script `scripts/benchmark_retrieval.js` executou oito referências no mesmo snapshot público congelado, com quatro sistemas e três repetições aquecidas por consulta. Foi usado o Word2Vec Skip-gram em todos; este experimento isola a estratégia de recuperação e o bônus, não compara novamente os quatro embeddings. Resultados completos: `output/comparacao-ri-v10/` e página **Experimentos de RI**.

| Sistema | Média das medianas por consulta | Sobreposição média do top 10 com a referência vetorial |
|---|---:|---:|
| Vetores + temas | 218,83 ms | 100% |
| Somente BM25 | 239,00 ms | 18,75% |
| Híbrido | 241,16 ms | 92,5% |
| Híbrido + comunidade 5% | 225,47 ms | 92,5% |

Tempos medem processamento nessa execução Node, não latência de rede nem desempenho garantido em outro dispositivo. A variação não demonstra que acrescentar comunidade acelera o sistema. A tabela não mede precisão: os resultados ainda não receberam julgamentos humanos. Em Lycoris Recoil, BM25 puro compartilhou 0/10 títulos com o ranking vetorial; o híbrido 9/10 e híbrido com comunidade 8/10. São hipóteses para avaliação, não uma prova de superioridade.

O IDF e os vetores documentais foram reconstruídos para o corpus ampliado. Portanto, mudanças frente a versões antigas também podem vir do dataset; não atribuí-las integralmente ao BM25. Comparações desta etapa usam o mesmo corpus para os quatro sistemas.

## 5. Avaliação humana: duas perguntas independentes

Na busca, clique **Avaliar esta busca · julgamento humano**. O programa congela referência, candidatos, filtros, parâmetros, identificação do corpus e quatro rankings. A página de avaliação reúne os top 10 dos sistemas numa união sem duplicatas. Exibe candidatos em ordem independente do ranking e oculta qual sistema os recuperou. Não é possível avaliar antes de preparar uma busca nesse navegador/endereço.

O avaliador informa um identificador anônimo e clica **Usar este identificador**. Para cada candidato responde separadamente:

1. **Parece com a referência?** 0 sem relação; 1 fraca; 2 boa; 3 muito forte.
2. **Combina com minhas preferências?** 0 não combina; 1 pouco; 2 bem; 3 muito.

Não sei avaliar permanece sem julgamento. Não usamos nota zero no lugar de resposta ausente. Sinopses completas e temas ficam disponíveis para apoiar a decisão; convém conhecer a obra ou explicitar a limitação de julgar apenas metadados. A avaliação não treina modelo ou ajusta pesos.

Quando há perfil ativo, a avaliação de preferências considera **somente obras ainda não iniciadas, sem nota fornecida e sem favorito manual no perfil**. Isso reduz vazamento: não avaliamos previsão de gosto de uma obra cuja nota já construiu o perfil. Todos os itens pontuados continuam usados para construir o perfil; são excluídos apenas desse conjunto de teste. A avaliação de semelhança pode incluir obras já vistas. Cada dimensão tem seu próprio conjunto unido e seu próprio ideal. Sem perfil ativo, julgamentos de gosto são opiniões do avaliador, mas não comprovam personalização.

### Precision@k

Consideramos relevante um candidato com julgamento 2 ou 3. Se 7 dos 10 são relevantes, `Precision@10 = 7/10 = 0,70`. Serve para medir quantos resultados úteis aparecem na primeira lista. Não considera a diferença entre posições e trata notas 2 e 3 igualmente.

Só calculamos quando todo o top k daquele sistema foi julgado. Se há apenas seis candidatos elegíveis, o resultado é **P@6**, nunca P@10 inventada. Mostrar menos de dez resultados pode ser correto com filtros estritos, proximidade mínima e exclusão de vistos. Aumentar o catálogo não garante dez obras dentro de qualquer combinação de filtros.

### nDCG@k

Utilizamos ganho `2^nota - 1`: notas 0,1,2,3 viram ganhos 0,1,3,7. Descontamos cada ganho por `log2(posição+1)` e somamos para obter DCG. Dividimos pela DCG ideal, calculada ordenando os julgamentos do **conjunto unido elegível daquela dimensão** do melhor para o pior. Assim valorizamos colocar resultados muito bons no começo.

Só calculamos nDCG após completar o conjunto unido daquela dimensão, necessário para conhecer o ideal. Se todos os ganhos são zero, nDCG permanece indefinida e o JSON sinaliza esse caso. O ideal é restrito ao pool avaliado, não ao catálogo inteiro; resultados relevantes fora do pool podem existir. Não chamamos esta medida de recall.

### Exportação e análise futura

Os julgamentos ficam no navegador. O botão exporta JSON com contexto, respostas, contagens e métricas. O arquivo pode conter opiniões pessoais: revise antes de compartilhar. Não inclui sua lista bruta ou notas do AniList. Julgamentos de QA são sintéticos e não contam como participantes.

**Nenhum resultado humano real foi fabricado nesta entrega.** Os valores de precisão e nDCG ficam ausentes até receber respostas suficientes. Para pesquisa, registrar várias consultas e avaliadores, comparar diferenças por consulta, informar tamanho da amostra e incerteza, e separar piloto para escolher pesos de conjunto final de teste. Usar apenas os exemplos escolhidos para calibrar e depois anunciar vitória seria enviesado.

## 6. Correções e validação

Foi corrigido um erro de dimensão no perfil vetorial JavaScript: havia trechos fixados em 100 dimensões, enquanto GloVe tem 50. Isso podia gerar valores não finitos no **laboratório personalizado**. Comparações pessoais desse laboratório anteriores à correção devem ser refeitas. A correção não invalida o ranking geral sem perfil nem, por si só, os experimentos científicos históricos executados por outro pipeline. Não reescrevemos seus resultados.

Metadados do catálogo congelado agora têm prioridade sobre cópias antigas guardadas no perfil, sem apagar notas. Perfis com obras externas ao snapshot são recodificados com o IDF atual quando necessário; isso pode carregar o codificador de aproximadamente 30 MB. O modo puro permanece independente do perfil.

Validação desta etapa: **26 testes Python**, testes do modo puro, 72 comparações numéricas de referência e 135 comparações das variantes Python/JavaScript, erro máximo abaixo de `2e-8`, além de checagem de sintaxe, dimensões, integridade do SQLite e distribuição pública. Os testes cobrem ausência de notas, fallback, limite do bônus, decomposição do score, BM25 sem termos compartilhados, métricas incompletas, ideal sem relevância e exclusão de itens conhecidos na avaliação de preferências. O workflow repete a validação antes da publicação.

## 7. Como usar agora

1. Abra o recomendador e escolha uma obra. O padrão continua sendo recomendação pura, vetores e temas, sem bônus.
2. Compare a mesma busca selecionando Híbrido e bônus máximo de 5%, então gere novamente. Inspecione as explicações, sem interpretar score como porcentagem de gostar.
3. Para avaliar personalização, ative seu perfil e mantenha os mesmos filtros durante a comparação.
4. Clique Avaliar esta busca, preencha as duas dimensões e exporte. As quatro estratégias são preparadas automaticamente no mesmo contexto.
5. Consulte Experimentos de RI para resultados automáticos, Laboratório para trocar embeddings e Atlas para verificar o dataset e SQL.

Fontes: [campos Media do AniList](https://docs.anilist.co/reference/object/media), [termos oficiais da API](https://github.com/AniList/docs/blob/master/docs/guide/terms-of-use.md), [avaliação de rankings — Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html), [BM25 no mesmo livro](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html). Parâmetros, normalização e política de bônus descritos acima são decisões deste projeto, não exigências dessas fontes.
