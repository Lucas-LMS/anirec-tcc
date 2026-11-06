# Modelos estáticos no TCC e LLMs como comparadores

Registro: 29/10/2026. Consulta a fontes oficiais nesta data. Este documento atualiza a decisão de escopo após esclarecimento de Lucas: **o sistema final do TCC usará representações estáticas**. Os resultados numéricos do piloto não mudaram.

## Correção da recomendação anterior

O MiniLM venceu o piloto PT → EN entre os pipelines avaliados, mas **não é um modelo de embeddings estáticos**: usa um Transformer para construir representações dependentes do texto. Mantê-lo como comparador moderno, não como encoder final do TCC. O PDF anterior registra a recomendação operacional antes desse esclarecimento e deve ser lido junto desta atualização. Ainda não há um modelo estático vencedor estabelecido para a configuração multilíngue final.

“Estático” aqui significa representação lexical não contextual: o vetor de uma palavra não muda conforme a frase. Fixar os pesos de um Transformer ou salvar seus embeddings não o torna um modelo estático nesse sentido. fastText usa subpalavras para compor representações lexicais, mas continua não contextual nesse uso. TF-IDF/BM25 são baselines lexicais, não modelos de word embeddings da mesma família.

## GPT: viável por API, sem exigir GPU local

Para um GPT servido pela OpenAI, a aplicação envia textos e recebe respostas por HTTP; o processamento pesado ocorre no servidor. A dificuldade local passa a ser integração, gestão de credenciais, orçamento, limites, repetição e auditoria das respostas, não carregar os pesos. Não tratar os GPTs proprietários da API como pacotes de pesos disponíveis para instalar localmente. Modelos de pesos abertos, inclusive de outras famílias, são uma alternativa distinta.

Na consulta oficial atual, GPT-5 Mini e GPT-4.1 Mini aparecem como deprecated; não são a primeira escolha para começar uma integração nova. A documentação de GPT-5 Mini direciona novos casos de baixa latência/alto volume para **GPT-5.6 Terra**, apresentado como equilíbrio entre inteligência e custo. Disponibilidade efetiva depende da conta e deve ser verificada antes de executar. [Modelo e documentação oficial](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [estado do GPT-5 Mini](https://developers.openai.com/api/docs/models/gpt-5-mini).

GPT pode ser comparador forte ao receber consulta + descrições + IDs e devolver somente IDs ordenados. Não precisa integrar o produto final. Por outro lado, requer rede, cobrança por uso, controle de prompt e tratamento de saídas inválidas; o fornecedor pode atualizar ou retirar versões. Salvar requisições sem segredos, respostas, modelo retornado, data, parâmetros, uso de tokens e falhas.

## Llama: família com tamanhos muito diferentes

**Llama 3.2 1B Instruct** é um candidato local pequeno; **3B Instruct** é uma expansão possível após medir o primeiro. Português é oficialmente suportado na família 3.2. Seguir cartão oficial, licença e requisitos de acesso aos pesos. [Cartão oficial Meta](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct).

Inferência em CPU com pesos quantizados é plausível nesta máquina, mas ainda não executada. Não afirmar velocidade nem consumo total antes de medir. `llama.cpp` documenta execução local, quantização e backends; sua documentação é oficial da ferramenta, não certificação da Meta para este hardware. [Runtime oficial](https://github.com/ggml-org/llama.cpp).

Llama também pode ser consumido por API hospedada: por exemplo, Amazon Bedrock documenta chamadas a modelos Meta Llama. Conta, região, modelo específico e permissões precisam ser conferidos. É uma API do provedor de hospedagem, não assumir que todo Llama usa um endpoint público único da Meta. [Documentação AWS](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-meta.html).

Vantagens locais: controlar pesos e versão, funcionar offline e medir recursos sem custo por chamada. Limitações: geração sequencial em CPU, janela de contexto/KV cache, instalação, quantização e qualidade menor possível nas versões pequenas. Um Llama 1B não representa a capacidade de toda a família ou de modelos maiores.

## DeepSeek: separar modelo completo, destilado e API

O **DeepSeek-R1 completo** possui 671 bilhões de parâmetros totais e 37 bilhões ativos por token segundo seu cartão. O número ativo não transforma o conjunto de pesos num modelo de 37B para armazenamento. Mesmo uma conta idealizada de 4 bits por parâmetro dá cerca de 335,5 GB somente para pesos, sem metadados, runtime ou cache. Não é um candidato prático local nesta máquina. Não generalizar essa conta para toda a família DeepSeek.

O **DeepSeek-R1-Distill-Qwen-1.5B** é um modelo pequeno derivado de Qwen, destilado com dados do R1. É candidato local plausível, diferente do R1 completo. Sua orientação para raciocínio e possíveis saídas longas podem acrescentar tempo desnecessário a uma busca temática. Isso é motivo para não priorizá-lo, não evidência de pior qualidade em animes. [Cartão e instruções oficiais](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B).

A API oficial está disponível e usa formato compatível com OpenAI/Anthropic. Na data consultada, **deepseek-flash** aponta para DeepSeek-V4.1-Flash-1017; o fornecedor também lista deepseek-v4-pro. O modelo servido pela API **não é** o destilado 1.5B local nem necessariamente o R1 histórico. Identificar corretamente no experimento. [Primeira chamada](https://api-docs.deepseek.com/quick_start/pricing), [modelos e preços](https://api-docs.deepseek.com/quick_start/pricing/).

É uma boa opção inicial de API para limitar custo de instalação local. Ainda exige chave/conta, orçamento, rede, registro de versão e checagem de saídas. Não fizemos chamadas pagas nem testamos acesso de conta nesta etapa.

Exemplo exclusivamente orçamentário: 58 chamadas com 10.000 tokens de entrada e 200 de saída cada totalizariam 580.000 de entrada e 11.600 de saída. Às tarifas oficiais consultadas, GPT-5.6 Terra (US$ 2/M entrada; US$ 12/M saída) resultaria em aproximadamente **US$ 1,30**. DeepSeek Flash em horário peak, sem cache (US$ 0,30/M entrada; US$ 1,20/M saída), em aproximadamente **US$ 0,19**. Não é orçamento garantido nem consumo medido: excluir desta conta raciocínio adicional, repetição, ajustes, falhas, impostos, câmbio e qualquer ferramenta extra pode subestimar o gasto real. O consumo deve ser calculado novamente com os textos/prompt finais. Tarifas e disponibilidade podem mudar; fontes de cada valor estão nos links oficiais acima.

## Estimativa de memória: não confundir pesos com RAM total

Conta didática para modelo denso: número de parâmetros × bits / 8. Valores decimais, não GiB, sem overhead. Quantização tem escalas/metadados e pode deixar partes em precisão maior. Contexto, cache, buffers, bibliotecas e processos do sistema aumentam a memória real.

| Parâmetros nominais | Pesos FP16 ideais | Pesos 4-bit ideais |
|---|---:|---:|
| 0,6B | 1,2 GB | 0,30 GB |
| 1B | 2,0 GB | 0,50 GB |
| 1,5B | 3,0 GB | 0,75 GB |
| 3B | 6,0 GB | 1,50 GB |
| 7B | 14,0 GB | 3,50 GB |

A máquina tem Ryzen 5 2400G, aproximadamente 13,9 GiB utilizáveis no Windows e 6,7 GiB no WSL observado, sem backend GPU validado. Começar por 0,6B–1,5B, contexto curto e saídas limitadas é uma estimativa de viabilidade, não um teste concluído. Modelos 7B quantizados podem caber sob algumas configurações, mas a folga de memória e velocidade em CPU exigem medição; não são a opção inicial mais confortável.

## Qual modelo estático priorizar

**Primeiro candidato: fastText com vetores PT/EN alinhados oficialmente.** O recurso oficial disponibiliza vetores de 44 idiomas, incluindo português e inglês, alinhados por RCSLS. Diferentemente do fastText inglês do piloto, possibilita comparar os idiomas em um espaço compatível. Isso oferece uma hipótese tecnicamente pertinente, sem garantir a vitória. [Vetores alinhados oficiais](https://fasttext.cc/docs/en/aligned-vectors.html).

Desenho: vetorizar consulta PT com a tabela PT; descrição EN com a tabela EN correspondente; aplicar agregação predefinida e cosseno. Usar o par alinhado do mesmo recurso, não misturar a tabela PT alinhada com nosso fil9 inglês independente. Pesos IDF precisam de definição consistente por idioma ou comparação explícita com média simples; não ajustar no teste final.

**Cuidado:** o download `.vec` é uma tabela de vetores, não um `.bin` com todos os parâmetros de subpalavras. Não herda automaticamente a capacidade do nosso binário fastText de produzir qualquer palavra fora do vocabulário. Medir e documentar OOV. Para usar composição de subpalavras em outro espaço, seria necessário um procedimento de projeção/alinhamento compatível adicional.

Segundo caminho: Word2Vec Skip-gram e GloVe pré-treinados em corpora adequados, com tradução fixa de consultas PT → EN ou tradução offline do catálogo EN → PT. Se a tradução vier de LLM, o sistema é híbrido; não atribuir o resultado somente ao modelo estático. Se o requisito excluir LLMs até do pré-processamento, preferir alinhamento de vetores ou outra solução permitida.

**Wang2Vec** é uma expansão estática interessante para a IC por incorporar informação de ordem no contexto de treinamento. Não torna a representação de frases automaticamente sensível à ordem se depois fizermos uma média dos vetores, nem resolve o alinhamento de idiomas. O trabalho do NILC fornece referência de Word2Vec, GloVe, fastText e Wang2Vec em português. [Projeto dos autores](https://github.com/nathanshartmann/portuguese_word_embeddings), [artigo original](https://arxiv.org/abs/1708.06025). O endereço antigo do portal NILC não foi acessível nesta consulta; o repositório dos autores aponta para a coleção de pesos atual.

Não priorizar Doc2Vec agora: muda a unidade e o procedimento de inferência, demanda corpus adequado e não resolve PT/EN sozinho. Pode ser um comparador clássico adicional se houver pergunta de pesquisa específica. Não precisamos instalar muitas famílias antes de resolver idioma e agregação das famílias já disponíveis.

## Comparadores modernos sugeridos

1. **MiniLM multilíngue:** já instalado, local, comparação contextual de baixo esforço adicional. Não é estático e não é um gerador de respostas.
2. **Qwen3-0.6B:** primeiro candidato gerador local, pequeno. Seu cartão permite modo sem thinking; testar com limite de saída e contexto, seguindo parâmetros recomendados em vez de impor temperature=0 a todos. Não representa a fronteira de qualidade dos LLMs. [Cartão oficial](https://huggingface.co/Qwen/Qwen3-0.6B).
3. **Llama 3.2 1B Instruct:** alternativa pequena para incluir a família Meta, com suporte oficial ao português.
4. **DeepSeek Flash por API:** comparador hospedado inicial. GPT-5.6 Terra pode ser uma segunda API para verificar se a conclusão depende do fornecedor, se o orçamento justificar.
5. **Qwen3-Embedding-0.6B:** opção moderna especializada em embeddings, mais diretamente comparável à recuperação vetorial que um chatbot. É contextual, distinto de Qwen3-0.6B gerador. Há suporte multilíngue e instruções específicas; capacidade local e tempo ainda não medidos. [Cartão oficial](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).
6. **text-embedding-3-small:** opção de embeddings por API; não chamar de “GPT gerador”. Documentação consultada lista US$ 0,02 por milhão de tokens de entrada, antes de outras condições aplicáveis. Boa referência hospedada para similaridade, mas acrescenta custo/rede e outra classe de comparação. [Modelo oficial](https://developers.openai.com/api/docs/models/text-embedding-3-small).

Não começar com todas essas opções: fastText alinhado + MiniLM já instalado + um gerador pequeno local + uma API são suficientes para um primeiro desenho.

## Como testar a hipótese sem forçar o resultado

Pergunta sugerida: **em busca temática de animes com consultas portuguesas e descrições inglesas, um pipeline estático alinhado oferece qualidade competitiva a representações contextuais e a um LLM, com menor custo e latência?**

Fixar a tarefa de devolver IDs ordenados do catálogo. Um texto convincente sobre animes não é uma métrica de recuperação. Separar três comparações:

- Recuperação vetorial: estáticos alinhados contra encoders contextuais, mesmo catálogo e mesmas consultas.
- Ranking por gerador: fornecer descrições e IDs aos LLMs, exigir IDs válidos, comparar com os mesmos julgamentos. Em catálogo pequeno, todos podem receber todos os candidatos se couberem; medir o custo desse contexto.
- Pipeline híbrido: quando um recuperador gera shortlist e LLM reordena, relatar o recuperador e seu Recall@k. O LLM não consegue recuperar um alvo que nunca recebeu. Para isolar reranking, fornecer a mesma shortlist a todos os rerankers; medir também o desempenho de ponta a ponta.

Evitar o vazamento de conhecimento: descrição e ID bastam para o teste principal de conteúdo; títulos podem permitir que um gerador use conhecimento memorizado de animes famosos. Se títulos forem usados como parte do produto, fazer condição separada e declarar a diferença. Aleatorizar ou contrabalancear ordem dos candidatos para testar viés de posição; contabilizar o custo adicional.

Consultas e julgamentos humanos cegos aos sistemas; divisão por intenção entre desenvolvimento e teste; prompts e hiperparâmetros ajustados só em desenvolvimento; nenhum ajuste retrospectivo para favorecer o estático. Não usar o LLM participante como único juiz da sua própria qualidade. Registrar IDs inválidos, respostas incompletas, recusas e falhas de API, sem simplesmente descartá-las.

Medir nDCG@5, Recall@5, Hit@1 e MRR, além de latência real por consulta com catálogo pré-indexado, memória observada, custo por 1.000 consultas e custo inicial de indexação. API usa hardware remoto desconhecido: comparar latência/custo do serviço, não fingir igualdade de hardware com a CPU local. Repetir inferência estocástica conforme documentação, guardando variância.

Se quisermos afirmar **equivalência/não inferioridade**, predefinir margem prática e calcular intervalo da diferença; ausência de significância não prova igualdade. Uma margem ilustrativa de 0,03 nDCG precisaria de justificativa e aprovação metodológica, não deve ser adotada só porque favorece resultados. Também é válido concluir que o estático tem qualidade um pouco menor, mas atende ao requisito com custo e dependências menores.

Não afirmar agora que um estático supera LLMs: nenhum gerador foi avaliado e nosso piloto favoreceu MiniLM no cenário multilíngue. A hipótese permanece aberta. Mesmo se o gerador vencer, a decisão de usar estático no TCC pode se apoiar no objetivo pedagógico/científico, processamento local, orçamento e requisitos mínimos explicitados.

## Ordem proposta para a continuação

1. Obter e verificar o par fastText alinhado PT/EN, preservando origem, licença, hashes, cobertura e versão; repetir o piloto como **nova versão**.
2. Construir conjunto com sinopses reais e consultas/julgamentos humanos, mantendo teste independente.
3. Instalar um gerador pequeno (Qwen3-0.6B ou Llama 3.2 1B), medir consumo/latência e executar o protocolo de ranking.
4. Executar uma API com orçamento predefinido e credenciais configuradas, preservando logs sem segredos.
5. Selecionar o estático final pela avaliação apropriada; manter comparação moderna na IC ou como justificativa delimitada no TCC.

Nesta etapa houve pesquisa documental e atualização de escopo. **Não instalamos novos modelos, não baixamos pesos e não fizemos chamadas pagas.**
