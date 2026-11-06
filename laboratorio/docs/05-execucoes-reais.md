# Execuções reais após reinicialização

Data: 29/10/2026, horário de Brasília. Resultados abaixo conferidos após o encerramento dos programas. Não usar mensagens de progresso como métricas finais.

## Ambiente validado

O Windows foi reiniciado às 09:48:14. A consulta WSL identificou Ubuntu em execução, versão 2. O comando Linux `id` confirmou usuário `lucas`, UID 1000. Sistema: Ubuntu 26.04.1 LTS; kernel `6.18.40.1-microsoft-standard-WSL2`; aproximadamente 6,7 GiB de RAM atribuídos ao Linux e 2 GiB de swap.

O espaço apresentado por `df` é a capacidade lógica do disco virtual expansível, não espaço físico livre garantido em C:. Os arquivos Linux também consomem o disco do Windows.

## Instalação das dependências — concluída

```powershell
wsl.exe -d Ubuntu -u root -- bash -lc 'set -euo pipefail; apt-get update; DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential python3 python3-venv python3-pip wget unzip perl ca-certificates git time'
```

Código de saída zero. O usuário Linux foi selecionado como `root` apenas para instalar pacotes de sistema; o ambiente do laboratório e os modelos são executados como `lucas`. Nenhuma senha foi solicitada ou armazenada. O log inclui avisos de conexão ao systemd durante os triggers; a instalação concluiu e as ferramentas foram verificadas posteriormente.

O script `01-preparar-linux.sh` foi executado e concluiu com código zero. Copiou os repositórios e os dados para `/home/lucas/tcc-lab`, conferiu revisões e criou `.venv`. Dependências efetivamente resolvidas: Python 3.14.4, NumPy 2.5.4, SciPy 1.18.1 e pip 25.1.1. Versões dos compiladores e lista completa de pacotes estão em `manifests/linux/`.

Logs: `07-dependencias-ubuntu.txt`, `08-validacao-wsl.txt` e `10-preparacao-linux.txt`.

## GloVe

Execução iniciada com `02-executar-oficial.sh glove`. O wrapper chama o `demo.sh` preservado e registra a execução em `~/tcc-lab/runs/`. Log espelhado: `12-glove-oficial.txt`.

O vocabulário do text8 conteve 71.290 palavras após o filtro mínimo 5. O corpus processado teve 17.005.207 tokens segundo o programa oficial. Esses números descrevem a entrada do exemplo; não são métricas de qualidade.

**Concluído com código zero.** Identificador: `glove-20261029T125916Z-glk9aY`.

| Medida do avaliador oficial | Resultado |
|---|---|
| Questões cobertas | 17.827 / 19.544 (91,21%) |
| Analogias semânticas | 2.038 / 7.416 (27,48%) |
| Analogias sintáticas | 2.152 / 10.411 (20,67%) |
| Acurácia total entre questões cobertas | 4.190 / 17.827 (23,50%) |
| Tempo total do demo oficial | 6 min 58,14 s |
| Pico de RSS reportado por GNU time | 1.942.808 KiB (aproximadamente 1,85 GiB) |
| Swaps reportados por GNU time | 0 |

O denominador da acurácia exclui questões com palavras ausentes do vocabulário. O tempo inclui compilação, preparação, treinamento e avaliação; não é tempo isolado do treinamento. Pico de RSS de um processo não é medição do consumo agregado do Windows/WSL. O custo final de treinamento foi 0,036180; não é a acurácia.

O exemplo próprio de consulta carregou os 71.290 vetores de dimensão 50 e retornou vizinhos para `king`, incluindo `emperor` e `henry`. O resultado completo está em `14-glove-consulta.txt`. Não se deve transformar essa inspeção qualitativa em resultado quantitativo de recomendação.

## fastText: por que separar as etapas

A tentativa de acessar RW pelo Ubuntu retornou `No route to host` para `nlp.stanford.edu:443`; log `09-rw-linux.txt`. O script oficial completo baixa RW antes do treinamento. Por isso foi criado o wrapper próprio `04-fasttext-etapas.sh`, que preserva os parâmetros do comando skip-gram oficial e permite treinar sem alegar avaliação RW concluída.

O modo `embeddings` compila o código oficial, treina em `fil9` com os parâmetros originais de uma época, salva o modelo, recarrega pela CLI e verifica vetores de palavras e de sentença. O teste numérico adicional é código próprio: verifica dimensão, valores finitos e vetores não nulos, incluindo uma palavra didática ausente. Não substitui correlação com julgamentos humanos.

O modo `cooking` segue o primeiro classificador do [tutorial oficial de classificação](https://fasttext.cc/docs/en/supervised-tutorial.html), sem aplicar as melhorias posteriores. Download oficial: `https://dl.fbaipublicfiles.com/fasttext/data/cooking.stackexchange.tar.gz`, com 457.609 bytes. O arquivo compactado foi listado com sucesso; log `11-cooking-download.txt`. O script usa 12.404 linhas de treino e 3.000 de validação, executa `supervised`, `test` com k=1/k=5 e `predict` com as duas perguntas do tutorial.

Esse teste avalia classificação, enquanto o objetivo estático usa embeddings não supervisionados. Resultados das duas tarefas devem ser apresentados separadamente. Não foram inventados escores RW nem usados dados de terceiros como substituição silenciosa.

### Compatibilidade de compilador

A primeira compilação fastText falhou em `src/args.cc`: `uint64_t` não declarado, com sugestão de incluir `<cstdint>` pelo GCC 15. Não foi aplicada alteração ao código oficial. Instalado o pacote `g++-12` dos repositórios Ubuntu (12.5.0), selecionado pela variável de Make `CXX`. Logs: `13-fasttext-cooking.txt` (tentativa com erro), `15-compilador-fasttext.txt` (pacote), `16-fasttext-cooking-gcc12.txt` (nova execução). A escolha deve ser preservada em reproduções. Os wrappers agora registram o compilador selecionado.

### Classificação cooking — concluída

Código de saída zero, execução `fasttext-cooking-20261029T130834Z-E1mBGZ`.

| Medida | Resultado |
|---|---|
| Exemplos de validação | 3.000 |
| P@1 | 0,151 |
| R@1 | 0,0652 |
| P@5 | 0,0679 |
| R@5 | 0,147 |
| Tempo do comando de treinamento | 2,10 s |
| Pico de RSS desse comando | 129.772 KiB |

São os resultados efetivamente observados, não os números ilustrativos publicados no tutorial. O treinamento com várias threads pode variar. A primeira pergunta do tutorial retornou `__label__baking`; a segunda, `__label__food-safety`, reproduzindo também uma limitação qualitativa discutida pelos autores. As predições foram obtidas carregando `model_cooking.bin` em um novo processo da CLI. Esse modelo demonstra a funcionalidade supervisionada; não é o modelo de embeddings do experimento principal.

## Organização dos resultados

### Embeddings fastText — concluídos; avaliação RW adicionada posteriormente

Código de saída zero, execução `fasttext-embeddings-20261029T130918Z-vZJ4RY`. Log principal: `17-fasttext-embeddings.txt`; evidências completas exportadas em `logs/execucoes/`.

| Medida | Resultado |
|---|---|
| Corpus | fil9, 713.069.767 bytes; MD5 conferido com o publicador |
| Configuração | Skip-gram, 100 dimensões, uma época; parâmetros completos em `comando.txt` |
| Entradas do arquivo de vetores | 218.316 |
| Tempo do comando de treinamento | 11 min 44,98 s, incluindo leitura e gravação do modelo |
| Pico de RSS do comando | 1.224.096 KiB (aproximadamente 1,17 GiB) |
| Arquivo do modelo completo | `fastText/result/fil9.bin`, 978.480.868 bytes |
| Carregamento em novos processos CLI | Concluído para vetores de palavras e de sentença |
| Verificação numérica própria | Três vetores 100d finitos e não nulos; uma sentença 100d finita |
| Avaliação de similaridade RW | Concluída posteriormente com cópia AWS corroborada: rho 0,4177; ver `07-rare-words-resolucao.md` |

O arquivo `.vec` contém as representações de palavras conhecidas e foi conferido pelo cabeçalho `218316 100`; o `.bin` mantém o modelo necessário à composição por subpalavras. A consulta didática incluiu `king`, `queen` e `unseenwordexample`. A ausência dessa última consulta no vocabulário foi confirmada percorrendo as entradas de `.vec`, com saída `False`, no log `18-fasttext-vocabulario.txt`; a capacidade numérica de gerar seu vetor não prova qualidade semântica.

O custo final reportado foi 0,881688, uma medida da otimização, não um escore de relevância ou similaridade humana. Não compará-lo ao custo GloVe, pois objetivos e dados diferem.

Os hashes dos modelos concluídos estão em `manifests/estado-linux-atual.json`; os repositórios Linux permaneceram sem alterações rastreadas. O binding Python fastText continua fora desta instalação; o executável oficial já está disponível e foi usado nos testes. Pesos LLM não foram baixados nesta etapa.

### Evidências exportadas

Cada pasta de execução inclui saída integral, comando, código de saída, início/fim UTC, hashes e medição de recursos quando aplicável. O horário UTC nos arquivos permite auditoria; Brasília está três horas atrás nesta data. Tempo medido no WSL descreve esta configuração e esta execução, não a velocidade geral do algoritmo.

Para uso futuro a partir de Python, a CLI fastText pode ser chamada por `subprocess`. O binding Python oficial ainda não foi instalado; compilar o executável não instala o módulo `import fasttext`. GloVe fornece seus programas e vetores; a representação agregada de sinopses será código específico da etapa de anime.
