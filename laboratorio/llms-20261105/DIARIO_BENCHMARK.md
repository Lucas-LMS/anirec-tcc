# Diário adicional - benchmark de 05/11/2026

## Ambiente recuperado

Após ativar virtualização no firmware e reiniciar, Ubuntu/WSL2 voltou sem reinstalação. Pesos e ambientes anteriores foram preservados. O benchmark usa CPU Ryzen 5 2400G, quatro threads, um pipeline local por vez. O cliente HTTP da Groq executa simultaneamente e acrescenta pequena carga; isso limita a interpretação dos tempos como ensaio de máquina ociosa.

Para uniformizar o sistema dos pipelines, foi baixado o runtime oficial Linux do llama.cpp b12110: https://github.com/ggml-org/llama.cpp/releases/download/b12110/llama-b12110-bin-ubuntu-x64.tar.gz . SHA-256: `368227edcc229be5f9bed16a2223d79b5e41d0ac2e19bcf5825e82291c060e55`. Extração em `/home/lucas/tcc-lab/LLMs/runtime-b12110/llama-b12110`. Os mesmos GGUF continuam no Windows, acessados por `/mnt/c/tcc-lab/LLMs/models`. O runtime Windows anterior continua disponível.

## Dependências adicionadas

- Ambiente Word2Vec Python 3.12: scikit-learn 1.9.1 e dependências para a cabeça de regressão logística. Não foi refeito o treinamento dos embeddings.
- Novo `/home/lucas/tcc-lab/.venv-groq`: CPython 3.12.16, SDK oficial groq 1.7.0 e httpx 0.28.1. O benchmark chama o endpoint compatível por httpx; o SDK fica disponível para exemplos oficiais. A escolha de transporte não muda o modelo ou o prompt.
- Runtime de documentos do Codex no Windows: matplotlib 3.11.2 e PyMuPDF 2.1 com dependências, para gráficos e inspeção do PDF. Não fazem parte dos modelos ou do tempo de inferência.

## Acesso remoto e erros

A chave Groq foi criada/salva pelo usuário, fora do projeto. O programa a lê privadamente. Nenhuma credencial é impressa ou incluída no pacote. Um GET confirmou o catálogo; isso sozinho não verificava inferência ou modalidade de cobrança. O POST inicial por urllib recebeu HTTP 403. Um diagnóstico com httpx teve sucesso HTTP 200 e utilizou 93 tokens numa mensagem sintética; esse diagnóstico não entra no teste. A falta inicial de httpx motivou criar o ambiente separado acima. O benchmark definitivo usa esse transporte e conserva o mesmo protocolo de avaliação.

Não houve contratação, upgrade, configuração de pagamento ou uso de endpoint pago. O script impõe limites locais de chamadas/tokens, espaça requisições, trata 429 com espera limitada e interrompe em outros erros. Essas proteções controlam a execução; não substituem a confirmação de que a conta foi mantida no plano Free pelo usuário.

## Ordem e preservação dos resultados

Os nove pipelines clássicos/contextual foram executados sequencialmente. Depois começaram Llama, DeepSeek e Qwen em sequência. GPT-OSS remoto ocorre em paralelo ao único gerador local. Os 200 IDs e os parâmetros foram congelados antes das predições. Respostas incorretas, inválidas e interrompidas são preservadas. Não ajustamos o prompt, limiar, orçamento ou rótulos depois de inspecionar resultados.

Os resultados completos de 775 exemplos existem apenas para os classificadores e têm tabela separada. Não comparar essa tabela com os 200 dos LLMs como se tivessem o mesmo denominador. Os modelos Lee são controles diagnósticos de corpus muito pequeno; não representam um Word2Vec bem treinado para produção.

## Arquivos e reprodução

`07-benchmark-classicos.py`: extrai vetores e ajusta classificadores; `08-rodar-classicos.sh`: executa um por vez; `09-benchmark-geradores.py`: serve GGUF ou chama Groq e grava cada requisição incrementalmente; `10-diagnosticar-groq.py`: diagnóstico sintético de transporte; `11-rodar-geradores-locais.sh`: sequência dos geradores; `12-avaliar-comparacao.py`: calcula métricas, valida IDs/hashes e confere métricas com scikit-learn; `13-gerar-relatorio.py`: produz apresentação dos resultados, sem alterar predições.

O pico de memória dos classificadores usa o máximo RSS observado por GNU time (máximo de um processo da execução, não soma simultânea). Isso captura o subprocesso fastText que não apareceria no RSS do Python. Geradores usam VmHWM do servidor, com cliente registrado separadamente. RAM remota Groq permanece desconhecida. Não interpretar valor ausente como zero. TTFT não foi instrumentado: a medida é tempo até receber a resposta completa.

O campo `load_seconds` dos classificadores representa a preparação do worker, não somente leitura de pesos: pode incluir cálculo do IDF e, no fastText, cache do vocabulário de treino; no MiniLM inclui a auditoria de truncamento. Por isso a tabela o chama de preparo. O cache de treino não é reutilizado no loop que mede a inferência individual do teste. Os tempos não incluem o treinamento original de text8/fil9.

Uma avaliação agregada preliminar foi executada durante as primeiras mensagens do DeepSeek. Ela não altera dados/predições, mas acrescenta carga temporária ao ambiente. A geração de documentos e o cliente remoto também são atividade de fundo. Não apresentar as latências como repetidas em máquina dedicada totalmente ociosa; uma futura rodada específica de desempenho deve isolar a máquina e repetir medições.

## Palavras raras e o benchmark Rare Words

Compor vetor de uma palavra fora do vocabulário, usando subpalavras do fastText, não é o mesmo que avaliar o benchmark semântico Rare Words (RW). A avaliação RW já havia sido concluída em 29/10/2026, com o avaliador oficial, ZIP do espelho AWS documentado e pares/notas corroborados por cópia acadêmica. Resultado preservado: 2.034 pares avaliados, zero descartados, Spearman rho 0,4177019229655776. Evidências: `../docs/07-rare-words-resolucao.md` e `../logs/execucoes/fasttext-rw-20261029T135536Z-BwFCmr/resultado-exato.json`. A origem Stanford permaneceu inacessível; não há checksum dos autores para provar identidade binária com o ZIP original. O espelho e esse limite estão documentados.

Correção da consolidação de 05/11: um trecho novo deste diário e do relatório de anime tratava RW incorretamente como pendente. A conferência dos logs históricos mostrou a avaliação já concluída. Esses trechos foram corrigidos; não houve novo teste ou treinamento RW nesta rodada. A correlação RW não é acurácia nem qualidade de recomendações e não se mistura com F1 SMS ou nDCG anime.

## Timeout e retomada do Qwen

Depois de 185 respostas concluídas, a próxima requisição terminou com `TimeoutError: timed out`, sob timeout HTTP configurado de 180 segundos. O log do servidor registra cancelamento da tarefa. A causa não foi estabelecida: não atribuímos o evento a memória, suspensão ou capacidade semântica do modelo sem evidência. O processo encerrou pelo tratamento de finalização. A verificação posterior mostrou memória disponível, mas não reconstrói as condições no instante da falha.

Preservamos `server-primeira-execucao.log`, `requests-primeiras-185.jsonl`, `warmup-primeira-execucao.json` e `interruption.json`. O cliente já suporta checkpoint por ID, portanto foi retomado somente para os 15 IDs restantes, mantendo prompt, seeds por índice, parâmetros e orçamento de saída. As 185 respostas anteriores não foram refeitas. Não houve tentativa de trocar uma resposta errada por uma melhor: o evento sem resposta é uma falha operacional e seu registro permanece separado.

A execução retomada não realiza novo aquecimento quando encontra checkpoint, portanto a primeira consulta após reiniciar o servidor pode incluir efeitos de carga fria. As latências finais por SMS correspondem às chamadas concluídas, inclusive a nova tentativa do ID afetado; não incluem a tentativa anterior que expirou. A duração exata dessa tentativa e o tempo total da primeira etapa não foram capturados pelo cronômetro que gravava os resultados, pois a exceção interrompeu a gravação. Não substituir por 180 segundos nominais como se fossem medição exata. O tempo total original do Qwen deve ficar ausente, não igual ao tempo menor da retomada. Reportar duração medida do segundo segmento e soma de latências bem-sucedidas separadamente.

Para transparência, a avaliação também pode calcular uma análise conservadora de primeira tentativa, tratando o ID afetado como inválido. Ela é adicional e explicitamente identificada; as respostas após recuperação e o evento operacional continuam auditáveis. O atualizador de relatórios foi pausado durante essa recuperação para permitir finalizar os metadados antes de gerar o relatório completo. O comparativo de animes permanece aguardando o fechamento dos SMS.

## Fechamento das duas comparações

Os SMS foram concluídos com os 13 pipelines e as mesmas 200 mensagens; Qwen completou as 15 restantes e a igualdade do prefixo de 185 registros foi conferida. O arquivo final mantém tempo total original ausente e duração medida da retomada separada. Posteriormente começou e terminou o comparativo de anime em inglês: 1.000 títulos, 24 consultas, dez referências de recuperação (incluindo aleatório e dois Lee diagnósticos), cinco configurações de geradores para a lista curta, e variantes de fallback identificadas. Nenhuma fase de inferência de anime começou antes do fechamento dos SMS. O QA independente de anime conferiu 720 linhas de ranking contra scikit-learn.

O melhor estático pontual na recuperação de anime foi Word2Vec Skip-gram. Isso substitui a sugestão provisória baseada apenas em classificação SMS como ponto inicial de engenharia, sem declarar vencedor definitivo para o produto. Os testes ainda não validam recomendação anime-para-anime personalizada. O escopo final confirmado é RI com vetores estáticos já preparados e pesos determinísticos, sem treinamento ou ajuste de modelos no programa.
