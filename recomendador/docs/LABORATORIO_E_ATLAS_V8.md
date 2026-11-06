# Laboratório de modelos e atlas do dataset — 06/11/2026

## O que foi entregue

O recomendador principal continua usando Word2Vec Skip-gram text8 100d. Uma área experimental separada no mesmo site permite selecionar Word2Vec Skip-gram, Word2Vec CBOW, GloVe ou fastText e comparar os quatro no mesmo catálogo congelado. Não substituímos silenciosamente o modelo do programa principal.

- Site: https://anirec-ri-animes.givingbamboo.chatgpt.site
- Laboratório: `/laboratorio.html`.
- Atlas visual: `/dataset.html`.
- Local: os mesmos caminhos em http://127.0.0.1:8765.

Esses modelos foram treinados anteriormente nos exercícios documentados, fora do aplicativo. Nesta etapa apenas carregamos os artefatos existentes e calculamos representações de documentos. Não treinamos nem ajustamos modelos.

## Quais vetores usamos

| Artefato | Dimensão | Corpus | Arquivo de origem na máquina |
|---|---:|---|---|
| Word2Vec Skip-gram | 100 | text8 | `/home/lucas/tcc-lab/Word2Vec/models/text8-skipgram-100d.model` |
| Word2Vec CBOW | 100 | text8 | `/home/lucas/tcc-lab/Word2Vec/models/text8-cbow-100d.model` |
| GloVe | 50 | text8 | `/home/lucas/tcc-lab/GloVe/vectors.txt` |
| fastText Skip-gram | 100 | fil9 | `/home/lucas/tcc-lab/fastText/result/fil9.bin` |

Word2Vec CBOW agrega o contexto para prever palavras; Skip-gram usa a palavra para prever contextos. GloVe usa estatísticas globais de coocorrência. fastText representa palavras também por partes de palavras. Nesta exportação usamos o `.bin` completo do fastText para obter vetores de termos fora do vocabulário, preservando esse recurso; não limitamos ao `.vec`.

Fontes oficiais: [Gensim Word2Vec](https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html), [GloVe Stanford](https://nlp.stanford.edu/projects/glove/), [tutorial fastText](https://fasttext.cc/docs/en/unsupervised-tutorial.html). Parâmetros recuperáveis e hashes dos artefatos estão em `online/lab/models.json`. Word2Vec: janela 5, min_count 5, épocas 5, negative 5, seed 20261029; sg=1 para Skip-gram e sg=0 para CBOW. Não inferimos parâmetros de treinamento do GloVe a partir de seus vetores: os logs históricos são a fonte para isso.

## Protocolo experimental

1. Congelar exatamente as mesmas 2.495 obras públicas do catálogo AniList, identificadas por SHA-256.
2. Usar a sinopse inglesa inteira, a mesma tokenização e o mesmo IDF.
3. Para cada modelo, calcular a média ponderada dos vetores das palavras e normalizar o vetor do documento. Documento sem termos utilizáveis recebe vetor zero e é excluído do ranking.
4. Trocar os vetores de **todos** os documentos e do perfil juntos. Não misturar vetores de modelos diferentes, inclusive quando a dimensão numérica coincide.
5. Manter 50% sinopse / 50% temas na referência, 70% texto / 30% temas no perfil, influência 35% e proximidade temática mínima 0,25. Filtros de interesses evitados podem ser aplicados ou desativados pelo controle de perfil.
6. Calcular três execuções após aquecimento, apresentar a mediana do tempo de ranking e medir o carregamento separadamente. Carregamento pode ser zero numa nova execução com os vetores já em memória.

A comparação usa somente o catálogo congelado. No teste com o perfil local, 2.427 notas tinham correspondência nesse catálogo; 12 obras avaliadas estavam fora e foram explicitamente excluídas **apenas do experimento**. O recomendador normal mantém o histórico completo. O filtro por catálogo é necessário para comparar as mesmas obras com todos os modelos sem misturar espaços vetoriais.

As exclusões e preferências deste ambiente podem ser aplicadas ao modo Geral também; desmarque o controle do perfil para uma comparação sem seus filtros. O laboratório não importa automaticamente o perfil local para o site. Não publica avaliações individuais.

## Primeiro resultado observado

Consulta Lycoris Recoil, modo Geral, interesses/exclusões do perfil local ativos, mesmo corpus e parâmetros:

| Modelo | Sobreposição do top 10 com Skip-gram | Mediana do ranking | Carregamento inicial observado |
|---|---:|---:|---:|
| Skip-gram | 100% | 158,30 ms | 83,50 ms |
| CBOW | 50% | 105,60 ms | 58,70 ms |
| GloVe | 100% | 118,90 ms | 45,50 ms |
| fastText | 90% | 111,40 ms | 68,10 ms |

São medições preliminares no navegador local, não benchmarks de latência universais. Cobertura média de tokens por documento: cerca de 93,56% para Word2Vec/GloVe e 99,88% para fastText com subpalavras, incluindo documentos vazios com cobertura zero. Cobertura não mede qualidade semântica. Cada modelo tem três documentos nulos, pela ausência de texto utilizável.

**Sobreposição@10** = quantidade de títulos comuns aos dois top 10 / 10 (ou tamanho da lista de referência, se menor). Não considera a ordem e não é precisão. GloVe compartilhar dez títulos não significa reproduzir os mesmos scores ou posições. Cada cosseno está em seu próprio espaço; não escolher o vencedor pelo maior score bruto.

Não há vencedor demonstrado. Os corpora e dimensões diferem, logo o experimento compara **artefatos instalados**, não o efeito isolado do algoritmo. Recomendação científica: conservar Skip-gram como referência, fazer julgamentos de relevância com âncoras variadas e avaliar ranking antes de trocar o modelo definitivo. Sem esses julgamentos não calculamos precisão, MAP ou nDCG como se houvesse gabarito.

O arquivo `output/prototipo/v8/comparacao-lycoris-estaticos.json` preserva parâmetros, hashes, tempos e top 10 dos dois modos para todos os modelos. A seleção do modo na tela não refaz as medições: alterna entre os resultados já calculados. Trocar a âncora ou o controle de perfil exige executar novamente.

## Melhorias no recomendador normal

- Funil explícito: candidatos → elegíveis → selecionados pelo modo → conhecidos + descobertas. A contagem agora acompanha Geral ou Para mim, resolvendo a ambiguidade anterior.
- Abertura dos motivos de exclusão e comparação de posições entre Geral e Para mim. A interface mostra temas em comum e afinidade; não atribui causalidade exclusiva a uma única tag.
- **Buscar mais descobertas** busca novos candidatos ligados aos gêneros da referência, excluindo IDs já disponíveis/conhecidos. Não reduz silenciosamente os filtros. O usuário pode escolher proximidade 0,15 ou 0 para ampliar o recorte de forma explícita.
- Teste local real: a consulta passou de 2.495 para 2.625 candidatos e de uma para quatro descobertas personalizadas, mantendo a proximidade 0,25 e a exclusão de Male Protagonist. Isso não garante dez resultados para todo perfil.
- Diversificação opcional por nomes: remove repetições por prefixo de título/temporada. É **heurística**, não agrupamento oficial por franquia; pode agrupar títulos distintos ou deixar passar temporadas. Fica desligada por padrão e não modifica scores.
- Julgamentos “Faz sentido”, “Não combina com a referência”, “Não combina comigo” ficam neste navegador e podem ser exportados. Não treinam modelo nem alteram automaticamente o ranking. Registram âncora, candidato, modo, parâmetros e score. Devem ser tratados como dados pessoais de avaliação, separados do dataset de obras e dos testes fictícios de interface.

## Atlas do dataset: o que é real

O painel lê os metadados das mesmas 2.495 obras do laboratório. Tem quatro gráficos, filtros por título/gênero/formato, ordenação, tabela paginada e inspeção da sinopse inteira. Paginação de 20 linhas é apenas visual: todas as obras continuam disponíveis.

O diagrama explica extração → tratamento → SQLite → representação → recuperação. O percurso da última consulta do recomendador vem de uma execução real registrada localmente, com horário, filtros, contagens e tempo; quando não existe, o painel diz isso. Não existe animação fictícia apresentada como processamento real. Recarregue o painel depois de executar uma nova recomendação para atualizar o percurso.

O banco para download é `online/lab/corpus.sqlite3`, construído especificamente a partir desse snapshot público. Tem as tabelas `works`, `genres`, `tags` e `vectors`; esta última contém quatro vetores por obra (9.980 linhas), com identificação do modelo e dimensão. Não contém tabelas de notas, perfis ou lista de usuário. Esse banco de distribuição é distinto do SQLite operacional privado da máquina e do export histórico de 2.507 obras. Números históricos não são misturados às contagens atuais do snapshot público.

Cinco consultas foram realmente executadas pelo SQLite ao construir o banco. O painel apresenta SQL e resultados congelados em `lab/queries.json`, explicitamente identificados como tal, não um console SQL ao vivo. Exemplo reproduzível:

```python
import sqlite3

with sqlite3.connect('corpus.sqlite3') as db:
    # Conta cada obra uma vez, sem multiplicação por suas tags.
    print(db.execute('SELECT COUNT(*) FROM works').fetchone()[0])
    # Verifica se todos os modelos possuem uma representação por obra.
    print(db.execute('SELECT model, dimensions, COUNT(*) FROM vectors '
                     'GROUP BY model, dimensions').fetchall())
```

Exemplo de inspeção de sinopses e consulta relacional:

```sql
SELECT w.anilist_id, w.title, w.word_count
FROM works w
JOIN genres g USING(anilist_id)
WHERE g.genre = 'Action' AND w.title LIKE '%Lycoris%'
ORDER BY w.title;
```

O `JOIN` liga a obra à sua categoria pelo ID. A condição seleciona Action e títulos contendo Lycoris. A contagem de palavras é da sinopse tratada, e não do título. O banco publicado passou em `PRAGMA integrity_check` e não teve gêneros com IDs órfãos.

## Reproduzir a construção

No WSL e ambiente Python já preparado, a partir da pasta `recomendador`:

```bash
python build_laboratory.py
python build_public_sqlite.py
python -m unittest test_laboratory -v
```

O primeiro script carrega modelos existentes, gera os quatro arquivos binários de vetores e o manifesto. O segundo cria o SQLite público e executa as consultas de prova. Não há treinamento. O navegador verifica SHA-256 e dimensões dos vetores antes de comparar. Gráficos usam Chart.js 4.5.1, copiado para `lab/chart.umd.js`, funcionando sem CDN durante o uso.

Verificação: 18 testes de recuperação/ETL/afinidade (incluindo expansão explícita de candidatos) e dois testes novos de integridade do laboratório passaram. Os testes novos verificam alinhamento de IDs, hashes, dimensões, valores finitos, normalização, igualdade do Skip-gram exportado com a versão atual e ausência de tabelas de usuário no SQLite público. A paridade Python/JavaScript anterior continua passando em 72 comparações numéricas.

## Crescimento do dataset

2.495 é o tamanho desta publicação, não um teto do SQLite. A arquitetura separa catálogo, perfil, vetores e apresentação. Crescer exige coleta autorizada, IDs únicos, proveniência, atualizações incrementais, verificação de ausências, recálculo versionado de IDF/vetores e novos testes. O painel torna o viés de seleção visível: predominância por década/gênero pode refletir o histórico de uso e a popularidade, e não a composição do catálogo do AniList.

A autorização solicitada ao AniList para ambição de catálogo completo segue pendente. Não declaramos ter esse catálogo nem transformamos coleta lenta em mecanismo para contornar restrições. A versão estática online usa snapshots; um catálogo muito maior poderá exigir backend/índice paginado, mantendo a recuperação determinística e a versão local para experimentos.
