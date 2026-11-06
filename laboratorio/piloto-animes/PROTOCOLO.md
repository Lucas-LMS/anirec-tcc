# Protocolo congelado do piloto para a reuniao de 29/10/2026

Registrado antes de observar os rankings. Objetivo: comparar **pipelines disponiveis** para busca de animes por descricao livre. Nao isola causalmente algoritmos e nao mede preferencias reais de usuarios.

## Dados e julgamentos

39 animes reais referenciados pelo Anime Offline Database, release 2026-27 (metadados de 04/07/2026). Descricoes curtas originais e paralelas PT/EN preparadas com IA, sem copiar sinopses oficiais. Os titulos, IDs, tags e notas publicas nao entram nos vetores. Nenhuma consulta contem titulo do anime. Dados e qrels em `dados/`, com hashes congelados em `freeze.json`.

58 consultas: 29 intencoes com duas formulacoes (literal e parafrase). Os 2.262 pares consulta/item foram julgados antes das predicoes: 2=fortemente pertinente, 1=parcialmente pertinente, 0=nao selecionado como pertinente para aquela intencao. As formulacoes PT/EN e as variantes de cada intencao compartilham os mesmos julgamentos.

**Limitacao central:** os textos, consultas e qrels foram preparados com assistencia de IA, sem validacao humana independente. Catalogo selecionado por conveniencia e interesse tematico, nao amostra aleatoria. Ha vies de autoria e cobertura intencional de enredos. O piloto apoia uma decisao tecnica provisoria; nao sustenta superioridade universal nem uma conclusao cientifica final.

## Cenarios

- **PT_EN — principal, confirmado pelo usuario:** consulta portuguesa sobre descricoes inglesas.
- EN_EN — diagnostico monolingue ingles.
- PT_PT — diagnostico monolingue portugues com as descricoes preparadas para este piloto.

Os mesmos IDs, relevancias e intencoes sao usados nos tres cenarios. Eles nao sao tratados como tres amostras independentes. O cenario principal nao sera escolhido depois de ver os resultados.

## Sistemas e parametrizacao previa

1. TF-IDF: tokenizer Unicode comum, unigramas/bigramas, TF sublinear, IDF aprendido apenas no catalogo do cenario e normalizacao L2. Sem lista de stopwords, tradutor ou ajuste por consulta.
2. GloVe text8, 50d: media de vetores ponderada por IDF do catalogo; palavras ausentes descartadas e cobertura registrada.
3. fastText fil9, 100d: mesma agregacao; vetores obtidos pelo executavel oficial, incluindo subpalavras para termos ausentes.
4. Word2Vec CBOW text8, 100d: cinco epocas, janela 5, min_count 5, quatro workers, seed 20261029. Mesma agregacao IDF.
5. Word2Vec Skip-gram text8, 100d: igual ao anterior, mudando sg=1.
6. MiniLM multilingue, 384d: pesos e revisao ja testados, encode direto da descricao completa em CPU, quatro threads. Sem fine-tuning, prompt ou alteracao do limite de entrada. Contar tokens e confirmar ausencia de truncamento neste piloto.

As duas versoes Word2Vec Lee sao medidas como **diagnostico adicional**, sem usa-las para excluir a familia Word2Vec. Sao demonstracoes pequenas e nao representam a capacidade do algoritmo. Os novos treinos em text8 nao usam o catalogo ou julgamentos de anime. GloVe/Word2Vec compartilham text8, mas dimensoes, objetivos e hiperparametros nao sao igualados; fastText usa fil9, e MiniLM tem pretreinamento muito maior. A comparacao nao e um ablation de arquitetura.

O classificador fastText cooking nao entra, pois aprende rotulos de culinaria; nao e um mecanismo de busca de animes. GPT, Llama e DeepSeek nao sao comparados: nao foram instalados/testados como rerankers nesta etapa.

## Metricas e desempates

- Primaria: nDCG@5 com ganho `2**grau - 1`; valor entre 0 e 1.
- Hit@1: fracao de consultas cujo primeiro item e grau 2.
- MRR@10: reciproco da primeira posicao de item grau 2, zero se nenhum nos dez primeiros.
- Recall@5: fracao dos itens com grau >=1 recuperada entre os cinco primeiros.
- Metricas de cobertura, consultas sem vetor e tempos/recursos como diagnostico.

Empates de score usam valor esperado sob permutacoes uniformes dentro do empate, incluindo MRR e Hit. Assim, uma consulta sem vetor nao e beneficiada por uma ordem de IDs. Os rankings ilustrativos usam desempate fixo por ID apenas para exibicao. Uma referencia de scores todos iguais representa busca sem informacao.

Incerteza exploratoria: bootstrap pareado por **familia de intencao**, mantendo juntas as duas formulacoes e sem misturar cenarios; 5.000 reamostragens, seed 20261029. Os intervalos nao capturam vies de anotacao, nao tornam a amostra representativa e nao sao uma prova de generalizacao. Nenhum hiperparametro sera escolhido a partir destas consultas.

## Desempenho

Um processo por modelo e somente um encoder medido por vez. Registrar carregamento, tempo total de codificacao e recursos do processo. Consultas em lote/cache nao sao latencia de uma API interativa; os tempos devem ser rotulados pelo que medem. Os modelos estaticos consultam vetores lexicais; o fastText usa um processo persistente do executavel e cache de termos. Os vetores e scores completos sao preservados.

## Decisao e escopo academico

O melhor no piloto e o maior nDCG@5 no cenario principal, relatando os demais criterios e exemplos de erro. A recomendacao para o TCC considera tambem suporte ao cenario PT_EN, necessidade de treino, explicabilidade, cobertura, tamanho, processamento local e risco de integracao. Uma diferenca pequena ou instavel nao sera descrita como vitoria definitiva.

No TCC, priorizar implementacao e avaliacao de uma arquitetura de recuperacao/ranking com um modelo principal. Na iniciacao cientifica, expandir corpus, avaliadores humanos cegos, consultas reais, separacao validacao/teste, controle de corpora e orcamento de treinamento, estudos de agregacao, multiplas sementes e replicacao. Este piloto nao substitui essa investigacao.
