# LLMs locais gratuitos e preparação da comparação Kaggle

> **Fechamento:** SMS completo, 13/13 pipelines; o [comparativo de anime em inglês](../anime-en-20261105/README.md) também terminou. Relatório atual dos SMS: `../../output/comparacao-sms/relatorio-comparacao-sms.pdf` e `.html`. Qwen foi retomado após timeout, sem repetir as 185 respostas anteriores; o tempo total original não foi inventado. `15-cenarios-sms.py` adiciona análises operacionais sem inferência; `16-documentar-retomada-qwen.py` preserva/explica os metadados da recuperação. Os avisos de execução pendente abaixo são históricos.

> **Entrega preliminar solicitada durante o DeepSeek:** 11/13 pipelines concluídos. Consulte `../../output/comparacao-sms/relatorio-preliminar-sms.pdf` e a versão HTML. Um atualizador independente (`codigo/14-atualizar-quando-concluir.py`) acompanha os arquivos de conclusão e incorpora DeepSeek e Qwen quando disponíveis. O log é `logs/atualizacao-relatorio.log`. Versões anteriores serão guardadas em `output/comparacao-sms/historico`; ao completar 13, será produzido `relatorio-comparacao-sms.pdf`. O atualizador não executa inferência nem novas chamadas de API. Manter computador/WSL ativos para a execução em andamento; se houver interrupção, conferir o estado antes de retomar.

> **Atualização após a escolha da opção Groq e configuração da chave:** o benchmark está em execução em `resultados/benchmark-v1`. Lucas autorizou GPT-OSS 20B pela Groq Free e salvou a credencial fora deste repositório. A autenticação e a inferência funcionaram; houve chamadas externas para esse modelo. Os parágrafos abaixo que dizem "nenhuma API" ou "pendente" descrevem o estado anterior e são mantidos como histórico. O estado atual será consolidado em `resultados/comparacao/comparacao.json` e no relatório de comparação. A virtualização está ativa e todos os ambientes foram reencontrados.

Registro de 05/11/2026. Requisito de Lucas: sem cobrança por API, sem compra de créditos. Lucas escolheu seguir localmente, sem configurar Groq. Nenhuma API de inferência externa foi chamada; não houve pagamento nem cadastro de cartão. Execução local consome os recursos/energia do computador.

**Após reinicialização:** virtualização ativa, Ubuntu iniciou como lucas; arquivos GloVe/fastText encontrados. Conferência dos demais ambientes e benchmark pendentes. Lucas reabriu a discussão de GPT gratuito: [modalidades verificadas e condições de acesso](ACESSO_GPT_SEM_CUSTO_ADICIONAL.md). Nenhuma API externa foi ativada por essa consulta.

## O que está pronto

Runtime oficial `llama.cpp` Windows CPU, build b12110, commit cd959bae99ff4bed22bef2604f45241c09bbb8c8. Executável verificado com `--version`: 0.9.0-dev, Clang 20.1.8, Windows x86_64. Instalado de forma portátil em `C:/tcc-lab/LLMs/runtime-b12110`; não depende de Docker, virtualização, WSL, GPU ou serviço pago. O ZIP teve SHA-256 comparado ao digest da release GitHub.

| Modelo instalado | Arquivo | Bytes | Proveniência |
|---|---|---:|---|
| Llama 3.2 1B Instruct | Llama-3.2-1B-Instruct-Q4_K_M.gguf | 807.694.464 | Pesos Meta, conversão/quantização comunitária Bartowski |
| DeepSeek-R1-Distill-Qwen-1.5B | DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf | 1.117.320.800 | Modelo destilado DeepSeek baseado em Qwen, conversão comunitária Bartowski |
| Qwen3 0.6B | Qwen3-0.6B-Q8_0.gguf | 639.446.688 | GGUF publicado pela organização Qwen |

Pesos em `C:/tcc-lab/LLMs/models`. São versões pequenas e quantizadas; não equivalem às versões completas hospedadas das famílias. Q4_K_M e Q8_0 usam precisões diferentes, que precisam aparecer na comparação. Não houve treinamento ou fine-tuning desses pesos nesta máquina.

Os hashes e revisões exatos estão em `resultados/instalacao.json`. Para os GGUF, o hash foi comparado ao LFS do **publicador do arquivo**, não aos pesos originais em outra precisão. A revisão exata dos pesos-base usados pelo conversor não foi estabelecida de forma independente; não alegar conversão oficial da Meta/DeepSeek. A receita de runtime é oficial do llama.cpp; a proveniência de cada peso é registrada separadamente.

Licença Qwen Apache 2.0; Llama 3.2 usa sua licença própria; o DeepSeek destilado tem licença MIT e deriva de Qwen, conforme o cartão original. Cópias/documentos de licença e cartões estão em `fontes/`. Não aceitar o nome de uma família como garantia de licença idêntica para toda versão.

## Testes feitos de fato

Um modelo por vez, quatro threads, CPU, contexto de 2.048 tokens e servidor restrito a 127.0.0.1. Após `/health` responder, foram enviadas perguntas aritméticas curtas em inglês e português. As requisições/respostas completas, tokenização de uso, tempo e peak working set estão nos JSON; os logs do servidor estão em `logs/`.

- Llama: carregou, gerou resposta e respondeu `4` em ambos os idiomas. Registro `smoke-llama.json`.
- DeepSeek: a configuração inicial sem raciocínio e com apenas 64 tokens produziu saída incompleta/vazia; tentativa preservada em `smoke-deepseek.json`. Com raciocínio e 512 tokens, gerou respostas finais contendo `4` nos dois idiomas: `smoke-deepseek-thinking.json`.
- Qwen: o teste inicial sem raciocínio respondeu incorretamente `2`; com a amostragem oficial sem raciocínio, houve um acerto e um erro. Ambos foram preservados. Com raciocínio, gerou `4` nas duas perguntas; a condição adicional `smoke-qwen-official-sampling-thinking.json` usa explicitamente a amostragem do README (temperatura 0,6, top_p 0,95, top_k 20, min_p 0, presença 1,5), com limite de saída 512 para este teste simples.

Esses testes verificam instalação, uso e algumas respostas simples. **Não são uma avaliação de spam, não demonstram superioridade entre modelos e não garantem qualidade geral.** As condições com raciocínio consomem mais tokens/tempo; não comparar seus tempos a configurações sem raciocínio como se fossem idênticas. O orçamento de saída curto foi escolhido para operação local básica, não para reproduzir todos os benchmarks dos fabricantes, que podem recomendar contextos/saídas muito maiores.

Os servidores de teste foram encerrados após cada execução. Nenhum processo precisa permanecer ativo para preservar os modelos.

## Por que não usamos GPT por API

A documentação da OpenAI apresenta APIs tarifadas. Existem créditos associados a certas assinaturas pagas, mas isso não é uma garantia de API independente 100% gratuita para este projeto. DeepSeek oficial também publica tarifas por token. Não usamos créditos promocionais como solução permanente.

A Groq documenta plano gratuito limitado para alguns modelos, incluindo GPT-OSS. Isso depende de conta/chave, catálogo e limites; não equivale a acesso ilimitado nem a usar os GPTs proprietários do ChatGPT. Na documentação consultada, Llama 3.1/3.3 aparecem como Enterprise e não constam da tabela gratuita observada; não prometemos Llama grátis nessa API. Lucas escolheu a rota local. **Nenhum GPT foi instalado/testado; Qwen é a alternativa local, não um GPT renomeado.**

Fontes consultadas em 05/11/2026: [preços OpenAI](https://developers.openai.com/api/docs/pricing), [créditos condicionados a assinatura](https://developers.openai.com/api/docs/guides/chatgpt-api-credits), [preços DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/), [limites Groq](https://console.groq.com/docs/rate-limits), [catálogo Groq](https://console.groq.com/docs/models).

## Dataset recomendado e já preparado

[SMS Spam Collection do Kaggle](https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset), versão 1. ZIP de 215.934 bytes baixado diretamente do Kaggle, sem credenciais. CSV tem **5.572** mensagens: 4.825 ham e 747 spam. A descrição da fonte anuncia 5.574; preservamos essa divergência e reportamos a contagem real do arquivo.

Após deduplicação normalizada: **5.157** exemplos; zero grupos com rótulos conflitantes. Divisões determinísticas antes de avaliar modelos: treino 3.609, validação 773, teste 775. Subconjunto comum inicial de 200 mensagens: 175 ham e 25 spam. Não comparar F1 obtido em 200 mensagens com resultado de outro modelo em 775 como se fosse a mesma avaliação.

O Kaggle retorna `licenseName: Unknown`; a fonte UCI da coleção declara CC BY 4.0 e pede atribuição. Não transformamos o campo Unknown da cópia Kaggle numa licença presumida. Preservamos os metadados de ambas as fontes para a redação/redistribuição acadêmica. A base foi adquirida do Kaggle, não silenciosamente substituída por outra versão. Fonte original e atribuição: Almeida e Hidalgo, SMS Spam Collection, DOI 10.24432/C5CC84; artigo de Almeida, Hidalgo e Yamakami, DOCENG 2011. [Página UCI](https://archive.ics.uci.edu/dataset/228/sms+spam+collection).

A tarefa é **classificação binária de textos ingleses**, adequada a um teste técnico básico com rótulos existentes. Não mede a busca multilíngue de animes nem escolhe sozinha o estático final do TCC. É uma base pública antiga; possível exposição de LLMs no pré-treinamento deve ser declarada. O protocolo completo está em [PROTOCOLO_COMPARACAO.md](PROTOCOLO_COMPARACAO.md).

Métricas previstas: F1 spam, precisão, recall, macro-F1, balanced accuracy, acurácia, matriz de confusão, falhas de resposta, mediana/p95 de latência, throughput, carga, tempo de treino/codificação, memória e tamanho. ROC-AUC/PR-AUC/calibração exigem scores apropriados; nDCG é de ranking e não é a métrica principal desta classificação.

## Como usar com código

No PowerShell, da pasta do TCC, iniciar um servidor (o terminal fica ocupado até Ctrl+C):

```powershell
& './laboratorio/llms-20261105/codigo/04-iniciar-servidor.ps1' -Model llama
```

Trocar por `deepseek` ou `qwen` para carregar outra família, executando um modelo por vez. A opção `-Port` permite escolher outra porta. O script usa a CPU, limita contexto e escolhe raciocínio nos modelos que dele precisaram no teste. Não troca pesos nem treina.

Em outro PowerShell, enviar uma mensagem:

```powershell
& './laboratorio/llms-20261105/codigo/05-consultar-api-local.ps1' -Text 'Quanto é dois mais dois?'
```

O cliente usa Invoke-RestMethod com JSON e UTF-8. O endereço é fixo no próprio computador, não um provedor pago. O servidor deve estar pronto antes da chamada.

O cliente Python equivalente está em `05-consultar-api-local.py`: usa urllib da biblioteca padrão, prepara `messages`, faz POST em `/v1/chat/completions` e mostra o JSON. Pode rodar com um Python 3 compatível. Nesta sessão, os scripts auxiliares usaram o Python interno do Codex; os executáveis LLM são independentes desse Python. Para o benchmark, usaremos o ambiente de pesquisa após restaurar o WSL.

O script `01-baixar-modelos.py` organiza downloads verificados, extração do runtime e manifesto. `02-preparar-dataset.py` valida e congela os splits sem rodar modelos. `03-testar-modelos.py` inicia um processo oculto, espera saúde HTTP, envia duas perguntas, registra respostas/recursos e encerra. `04` inicia o servidor para uso manual; `05` fornece clientes PowerShell/Python. Não é necessário baixar pesos novamente a cada consulta.

## Pendência para comparar com todos os modelos antigos

O Ubuntu não iniciou nesta sessão: HCS_E_HYPERV_NOT_INSTALLED e mensagem de virtualização desabilitada. A consulta Win32_Processor retornou VirtualizationFirmwareEnabled=False. Placa identificada como Gigabyte B450M S2H; não inferimos a revisão/versão da BIOS. Lucas informou retirada da bateria, compatível com perda de configurações de firmware, sem prova causal definitiva.

Para retomar GloVe/fastText/Word2Vec/MiniLM que estão no Linux: ativar SVM Mode/AMD-V na BIOS/UEFI e reiniciar. A localização exata depende da BIOS. Não reinstalar ou apagar Ubuntu por esse erro. Depois conferir novamente virtualização, iniciar Ubuntu e validar os caminhos/pesos existentes. A ativação de firmware é ação manual de Lucas. [Orientação oficial Microsoft](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting).

A comparação completa ainda não foi executada. O estado está salvo; downloads e servidores de teste encerraram. O computador pode ser reiniciado para essa correção sem interromper treinamento desta tarefa, pois não há treinamento ativo.

## Fontes técnicas

- [Releases oficiais llama.cpp](https://github.com/ggml-org/llama.cpp/releases/tag/b12110).
- [Llama original Meta](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) e [GGUF comunitário usado](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF).
- [DeepSeek original](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B) e [GGUF comunitário usado](https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF).
- [Qwen GGUF oficial usado](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF).

Não há resultados comparativos novos de precisão no Kaggle nesta entrega. Os testes aritméticos não foram usados para selecionar mensagens do teste ou mudar seus rótulos.
