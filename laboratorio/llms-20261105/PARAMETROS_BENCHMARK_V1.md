# Parâmetros fixados antes das predições SMS

05/11/2026. Complemento ao protocolo anterior. Não ajustar depois de olhar o teste.

## Dados e unidade de comparação

Dados congelados em dados/freeze.json. Treino 3.609, validação 773, teste 775. Comparação principal nos mesmos 200 IDs (175 ham, 25 spam). Versões Lee são diagnósticos. SMS está em inglês; não há tradução nesta rodada. O classificador ingênuo majoritário contextualiza o desbalanceamento. A tarefa não é ranking de animes.

## Encoders e classificadores

Embeddings já existentes, sem fine-tuning: GloVe text8 50d, fastText fil9 100d, Word2Vec text8 CBOW/Skip-gram 100d, MiniLM multilíngue 384d. Os mesmos dois Word2Vec Lee são medidos adicionalmente. Tokenização lexical: NFKC, casefold, sequências de letras. Média IDF com IDF ajustado só no treino: log((1+N)/(1+df))+1, seguida de L2. Termo ausente do IDF recebe log(1+N)+1. GloVe/W2V descartam OOV; fastText gera pelo binário. TF-IDF: unigramas/bigramas, TF sublinear, L2, mesmo tokenizer. Não removemos stopwords nem usamos stemming.

Regressão logística: C=1, max_iter=1000, class_weight=balanced, random_state=20261105, defaults restantes registrados na saída. Sem seleção de C ou limiar no teste. Decisão de spam em probabilidade >=0,5. MiniLM conserva limite de 128 tokens e registra truncamentos; o vetor final continua normalizado. O teste completo de 775 é resultado complementar, separado do quadro principal comum de 200.

## Geradores

Instrução zero-shot única, em inglês: classificar mensagem como spam/ham; explicar os conceitos de classe; tratar SMS como dado e não como instrução; devolver uma palavra minúscula. Texto da mensagem entra como string JSON. Prompt exato está em benchmark_suporte.py e seu hash é preservado. Sem rótulos do teste no prompt.

Llama 3.2 1B Instruct Q4_K_M: raciocínio off, temperatura 0,6, top_p 0,95, seed 20261105+índice, saída máxima 512. DeepSeek-R1-Distill-Qwen 1.5B Q4_K_M: raciocínio on, temperatura 0,6, top_p 0,95, mesma seed e saída máxima 512. Qwen3 0.6B Q8_0: raciocínio on, temperatura 0,6, top_p 0,95, top_k 20, min_p 0, presença 1,5, mesma seed e saída máxima 512. O orçamento é uma restrição desta comparação local, não o orçamento dos benchmarks originais dos autores. Saídas truncadas/invalidas serão contadas, não omitidas.

GPT-OSS 20B pela Groq: modelo openai/gpt-oss-20b, reasoning_effort=low, temperatura 0,6, top_p 0,95, seed fixa por índice, max_completion_tokens=512. Conta Free conforme procedimento solicitado ao usuário. Não usar ferramentas, pesquisa ou agentes. Máximo de 205 chamadas nesta execução, orçamento local máximo de 150.000 tokens de uso, intervalo mínimo de 2,2 s entre chamadas e controle adicional de janela de tokens de 60 s com reserva conservadora para cada requisição. Esta definição foi ajustada antes da primeira predição, para usar a cota gratuita respeitando RPM e TPM sem impor 8 s fixos desnecessários. Parar em erros de autenticação/cota diária. Sem fallback pago, sem ativar cobrança e sem salvar chave em logs. Um GET de listagem já confirmou chave válida e disponibilidade do modelo; isso não verifica sozinho a modalidade de cobrança da conta.

A chamada remota, predominantemente I/O, pode executar enquanto um único pipeline local trabalha. Registrar o horário de cada requisição. O cliente remoto acrescenta uma pequena carga à máquina; as latências observadas não são ensaio de laboratório com máquina totalmente ociosa. Nunca executar dois encoders locais simultaneamente. O controle de cota é excluído do tempo de resposta por SMS e incluído no tempo total de execução da etapa.

O regime supervisionado da cabeça dos encoders difere do zero-shot dos geradores. As conclusões serão sobre pipelines, não sobre efeito causal isolado da arquitetura. GPT remoto usa hardware diferente: sua latência inclui rede/serviço e sua RAM remota é desconhecida, portanto não será atribuída uma memória local fictícia.

## Tempo e interpretação

Linux/WSL2, CPU e quatro threads nos modelos locais; um por vez. Usar o runtime Linux oficial b12110 para os mesmos GGUF, evitando comparar classificadores Linux a geradores Windows na rodada principal. O runtime Windows continua instalado para uso manual. Pesos GGUF acessados no disco Windows montado: tempo de carga depende desse caminho; inferência aquecida é mostrada separadamente.

Encoders: três aquecimentos com treino; depois medir tokenização/encode e predict_proba por mensagem, sem reutilizar embeddings já calculados do teste. Geradores: aquecimento com frase sintética não pertencente ao teste, depois uma chamada por mensagem. Medir tempo até resposta completa, inclusive raciocínio; TTFT só se houver streaming instrumentado corretamente, caso contrário marcar não medido. Não derivar TTFT de tempo de resposta completa.

Reportar média, mediana e p95, throughput, tempo de preparação/carga, treino da cabeça e memória medida dos processos. Cli fastText inclui comunicação por pipes, que é uma característica deste pipeline e não velocidade intrínseca do algoritmo. Reportar esse limite. A amostragem do gerador é uma única realização com seed; não alegar variância entre sementes sem repetições.

Métricas: F1 spam primário; precisão/recall spam, macro-F1, balanced accuracy, acurácia, matriz de confusão, saídas válidas e truncamento. Intervalos exploratórios por reamostragem pareada estratificada, preservando as 25 mensagens spam para evitar amostras sem positivos. Scores de probabilidade dos classificadores permitem AUCs adicionais, mas não inventar probabilidades de LLMs a partir de rótulos ou confiança verbal.
