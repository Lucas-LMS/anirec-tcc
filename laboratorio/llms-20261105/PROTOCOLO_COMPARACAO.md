# Protocolo inicial para comparação gratuita de classificação de SMS

Registrado em 05/11/2026 antes de observar desempenho de classificação. Esta fase prepara instalação e testes funcionais. A avaliação comparativa completa depende de retomar os modelos estáticos no WSL.

## Pergunta e limites

Comparar pipelines disponíveis para classificar mensagens inglesas como spam ou legítimas, em uma base básica rotulada. Usar os mesmos IDs de teste e medir qualidade e recursos. Este experimento não substitui a avaliação de busca multilíngue de animes do TCC, cujo modelo final permanece estático. Não foi alterada essa restrição.

## Dataset sugerido e adquirido

[SMS Spam Collection no Kaggle](https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset), referência `uciml/sms-spam-collection-dataset`. Arquivo público baixado diretamente da API de datasets Kaggle, sem chave e sem pagamento. Metadados apontam para a coleção de Almeida, Hidalgo e Yamakami, originalmente usada em filtragem de spam. [Fonte acadêmica UCI](https://archive.ics.uci.edu/dataset/228/sms+spam+collection).

O Kaggle e a UCI anunciam aproximadamente 5,5 mil exemplos; relatar a quantidade observada no CSV, sem assumir que todas as distribuições têm exatamente o mesmo número. As classes já existem na fonte. O conteúdo é inglês e curto, favorecendo experimentos locais menores. O desbalanceamento torna acurácia isolada insuficiente. Dataset público antigo pode estar no pré-treino de LLMs: não temos como demonstrar ausência de contaminação.

Procedimento: preservar ZIP/CSV bruto; usar apenas `v1` como rótulo e `v2` como texto; verificar ausências/classes; agrupar textos por NFKC/casefold/whitespace; remover duplicatas antes da separação e excluir grupos conflitantes, se houver. Para inferência, preservar o texto original, sem trocar todos os textos pela versão normalizada usada para deduplicar.

Separação estratificada determinística aproximada 70% treino, 15% validação, 15% teste, seed 20261105, hashes congelados. Criar também subconjunto comum estratificado de até 200 mensagens dentro do teste, para tornar a primeira rodada de todos os LLMs viável em CPU. Não escolher essas mensagens depois de ver previsões. O resultado principal inicial compara TODOS os pipelines nesse mesmo subconjunto. Os resultados dos estáticos no teste completo são adicionais e não devem aparecer na mesma tabela como se usassem o mesmo denominador.

## Sistemas

- Classificador ingênuo que sempre prevê a classe majoritária do treino, para contextualizar a acurácia em dados desbalanceados.
- TF-IDF + regressão logística, como controle lexical.
- GloVe, fastText e Word2Vec CBOW/Skip-gram já treinados: representação de SMS por média IDF e regressão logística. Ajustar vocabulário/IDF e classificador somente no treino; parâmetros predefinidos inicialmente: C=1, max_iter=1000, class_weight=balanced e seed fixa. Não retreinar os embeddings no teste.
- MiniLM congelado + regressão logística, como encoder contextual. Medir/registrar truncamento se houver; nenhuma alteração silenciosa de limite após resultados. Treinar a cabeça só no treino.
- Llama 3.2 1B Instruct Q4_K_M, DeepSeek-R1-Distill-Qwen-1.5B Q4_K_M e Qwen3-0.6B Q8_0 como classificadores por instrução, com saída final `ham` ou `spam`. Quantizações/tamanhos diferentes serão declarados.
- Word2Vec Lee pode aparecer como diagnóstico, não como único representante da família. O classificador cooking não é candidato para SMS, pois aprende rótulos de outra tarefa. Um fastText supervisionado treinado em SMS seria uma configuração adicional distinta, se incluído.

Os estáticos/encoder recebem treino supervisionado da cabeça classificadora, enquanto LLMs recebem instrução zero-shot ou exemplos de contexto. São pipelines com regimes de supervisão diferentes, não uma comparação causal de arquiteturas. Se houver few-shot, fixar exemplos extraídos somente do treino, com mesmo conjunto/ordem entre geradores, e reportar como outra condição. Não usar rótulos de teste no prompt nem ajustar no teste.

Prompt inicial em inglês, pois o CSV é inglês. O texto da mensagem é dado a classificar, não uma instrução a ser obedecida. Fixar template e instrução antes do teste. Respostas inválidas, truncadas, recusas e timeouts contam como falhas, não podem ser descartadas para melhorar os números. DeepSeek tem orientação de raciocínio e pode necessitar orçamento maior de saída; seguir documentação e relatar esse custo. Não impor temperatura zero indiscriminadamente se o fabricante recomenda amostragem diferente. Separar testes de instalação de resultados de acurácia.

## Métricas adequadas

Primária proposta: F1 da classe spam. Complementares: precisão/recall spam, macro-F1, balanced accuracy, acurácia e matriz de confusão com contagens, além de taxa de resposta válida. Reportar denominadores e intervalo exploratório por bootstrap pareado das mesmas mensagens. Ausência de diferença significativa não prova equivalência. Não ajustar limiar ou prompts no teste.

ROC-AUC, PR-AUC, Brier e calibração só quando existir um score/probabilidade comparável bem definido. Um gerador que devolve somente `spam`/`ham` não fornece automaticamente uma probabilidade calibrada; não inventar números nem usar sua confiança declarada como equivalência. nDCG@k e Recall@k de busca não são métricas principais adequadas a classificação binária.

## Tempo memória e custo

Um modelo por vez, quatro threads inicialmente, mesma máquina; processos separados para medir recursos. Medir carregamento e primeira chamada separados da inferência aquecida. Após aquecimento, medir por mensagem sem batching na condição comum e reportar mediana, p95, média e throughput. Se houver lote, apresentar outra condição e registrar tamanho.

Registrar tempo de treino da cabeça, indexação/codificação inicial, tempo de consulta/inferência, RAM residente observada e tamanho em disco. Para geradores, TTFT e tokens/s são diagnósticos adicionais, não uma métrica comum a Word2Vec. Pico de working set Windows e RSS Linux têm diferenças de ambiente; declarar plataforma ou executar todos num mesmo ambiente após retomar WSL. Não chamar dois cronômetros diferentes de igualdade de hardware/configuração.

Modelos locais não cobram tokens/API, mas consomem energia, armazenamento e processamento. Não será usado serviço pago, cartão ou crédito promocional. Nenhum benchmark completo deve ser declarado concluído antes de registrar todas as predições e verificar os arquivos.
