# Métricas explicadas para leitura do comparativo

Este guia distingue classificação de SMS e busca/recomendação de anime. As fórmulas não tornam um julgamento de relevância automaticamente correto: qualidade dos rótulos, amostra e cenário continuam essenciais. Nenhuma métrica isolada escolhe o modelo final do TCC.

## 1. A matriz de confusão dos SMS

Chamamos spam de classe positiva e ham (mensagem legítima) de negativa.

- TP: spam identificado corretamente.
- FP: mensagem legítima acusada de spam. Pode bloquear uma conversa importante.
- FN: spam que não foi identificado. Pode deixar uma fraude passar.
- TN: mensagem legítima identificada corretamente.

Um LLM também pode não fornecer um rótulo utilizável. Guardamos a matriz com duas linhas de verdade (ham/spam) e três colunas de predição (ham/spam/inválida). Uma inválida nunca vira acerto e não é descartada. Para recall/F1 de uma classe, a inválida daquela classe conta como exemplo não recuperado. Para acurácia, é um erro. Isso evita favorecer um sistema por avaliar apenas suas respostas fáceis.

## 2. Acurácia, precisão, recall e F1

Acurácia = quantidade de rótulos corretos / quantidade total de mensagens, incluindo inválidas no denominador. Mede o acerto global. Com 175 ham e 25 spam, responder sempre ham dá 175/200 = 87,5%. Portanto esse número sozinho pode esconder a ausência de detecção de spam.

Precisão de spam = TP/(TP+FP). Pergunta: entre as mensagens que o sistema acusou de spam, quantas realmente eram spam? Útil quando um falso bloqueio é caro. Exemplo ilustrativo: 20 spams encontrados e cinco mensagens legítimas acusadas dão 20/25 = 80% de precisão. Sem predições de spam, registramos precisão zero, não omitimos o sistema.

Recall de spam = TP/(TP+FN), contando também spams com saída inválida entre os não encontrados. Pergunta: de todos os spams existentes, quantos encontramos? Útil quando deixar uma fraude passar é caro. Se existiam 25 spams e encontramos 20, recall = 80%.

F1 de spam = 2*precisão*recall/(precisão+recall) = 2TP/(2TP+FP+FN). É a média harmônica: penaliza um desempenho muito baixo em uma das duas dimensões. Nesta fórmula FN inclui spams inválidos. É a métrica principal dos SMS, mas não distingue sozinha se os erros foram falsos bloqueios ou spams perdidos. Registramos zero se o denominador é zero.

Macro-F1 = (F1_ham + F1_spam)/2. Dá o mesmo peso às duas classes, apesar do número diferente de mensagens. Não confundir com calcular F1 usando as médias de precisão e recall. Balanced accuracy = (recall_ham + recall_spam)/2. Também dá peso igual às classes, mas considera recall, não precisão.

## 3. Probabilidades, ROC-AUC, AP e Brier

Uma regressão logística fornece um score probabilístico de spam. O limiar fixado nesta rodada é 0,5. Um gerador que respondeu apenas ham/spam não forneceu essa distribuição de scores; não inventamos probabilidades para ele. Similaridade de vetores tampouco é probabilidade de um usuário gostar de um anime.

ROC-AUC: probabilidade de um spam escolhido aleatoriamente receber score maior que um ham escolhido aleatoriamente; um empate contribui metade. Equivale à área sob a curva de taxa de positivos verdadeiros versus taxa de falsos positivos quando variamos o limiar. Quanto maior, melhor; 0,5 corresponde ao comportamento sem discriminação nessa interpretação. Avalia ordenação, não o acerto com limiar 0,5, e pode esconder dificuldades práticas com a classe rara.

Average precision (AP) = soma, ao longo dos limiares, de (recall_n - recall_anterior)*precisão_n. Resume a recuperação de positivos com seus scores e é útil para classes raras. Maior é melhor. AP não é idêntica à integração trapezoidal da curva precisão-recall. Reportamos o nome exato para permitir reprodução.

Brier = média de (p_spam - y)^2, com y=1 para spam e 0 para ham. Menor é melhor; zero significa probabilidades exatamente corretas nos exemplos observados. Uma previsão p=0,9 para uma mensagem legítima produz erro quadrático 0,81, muito maior que p=0,1 (0,01). Mede qualidade probabilística, combinando discriminação e calibração. Não mede somente calibração. A cabeça usa class_weight=balanced: seu score não deve ser tratado como frequência real calibrada sem avaliação adicional.

## 4. Custos operacionais hipotéticos

No cenário de custos iguais: FP + FN + inválidas. Para proteger mensagens legítimas: 5*FP + FN + 5*inválidas. Para priorizar detecção de spam: FP + 5*FN + 5*inválidas. Aqui FN designa a predição ham para um spam; inválidas são cobradas separadamente uma única vez. Uma inválida recebe conservadoramente o maior peso de erro do cenário.

Menor custo é melhor sob aquelas suposições. As unidades não são reais, dinheiro ou custos medidos com usuários. Mudamos apenas a interpretação dos erros existentes, não o limiar ou as predições. São análises exploratórias pós-hoc, úteis para discutir requisitos. Não podemos escolher depois o custo que faz nosso modelo favorito vencer e tratá-lo como hipótese prévia confirmada.

## 5. Relevância dos animes e limites do teste

O catálogo contém 1.000 sinopses. Cada consulta tem preferências de gêneros e, às vezes, uma exclusão. A referência automática usa os gêneros do publicador: grau 2 satisfaz todos os gêneros pedidos e nenhuma exclusão; grau 1 satisfaz parte dos pedidos sem violar exclusão; grau 0 não satisfaz ou viola uma exclusão. Os gêneros não entram nos textos dos modelos; servem para avaliar.

Esses rótulos são uma aproximação controlada de aderência a gêneros, não avaliações humanas de gosto, enredo ou qualidade. Uma taxonomia incompleta pode penalizar uma recomendação plausível. As consultas foram preparadas com assistência de IA antes dos rankings; não representam uma amostra independente de usuários. Esta fase ajuda a testar o sistema; o trabalho acadêmico final precisará de julgamentos humanos e/ou dados de preferência adequados à pergunta científica.

## 6. nDCG@5: qualidade da ordem dos primeiros resultados

Para uma lista de até cinco itens, DCG@5 = soma de (2^grau_i - 1)/log2(i+1), com a posição i começando em 1. Os ganhos dos graus 0, 1 e 2 são 0, 1 e 3. A divisão por log2(i+1) reduz a contribuição de resultados mais distantes do topo. nDCG@5 = DCG@5 / IDCG@5, onde IDCG é o DCG da melhor ordenação possível na coleção de referência. Maior é melhor; 1 representa uma ordenação ideal segundo esses rótulos. Se o ideal tem ganho zero, registramos zero e contamos esse caso.

Exemplo meramente didático de três itens: graus [2,1,0] produzem DCG = 3 + 1/log2(3), aproximadamente 3,631. A ordem [1,2,0] produz 1 + 3/log2(3), aproximadamente 2,893; nDCG aproximadamente 0,797 quando [2,1,0] é o ideal. Há itens relevantes nas duas listas, mas a melhor recomendação apareceu mais cedo na primeira.

Na recuperação completa, o ideal considera o catálogo inteiro. Na reordenação de cinco candidatos, a métrica principal usa o ideal dentro desses mesmos cinco, para isolar a ordenação. Também guardamos nDCG em relação ao ideal global. Não misturamos essas normalizações numa única tabela: um reranker pode ordenar perfeitamente uma lista que deixou bons títulos fora.

## 7. Hit@1, Precision@3, Recall@10 e MRR

Hit@1 = média, entre consultas, de 1 se o primeiro item é grau 2 e 0 caso contrário. Mede a chance de a primeira sugestão atender completamente ao pedido segundo a referência. Uma sugestão parcialmente relevante não conta como hit, embora receba ganho no nDCG.

Precision@3 = quantidade de itens grau 2 nas três primeiras posições / 3, depois média entre consultas. Mede a concentração de boas sugestões no começo da lista. É precisão de ranking, diferente da precisão do classificador de spam.

Recall@10 = quantidade de itens grau 2 recuperados nos dez primeiros / quantidade de itens grau 2 existentes no catálogo, depois média entre consultas. É útil para medir quantos candidatos relevantes a recuperação consegue alcançar. Em um gênero amplo com centenas de títulos relevantes, recall@10 será baixo mesmo com dez boas sugestões. Por isso deve ser lido junto com Precision e nDCG, não como uma nota isolada de satisfação.

MRR@k = média de 1/r, onde r é a posição do primeiro item grau 2 dentro dos k primeiros. Se não houver, vale zero. Se a primeira boa sugestão está em primeiro lugar, contribui 1; em segundo, 0,5; em quinto, 0,2. Usamos MRR@10 na recuperação completa e MRR@5 na lista curta. Mede rapidez para encontrar a primeira boa opção, mas não avalia a qualidade dos demais itens da lista.

## 8. Limite da lista de candidatos e falhas

Todos os rerankers recebem os mesmos cinco candidatos selecionados por TF-IDF, em uma ordem de entrada permutada previamente. Eles não podem devolver um anime que não entrou nessa lista. O recall do conjunto de cinco é invariável sob uma permutação válida: a reordenação melhora posições, não recupera itens novos. Reportamos o limite de qualidade atingível e a quantidade de listas sem ganho positivo.

Uma permutação válida contém exatamente A, B, C, D e E uma vez cada. Saída incompleta, repetida, inexistente ou explicação sem JSON válido é inválida. O resultado bruto recebe qualidade zero; não escolhemos trechos favoráveis do raciocínio. Um pipeline adicional, identificado como fallback, usa a ordem TF-IDF nesses casos e informa quantas vezes precisou fazer isso. Seu resultado não é apresentado como acerto do LLM.

Nas consultas com exclusão, verificamos se o primeiro item tem um gênero proibido nos metadados. Uma saída inválida não constitui recomendação segura: a taxa conservadora de falha de restrição conta também essas inválidas. Essa medida só é interpretável no subconjunto com restrições, e o número de casos é pequeno. Taxa de respostas válidas = saídas no formato solicitado / consultas; mais alta é melhor para integração. Encerramento por limite de tokens é diagnóstico: pode explicar uma resposta incompleta, mas não a transforma em acerto.

## 9. Cobertura e diversidade: diagnósticos de recomendação

Cobertura do catálogo@5 = quantidade de títulos diferentes recomendados entre os cinco primeiros de todas as consultas / tamanho do catálogo. Mostra se as listas ficam concentradas em poucos títulos. Não prova que os títulos adicionais são bons. Aqui existem apenas 24 consultas e 1.000 títulos: o máximo observável seria 120 títulos diferentes, isto é, 12% de cobertura. As consultas correlacionadas também reduzem esse valor. Não comparar com outro estudo que usa número diferente de consultas sem considerar esse limite.

Diversidade de gêneros@5: para cada par de itens da lista, calcular distância Jaccard = 1 - |gêneros_A interseção gêneros_B|/|gêneros_A união gêneros_B|; tirar a média dos pares e depois das listas válidas. Mais alto indica listas com gêneros mais diferentes. Isso não é automaticamente melhor: um pedido específico pode desejar sugestões semelhantes. Só usamos metadados após o ranking para descrever o resultado. Listas inválidas não recebem diversidade inventada; sua taxa de falhas aparece separadamente.

Nos diagnósticos de listas exibidas, empates usam ID fixo, enquanto métricas principais calculam a expectativa sob permutações uniformes dos empatados. Isso evita favorecer a qualidade de um modelo sem informação. O baseline aleatório representa essa expectativa de scores empatados; não atribuímos a ele uma cobertura arbitrária de IDs.

## 10. Tempo, memória e armazenamento

Preparação/indexação: carregar pesos, construir o índice e codificar o catálogo; ocorre antes das consultas. Seu custo pode ser amortizado por muitas recomendações. No SMS também há codificação do treino e ajuste da cabeça logística, registrados separadamente do treinamento histórico dos embeddings.

Latência por consulta: tempo observado para gerar a decisão/resposta completa. Nos encoders, inclui transformar a consulta em vetor e calcular os scores. Nos geradores, inclui processamento do prompt, raciocínio e resposta final. Média = soma dos tempos/N; mediana é o valor central; p95 é o percentil amostral de 95%, calculado com interpolação do NumPy. P95 é útil para observar a cauda de respostas demoradas, mas não é uma garantia de SLA e é instável com só 24 consultas.

No pipeline com reranker, tempo operacional estimado por consulta = recuperação TF-IDF medida + resposta do reranker medida. É uma composição de medições, não teste de serviço concorrente em produção. Os retrievers no catálogo completo têm o tempo real de sua busca completa; não fingimos que medimos separadamente somente cinco scores. Não inferimos TTFT (tempo até primeiro token) da latência total: sem streaming instrumentado, TTFT não foi medido.

Throughput serial = 1/latência média em segundos, quando aplicável. Não é vazão de múltiplos usuários em paralelo. Groq inclui rede e serviço em hardware remoto desconhecido. Pausas preventivas por cota aparecem no tempo total da etapa, mas não na latência individual de resposta. Esperas de retry são preservadas. Diferenças de hardware impedem atribuir tudo ao modelo.

RSS é memória residente de processo. KiB/1.024 dá MiB. GNU time registra o maior processo da execução; isso captura o CLI fastText, mas não soma toda a máquina. Para geradores locais lemos o pico do servidor e registramos o cliente separadamente. A RAM remota Groq é desconhecida, não zero. Tamanho de arquivo no disco é outro conceito e não substitui RSS. Gratuidade de API não significa ausência de consumo elétrico ou de recursos locais; energia não foi medida nesta rodada.

## 11. Cobertura lexical, truncamento e incerteza

Cobertura lexical = tokens com entrada exata no vocabulário / tokens consultados. GloVe/Word2Vec sem entrada descartam a palavra; fastText pode compor uma representação por subpalavras. Ter vetor para um termo raro não prova que seu significado foi aprendido. Consulta com scores todos zero é um diagnóstico de ausência de discriminação, não prova isolada de qual componente falhou.

Truncamento: quantidade de textos que ultrapassam o limite de tokens do encoder. Todos os modelos recebem o mesmo trecho de até 80 palavras, mas tokenizadores diferentes geram números diferentes de tokens. MiniLM conserva limite 128 e os excessos são contados. Nos LLMs verificamos os prompts renderizados e reservamos 512 tokens de saída dentro do contexto 2.048 antes de prever, sem cortar candidatos de modo desigual.

Intervalos de 95% por bootstrap são obtidos reamostrando os exemplos/unidades e recalculando a métrica 5.000 vezes, com seed 20261105; usamos os percentis 2,5 e 97,5. Nos SMS preservamos 175 ham e 25 spam. Em anime reamostramos as 12 famílias de intenção, mantendo juntas formulação literal e paráfrase. Reutilizamos as mesmas amostras entre modelos para diferenças pareadas.

Esses intervalos descrevem incerteza condicional à amostra e aos modelos fixos. Não incluem erro dos rótulos, autoria das consultas, novos corpora, novos usuários, hardware, sementes ou treinamento. Um intervalo que cruza zero não prova equivalência. Procurar o melhor modelo em vários testes também exige cuidado com seleção; as recomendações desta fase são exploratórias, não uma confirmação científica final.

## 12. Spearman rho - somente referência histórica Rare Words

Spearman rho compara a ordem das similaridades calculadas pelo modelo com a ordem das notas humanas para pares de palavras. Calculamos a correlação de Pearson entre os ranks: rho = covariância(R_modelo, R_humano)/(desvio_R_modelo * desvio_R_humano), usando ranks médios para empates. Varia entre -1 e 1: 1 indica a mesma ordem, 0 ausência de associação monotônica medida e -1 ordem inversa. Valores maiores e positivos são desejáveis nessa avaliação. Não é porcentagem de acerto. O resultado histórico fastText RW foi 0,4177019229655776 em 2.034 pares; não deve ser misturado com F1 dos SMS ou nDCG dos animes. O teste RW foi concluído em 29/10/2026 e apenas citado nesta consolidação.
