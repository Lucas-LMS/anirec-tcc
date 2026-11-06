# AniRec: comparação piloto e escolha provisória para o TCC

29/10/2026 • Lucas • cenário prioritário confirmado: consultas em português e descrições em inglês.

## 1. Decisão que os dados permitem tomar

Recomendo **paraphrase-multilingual-MiniLM-L12-v2 como encoder principal do protótipo do TCC**. Neste catálogo e nestas consultas, teve nDCG@5 de **0,805**, Hit@1 de **47/58 = 81,0%**, MRR@10 de 0,878 e Recall@5 de 72,7%. Opera localmente em CPU, já foi carregado com os arquivos locais e dispensa treinar um modelo de linguagem para iniciar o sistema.

Essa é uma decisão de engenharia apoiada por um piloto controlado. Não demonstra que MiniLM seja universalmente melhor, nem que a arquitetura dos modelos estáticos seja incapaz de servir ao projeto. Escolhemos o melhor dos pipelines disponíveis para o requisito PT → EN. O uso de descrições e julgamentos preparados com IA exige confirmação humana antes de uma conclusão científica.

## 2. O que já está funcional

- GloVe oficial compilado e treinado no demo text8: 50 dimensões, 71.290 palavras. Analogia oficial: 23,50% nas questões cobertas, com 91,21% de cobertura. Esse teste verifica aprendizado lexical; não mede recomendação de animes.
- fastText oficial v0.9.2 compilado com G++ 12 e treinado em fil9/enwik9: Skip-gram, 100 dimensões, 218.316 entradas, uma época. O tutorial de classificação cooking também foi executado, mas seu classificador não participa desta busca.
- Rare Words do fastText resolvido: avaliador oficial aplicado a 2.034 pares, zero pares descartados, Spearman rho = **0,4177019**. A origem Stanford estava inacessível; usamos cópia histórica AWS e corroboramos todos os pares/notas com cópia acadêmica. Não há checksum publicado da origem para afirmar identidade binária. Detalhes em `../../docs/07-rare-words-resolucao.md`, e no registro de fontes do laboratório.
- Word2Vec Gensim 4.4: CBOW e Skip-gram nos exemplos Lee, mais novos treinos em text8 para este piloto. Text8: 100 dimensões, cinco épocas, janela 5, min_count 5, quatro workers, seed 20261029, 71.290 palavras. Lee é apenas demonstração e não decide a exclusão do Word2Vec.
- Sentence Transformers MiniLM multilíngue: pesos salvos localmente, 384 dimensões, inferência CPU e carregamento offline verificados. Revisão fixada: e8f8c211226b894fcb81acc59f3b34ba3efd5f42.
- TF-IDF é a referência lexical adicional; não necessita pesos pré-treinados.

Nenhum GPT, Llama ou DeepSeek gerador foi instalado ou comparado. O MiniLM usado é um encoder de embeddings, não um chatbot gerador. “Funcional” significa que os testes documentados passaram; não significa que um produto final de recomendação esteja pronto ou validado.

## 3. Base: o que veio de uma fonte e o que foi criado

Selecionamos **39 animes reais**, identificados no Anime Offline Database, release 2026-27, metadados de 04/07/2026. O download do JSON completo ficou em C:/tcc-lab/Pilot, com 62.331.136 bytes; o subconjunto de metadados está preservado em `dados/brutos/aod-subconjunto.json`. A consulta à API Jikan não forneceu a base deste experimento.

**As descrições bilingues são textos curtos originais preparados com IA, não sinopses oficiais obtidas dessa base.** Consultas e relevâncias também foram preparadas com assistência de IA, sem anotadores humanos independentes. O catálogo foi escolhido por conveniência e diversidade temática. Isso facilita demonstrar o mecanismo, mas cria viés de autoria, vocabulário e cobertura intencional de enredos. Não apresentar estes textos como um benchmark público validado.

São 58 consultas, duas versões por 29 intenções: uma direta e uma paráfrase. As traduções PT/EN compartilham o mesmo julgamento. Os **2.262 pares** consulta/anime têm grau 2 (fortemente pertinente), 1 (parcialmente pertinente) ou 0 (não selecionado como pertinente). Grau 0 reflete o julgamento operacional do piloto, não uma verdade universal sobre a obra.

O protocolo, os textos e os julgamentos foram congelados antes de observar rankings. Hashes estão em `dados/freeze.json`. Títulos, IDs, gêneros e notas públicas não entram nos vetores. Nenhum modelo foi treinado com os julgamentos de anime; nenhum hiperparâmetro foi escolhido depois dos resultados. Para o TCC, substituir/complementar estas descrições por sinopses reais com fonte e condições de uso registradas.

Fonte: [Anime Offline Database](https://github.com/manami-project/anime-offline-database). Preservar atribuição e as licenças ODbL 1.0 / DbCL 1.0 dos metadados derivados; cópia da licença em dados/brutos.

## 4. Como cada busca funciona

TF-IDF: tokenização Unicode, unigramas/bigramas, frequência sublinear e IDF aprendido somente nas descrições do catálogo de cada cenário. Não utiliza tradução.

GloVe, fastText e Word2Vec: tokenização NFKC/casefold e letras Unicode; média dos vetores das palavras ponderada pelo IDF do catálogo, seguida de normalização L2. Palavras ausentes são descartadas em GloVe/Word2Vec. O fastText usa o executável oficial e subpalavras para gerar vetores também fora do vocabulário.

MiniLM: encode do texto completo com o tokenizer próprio, normalização L2 e similaridade por produto escalar, equivalente ao cosseno para vetores unitários. Não aplica a tokenização lexical comum antes do encoder. O maior texto teve **60 tokens**, abaixo do limite de 128; **nenhuma entrada foi truncada**. Sinopses reais longas exigirão definir e avaliar segmentação/agregação; este piloto não testa isso.

Todos ranqueiam os mesmos 39 candidatos. A documentação oficial do Sentence Transformers descreve embeddings e similaridade; a escolha do catálogo, média IDF e protocolo de comparação é nossa implementação experimental, não um benchmark oficial dos fabricantes.

Fontes: [similaridade no Sentence Transformers](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html), [cartão do modelo MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2), [tutorial fastText](https://fasttext.cc/docs/en/unsupervised-tutorial.html), [GloVe oficial](https://github.com/stanfordnlp/GloVe), [Word2Vec Gensim](https://radimrehurek.com/gensim/models/word2vec.html), [TF-IDF sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).

## 5. Métricas e confiabilidade do cálculo

**nDCG@5** é a métrica principal: avalia ordem e graus de relevância dos cinco primeiros, com ganho 2^grau - 1, normalizado pelo ranking ideal. Varia de 0 a 1. **0,805 não significa 80,5% de acurácia**.

Hit@1 conta consultas cujo primeiro item é grau 2. MRR@10 considera o inverso da posição do primeiro grau 2 nos dez primeiros. Recall@5 conta a proporção dos itens grau 1 ou 2 recuperados entre os cinco primeiros; seu denominador pode ser maior que cinco.

Empates usam o valor esperado sob permutações uniformes, inclusive quando não há vetor. Assim, IDs não produzem acertos artificiais. O painel exibe uma ordem fixa por ID nos empates; ela não deve ser confundida com evidência de preferência do modelo. Scores de diferentes modelos não são probabilidades nem são diretamente comparáveis.

A implementação de nDCG foi conferida em **1.392 casos** contra sklearn, diferença máxima 3,33e-16; um exemplo pequeno de empate foi verificado separadamente. Os intervalos de 95% usam 5.000 reamostragens bootstrap por **29 famílias de intenção**, mantendo as duas formulações juntas. Não consideramos 174 consultas independentes ao juntar idiomas. Os intervalos quantificam variação nesta amostra, não corrigem viés de autoria ou ausência de anotadores humanos.

## 6. Resultado principal: português → inglês

| Pipeline | nDCG@5 | Hit@1 | MRR@10 | Recall@5 | IC exploratório nDCG |
| --- | --- | --- | --- | --- | --- |
| TF-IDF | 0.127 | 10.6% | 0.160 | 13.6% | [0.082; 0.176] |
| GloVe text8 50d | 0.115 | 5.2% | 0.112 | 14.9% | [0.060; 0.180] |
| fastText fil9 100d | 0.148 | 5.2% | 0.160 | 17.1% | [0.080; 0.222] |
| Word2Vec CBOW text8 | 0.084 | 3.4% | 0.085 | 12.4% | [0.035; 0.145] |
| Word2Vec Skip-gram text8 | 0.084 | 3.4% | 0.089 | 12.9% | [0.037; 0.147] |
| MiniLM multilíngue | 0.805 | 81.0% | 0.878 | 72.7% | [0.747; 0.857] |

MiniLM supera fastText, o segundo maior nDCG neste cenário, por 0,658; intervalo bootstrap pareado exploratório [0,562; 0,748]. Essa diferença é consistente dentro do piloto. Não apresentamos isso como prova de superioridade universal ou estudo causal de arquitetura.

Separação por formulação: MiniLM teve nDCG 0,904 e Hit@1 29/29 nas consultas diretas; nas paráfrases, nDCG 0,707 e Hit@1 **18/29**. Portanto, a média total esconde erros importantes quando o usuário se afasta das palavras mais diretas do enredo.

## 7. Idioma muda a interpretação

Valores abaixo são nDCG@5; os três cenários reutilizam intenções e julgamentos.

| Pipeline | PT → EN | EN → EN | PT → PT |
| --- | --- | --- | --- |
| TF-IDF | 0.127 | 0.680 | 0.646 |
| GloVe text8 50d | 0.115 | 0.606 | 0.275 |
| fastText fil9 100d | 0.148 | 0.723 | 0.367 |
| Word2Vec CBOW text8 | 0.084 | 0.601 | 0.171 |
| Word2Vec Skip-gram text8 | 0.084 | 0.739 | 0.319 |
| MiniLM multilíngue | 0.805 | 0.843 | 0.789 |

Em inglês, Word2Vec Skip-gram text8 alcança 0,739 e fastText 0,723; TF-IDF chega a 0,680 e GloVe a 0,606. Isso mostra que os pipelines estáticos estão produzindo informação útil no idioma em que foram treinados. Sua queda em PT → EN não permite concluir que o algoritmo é ruim: falta um espaço semanticamente alinhado entre os idiomas nessa configuração.

O fastText gera vetor utilizável para **100%** dos tokens portugueses destas consultas, mas apenas 53,3% pertencem ao vocabulário treinado; GloVe/Word2Vec cobrem 45,1%. Cobertura mede disponibilidade lexical, não entendimento ou tradução. Subpalavras ajudam com formas desconhecidas, mas não criam por si sós alinhamento português/inglês. Para TF-IDF EN, apenas 3,5% dos tokens das consultas PT pertencem ao vocabulário do catálogo.

## 8. Por que continuar com MiniLM e não priorizar os outros no TCC

### MiniLM multilíngue: escolha principal

O requisito decisivo é atravessar português e inglês sem exigir que o usuário traduza a consulta. O modelo representa frases completas e foi disponibilizado para similaridade/busca semântica multilíngue. A evidência deste piloto favorece a configuração já instalada, sem treino adicional. Arquitetura proposta: descrição inglesa → embedding persistido; consulta portuguesa → embedding; cosseno → top-k de animes. É uma base adequada para construir o protótipo e avaliar o fluxo de recuperação.

Custos e limitações: mais dependências e custo de codificação que TF-IDF/GloVe; limite de entrada curto; erros em nuances de enredo; cosseno não é confiança calibrada. Não há ainda latência de API medida nem validação com usuários. É busca por conteúdo, não recomendação personalizada por histórico ou preferência individual. Essas etapas precisam ser definidas no escopo do TCC.

### fastText: manter como comparador estático

Tem valor por subpalavras, tratamento de formas raras e desempenho monolíngue útil. A instalação e Rare Words estão funcionando. Porém, o modelo inglês local não atende bem ao requisito PT → EN: nDCG 0,148 e Hit@1 3/58, apesar de gerar vetores para todos os termos. Além disso, a média de vetores perde relações entre palavras. Não escolher como núcleo agora reduz o trabalho de alinhar idiomas ou adicionar tradução antes de construir o produto.

Alternativas para a IC: vetores fastText português/inglês alinhados oficialmente, ou uma etapa fixa de tradução PT → EN seguida do mesmo buscador inglês. Treinar dois espaços separados, um por idioma, não basta: seus eixos precisam estar alinhados. A variante com tradução deve ser avaliada como pipeline próprio, contabilizando qualidade, tempo, dependências e erro do tradutor. Não foi instalada nem testada neste piloto.

### GloVe: referência clássica, sem prioridade de integração

Seu demo prova que o algoritmo e a ferramenta funcionam. No pipeline atual, palavras fora do vocabulário são descartadas e uma palavra conserva o mesmo vetor independentemente da frase; a média IDF também ignora ordem. A configuração inglesa 50d teve nDCG 0,115 em PT → EN. Para atender ao produto, seria preciso outro corpus/modelo, alinhamento ou tradução e nova avaliação. Manter como referência científica; não gastar o escopo inicial do TCC nessas adaptações.

### Word2Vec CBOW e Skip-gram: distinguir exemplo pequeno de candidato real

Não rejeitamos Word2Vec por causa do corpus didático Lee. Treinamos também CBOW e Skip-gram em text8, sem usar animes, e o Skip-gram mostrou resultado competitivo em inglês (0,739). Contudo, ambos ficam perto de 0,084 em PT → EN. O obstáculo combina idioma, vocabulário e agregação lexical; CBOW e Skip-gram não resolvem alinhamento automaticamente. Treinar um corpus pequeno de animes também não garante vetores melhores. Novas bases, múltiplas sementes e outros agregadores pertencem à investigação da IC.

### TF-IDF: conservar como controle barato

É simples, auditável e útil quando as mesmas palavras aparecem na consulta e descrição. Neste piloto em inglês teve 0,680, mas em PT → EN caiu para 0,127. Não atende sozinho à busca semântica entre idiomas. Deve permanecer como baseline para medir se a complexidade do encoder compensa. Não há razão para apagar os outros modelos ou encerrar sua investigação.

### GPT, Llama e DeepSeek

Não participaram do teste e não há pesos de geradores instalados. Portanto, não há evidência experimental para dizer que perdem para MiniLM. Um gerador pode futuramente explicar resultados ou reordenar candidatos, mas introduz outro problema de custo, avaliação e possíveis respostas inventadas. Para a entrega inicial, o encoder local já resolve a operação central de produzir vetores e ordenar candidatos. Não é necessário instalar um gerador agora para implementar essa arquitetura.

## 9. Exemplos concretos e erros preservados

### I01-paraphrase

Um jovem brilhante decide quem merece viver enquanto um perseguidor tenta desmascará-lo.

| Pipeline | Primeiro resultado | Grau |
| --- | --- | --- |
| TF-IDF | Cowboy Bebop | 0 |
| GloVe text8 50d | Steins;Gate | 0 |
| fastText fil9 100d | Gintama | 0 |
| Word2Vec CBOW text8 | Natsume Yuujinchou | 0 |
| Word2Vec Skip-gram text8 | Death Note | 2 |
| MiniLM multilíngue | Death Note | 2 |

Scores empatados podem tornar o primeiro item exibido arbitrário; as métricas usam a expectativa do empate.

### I04-paraphrase

Um forasteiro precisa reviver erros fatais em um reino desconhecido para impedir uma catástrofe.

| Pipeline | Primeiro resultado | Grau |
| --- | --- | --- |
| TF-IDF | Cowboy Bebop | 0 |
| GloVe text8 50d | Violet Evergarden | 0 |
| fastText fil9 100d | Naruto | 0 |
| Word2Vec CBOW text8 | Natsume Yuujinchou | 0 |
| Word2Vec Skip-gram text8 | Natsume Yuujinchou | 0 |
| MiniLM multilíngue | Re:Zero | 2 |

Scores empatados podem tornar o primeiro item exibido arbitrário; as métricas usam a expectativa do empate.

### I10-paraphrase

Irmãos pagam um preço físico terrível por um ato proibido e procuram uma forma de voltar a ser completos.

| Pipeline | Primeiro resultado | Grau |
| --- | --- | --- |
| TF-IDF | Psycho-Pass | 0 |
| GloVe text8 50d | Violet Evergarden | 0 |
| fastText fil9 100d | Chihayafuru | 0 |
| Word2Vec CBOW text8 | Ghost in the Shell | 0 |
| Word2Vec Skip-gram text8 | Death Note | 0 |
| MiniLM multilíngue | Fullmetal Alchemist: Brotherhood | 2 |

Scores empatados podem tornar o primeiro item exibido arbitrário; as métricas usam a expectativa do empate.

### Todos os 11 casos em que MiniLM não colocou grau 2 em primeiro

- **I02-paraphrase** — Um homem tenta reparar as consequências de salvar uma vida que depois destrói outras vidas.
  Primeiro resultado: **Re:Zero**, grau 0. Alvo(s) forte(s): Monster; primeiro grau 2 na posição 6.

- **I03-paraphrase** — Mudar o dia de ontem repetidamente cria novas tragédias para quem um pesquisador deseja proteger.
  Primeiro resultado: **Re:Zero**, grau 1. Alvo(s) forte(s): Steins;Gate; primeiro grau 2 na posição 2.

- **I05-paraphrase** — Pessoas já não conseguem sair do lugar digital onde costumavam se divertir juntas.
  Primeiro resultado: **Steins;Gate**, grau 0. Alvo(s) forte(s): Log Horizon, Sword Art Online; primeiro grau 2 na posição 2.

- **I06-paraphrase** — Alguém excluído de uma sociedade de pessoas especiais conquista um lugar entre seus protetores.
  Primeiro resultado: **Naruto**, grau 0. Alvo(s) forte(s): My Hero Academia; primeiro grau 2 na posição 2.

- **I08-paraphrase** — Um órfão rejeitado deseja que a comunidade que o teme finalmente reconheça seu valor.
  Primeiro resultado: **Mob Psycho 100**, grau 0. Alvo(s) forte(s): Naruto; primeiro grau 2 na posição 5.

- **I12-paraphrase** — Investigadores atuam em um futuro no qual máquinas questionam o que significa ser uma pessoa ou ser culpado.
  Primeiro resultado: **Steins;Gate**, grau 0. Alvo(s) forte(s): Ghost in the Shell, Psycho-Pass; primeiro grau 2 na posição 2.

- **I13-paraphrase** — Jovens defensores carregam o peso emocional de salvar outras pessoas enquanto mal compreendem a própria dor.
  Primeiro resultado: **Mob Psycho 100**, grau 0. Alvo(s) forte(s): Neon Genesis Evangelion; primeiro grau 2 na posição 4.

- **I15-paraphrase** — Viajantes sem rumo com passados difíceis cruzam fronteiras estranhas onde violência e sobrevivência se encontram.
  Primeiro resultado: **Princess Mononoke**, grau 0. Alvo(s) forte(s): Cowboy Bebop, Trigun; primeiro grau 2 na posição 3.

- **I16-paraphrase** — Companheiros de personalidades conflitantes seguem uma busca pessoal entre duelos e encontros na estrada.
  Primeiro resultado: **Your Name**, grau 0. Alvo(s) forte(s): Samurai Champloo; primeiro grau 2 na posição 16.

- **I19-paraphrase** — Um atleta de baixa estatura e um rival talentoso aprendem a confiar um no outro em quadra.
  Primeiro resultado: **Kuroko no Basket**, grau 1. Alvo(s) forte(s): Haikyuu!!; primeiro grau 2 na posição 2.

- **I29-paraphrase** — Um grupo caótico aceita trabalhos absurdos para pagar as contas em um mundo que mistura tradições antigas e visitantes do espaço.
  Primeiro resultado: **Cowboy Bebop**, grau 0. Alvo(s) forte(s): Gintama; primeiro grau 2 na posição 2.

Há casos de proximidade temática e casos de perda do detalhe decisivo da consulta. Um grau 1 pode ser uma sugestão aceitável, mas continua sendo falha no Hit@1 forte definido previamente. Não alteramos os julgamentos depois de ver esses erros. A próxima análise humana deve revisar os pares sem mostrar qual modelo os produziu; discordâncias precisam ser registradas, não corrigidas silenciosamente para favorecer o vencedor.

## 10. Recursos observados nesta máquina

Ryzen 5 2400G, CPU, WSL2 com aproximadamente 6,7 GiB disponíveis e 2 GiB swap. Um processo de encoder por vez; quatro threads no MiniLM. Tabela registra o processo observado, incluindo imports e bibliotecas.

| Pipeline | Pico RSS (MiB) | Carregamento (s) | Cache de textos/termos (s) |
| --- | --- | --- | --- |
| TF-IDF | 120.5 | 2.24 | 0.000 |
| GloVe text8 50d | 37.6 | 0.12 | 0.000 |
| fastText fil9 100d | 1065.8 | 3.74 | 0.327 |
| Word2Vec CBOW text8 | 171.5 | 6.06 | 0.000 |
| Word2Vec Skip-gram text8 | 171.7 | 2.78 | 0.000 |
| MiniLM multilíngue | 919.0 | 16.85 | 6.437 |

**Esses números não são latência online por consulta nem um benchmark justo de velocidade.** Os modelos lexicais possuem estratégias de carregamento/cache diferentes; GloVe pode ler apenas vetores necessários. MiniLM codificou o lote completo de 194 textos únicos em cerca de 6,44 s após carregamento, não uma chamada de API individual. Pico RSS não é tamanho do arquivo e não equivale a toda a memória do sistema. Ainda faltam repetições, aquecimento, concorrência e medição separada da consulta com catálogo pré-indexado.

## 11. O que relatar na reunião

“Instalei e executei os exemplos e avaliações documentados de GloVe, fastText, Word2Vec e um encoder MiniLM multilíngue. Resolvi a obtenção da base Rare Words e documentei a origem alternativa. Construí um piloto reproduzível de busca de animes com 39 títulos e 58 consultas, com dados congelados antes das predições. Para consultas em português e descrições inglesas, MiniLM teve nDCG@5 0,805 e um resultado fortemente relevante em primeiro em 47 de 58 consultas. Proponho usar esse encoder no protótipo do TCC. A comparação ampla, controlada e com anotação humana fica para a IC. Os números atuais são exploratórios, porque textos e julgamentos foram preparados com IA.”

Pedir orientação sobre a formulação do objetivo: busca semântica de animes por descrição ou recomendação personalizada? Confirmar a separação TCC/IC, a fonte das sinopses reais, critérios de avaliação humana e requisitos mínimos do protótipo. Não afirmar que o sistema final já está pronto.

## 12. Próximas entregas e desenho da IC

No TCC: fixar MiniLM como candidato inicial; coletar catálogo com sinopses inglesas reais e fonte registrada; definir tratamento de sinopses maiores que 128 tokens; criar índice persistido e função/API de busca; interface com consulta PT e resultados; documentar versão dos dados e encoder; avaliar utilidade com consultas reais e julgamento humano. Se a avaliação independente contradisser o piloto, reabrir a escolha explicitamente.

Na IC: hipótese prévia sobre busca multilíngue e formulação; catálogo maior e com casos difíceis; consultas escritas por pessoas sem acesso às descrições-alvo; pelo menos dois avaliadores cegos e protocolo de adjudicação; separação por intenção entre desenvolvimento e teste; teste final não usado para ajustar hiperparâmetros; corpora e orçamento controlados quando a pergunta for causal; estáticos alinhados e tradução como alternativas distintas; várias sementes no treino; comparação pareada por intenção e análise de erros/custo. Não escolher arquitetura e publicar desempenho final usando o mesmo pequeno conjunto de ajuste.

## 13. Reprodução e trilha de auditoria

Ler `../PROTOCOLO.md`, `../dados/freeze.json` e `../README.md`. Código completo em `../codigo/`: 01 treina Word2Vec text8; 02 cria e congela a base; 03 codifica cada pipeline sem ler relevâncias; 04 orquestra; 05 avalia; 06 gera estes relatórios. Os scripts de instalação e demos oficiais continuam em `../../scripts/`, com documentação em `../../docs/`.

Preservados: JSON agregado, CSV por consulta, CSV agregado, rankings completos, matrizes NumPy e metadados/recursos de cada execução. O painel HTML é offline e usa resultados prontos; não consulta um modelo ao selecionar opções. Não reexecutar o gerador de base sobre o congelamento. Novas avaliações devem usar uma nova versão, mantendo v1.

Reprodutibilidade não significa identidade bit a bit: os treinos multithread podem variar apesar da seed. Pesos treinados e seus hashes são a referência desta execução. As comparações usam corpora, dimensões e pré-treinamentos diferentes; avaliam a escolha de pipelines disponíveis, não o efeito isolado de um algoritmo.
