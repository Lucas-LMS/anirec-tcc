# Guia de execução e explicação dos comandos

## 1. Preparar Linux

**Estado: concluído nesta máquina após a reinicialização.** Ubuntu validado e dependências instaladas; ver `05-execucoes-reais.md`. Os comandos abaixo preservam o procedimento para reprodução no terminal **Ubuntu**. Não colar comandos `sudo` diretamente no PowerShell.

```bash
sudo apt-get update
sudo apt-get install -y build-essential g++-12 python3 python3-venv python3-pip wget unzip perl ca-certificates git time
```

`update` atualiza o índice de pacotes. `install` instala os pacotes e suas dependências no Ubuntu. `build-essential` fornece o compilador C/C++, Make e componentes de compilação. Python executa as avaliações; `venv` isola bibliotecas. `wget` baixa os dados; `unzip` extrai ZIPs; Perl executa o pré-processamento oficial fastText; certificados permitem HTTPS; Git verifica a revisão; `time` mede tempo e memória no Linux. Esses são componentes de infraestrutura, não modelos.

Compatibilidade constatada: a tag fastText v0.9.2 falhou com o GCC 15 por ausência de declaração de `uint64_t` via includes indiretos. Foi acrescentado o pacote Ubuntu `g++-12` e o wrapper por etapas seleciona esse compilador com `make CXX=g++-12`, mantendo os arquivos oficiais intactos. O GloVe utilizou GCC 15. Essa escolha é parte do ambiente reproduzível, não alteração de algoritmo.

## 2. Configurar o diretório e as bibliotecas de avaliação

Na primeira execução, o script abaixo cria `~/tcc-lab`, copia os clones e dados já baixados do Windows quando disponíveis, confere os commits e cria um ambiente Python. A execução usa o sistema de arquivos Linux para compilação e arquivos temporários. Precisa de alguns GiB adicionais de disco, além do espaço ocupado no Windows.

```bash
bash '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/scripts/01-preparar-linux.sh'
```

O script instala **NumPy e SciPy** no ambiente virtual local com pip; são dependências declaradas pelos avaliadores oficiais. Não instala um pacote Python GloVe nem um pacote fastText de terceiros. `requirements-resolved.txt`, `pip-inspect.json` e `pacotes-linux.txt` registram as versões resolvidas. Uma instalação futura sem usar as versões registradas não é idêntica à original; o lock só existirá após executar essa etapa.

## 3. GloVe: demonstração oficial

```bash
bash '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/scripts/02-executar-oficial.sh' glove
```

O wrapper ativa o ambiente Python, confere a revisão, registra a chamada e executa **`bash demo.sh`**, sem editar o arquivo oficial. O demo compila, usa `text8`, conta palavras, calcula coocorrências, embaralha os registros, treina vetores e executa o avaliador oficial de analogias.

Configuração presente no demo fixado: vetores 50d, 15 iterações, janela 15, frequência mínima 5, 8 threads, `x_max=10` e parâmetro de memória 4,0. Esse último é orçamento do programa para certas etapas, não medição de RAM total. O demo produz `vocab.txt`, `cooccurrence.bin`, `cooccurrence.shuf.bin` e arquivos `vectors.*`.

**Critério de conclusão:** código de saída zero, vetores presentes e saída da avaliação registrada com cobertura e acurácia. Não existe neste laboratório uma acurácia mínima inventada para declarar a instalação correta. A qualidade deve ser interpretada separadamente. Analogia é um teste intrínseco; não mede recomendação de anime.

## 4. fastText: exemplo oficial de vetores

```bash
bash '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/scripts/02-executar-oficial.sh' fasttext
```

Executa **`bash -e word-vector-example.sh`** da tag oficial. A opção externa `-e` interrompe em erros de comandos simples; não muda parâmetros do modelo. O wrapper verifica os downloads antes de entrar no script e habilita `pipefail` no subprocesso, para evitar que falhas de pipelines passem despercebidas.

O script usa `wikifil.pl` para limpar o XML de `enwik9`, compila com Make, treina skip-gram, calcula vetores para os pares Rare Words e executa `eval.py`. Sua configuração inclui dimensão 100, uma época, janela 5, taxa inicial 0,025, frequência mínima 5, cinco negativos, buckets 2.000.000, n-gramas de caracteres de 3 a 6 e quatro threads. O tutorial interativo usa defaults diferentes; executar o script de uma época reproduz **esse exemplo**, não todo experimento do artigo.

`result/fil9.bin` guarda o modelo completo e permite obter vetores para palavras ausentes do vocabulário; `result/fil9.vec` guarda os vetores das palavras conhecidas e não substitui o `.bin` para essa funcionalidade. A avaliação oficial reporta correlação de Spearman com julgamentos humanos e cobertura.

**Origem RW:** o endereço oficial `https://nlp.stanford.edu/~lmthang/morphoNLM/rw.zip` não respondeu. A avaliação foi posteriormente concluída com cópia AWS e conferência de todos os pares/notas contra outra cópia acadêmica; ver `07-rare-words-resolucao.md`. O script original continua referenciando Stanford quando não há arquivo local. O script `13-rw-copia-verificada.sh` registra a rota alternativa, audita os arquivos e só então chama o avaliador. Isso não altera silenciosamente o benchmark.

**Critério de conclusão:** código zero, `.bin` e `.vec` presentes e avaliação RW registrada. A correlação não é diretamente comparável à acurácia de analogias do GloVe, pois as tarefas e os corpora diferem.

## 5. Consultar e carregar um modelo

Após treinamento real, no Ubuntu:

```bash
cd ~/tcc-lab/fastText
printf 'king\nqueen\nunseenwordexample\n' | ./fasttext print-word-vectors result/fil9.bin
printf 'king\n' | ./fasttext nn result/fil9.bin
printf 'berlin germany france\n' | ./fasttext analogies result/fil9.bin
printf 'an adventure about friendship\n' | ./fasttext print-sentence-vectors result/fil9.bin
```

São consultas pela CLI oficial: carregam o `.bin`, imprimem vetores, vizinhos, analogias ou vetor de sentença. As palavras acima são entradas didáticas próprias e não um benchmark. O primeiro uso de vetores fora do vocabulário verifica funcionalidade, não comprova qualidade semântica. GloVe fornece vetores textuais e seu avaliador oficial; para agregá-los por sinopse será necessário código próprio documentado numa etapa posterior.

## 6. Custos, registros e repetição

Executar um modelo por vez. As durações efetivamente medidas nesta máquina estão em `05-execucoes-reais.md` e nos arquivos `recursos.txt`; elas não garantem a duração de outro corpus ou de outra execução. A avaliação de analogias também pode ser custosa. Cada execução cria uma pasta em `~/tcc-lab/runs` e guarda comando, log, código de saída, duração e pico de memória quando `/usr/bin/time` estiver disponível. Os modelos ficam nos diretórios oficiais, sendo necessário preservá-los antes de repetir um treinamento que os sobrescreva; o wrapper impede repetição se já encontrar o modelo.

Ao terminar, copiar a pasta da execução e os manifests Linux para `laboratorio/logs/` e `laboratorio/manifests/`, documentando o identificador do experimento. Os resultados não são sincronizados automaticamente. Registrar qualquer ajuste de RAM, threads, épocas, versão ou corpus antes de chamar a execução de reprodução do exemplo.

Para desfazer apenas a ativação Python, executar `deactivate`. A remoção do ambiente, dos modelos ou da distribuição Linux não está automatizada, para evitar perda de evidências.

## 7. Entender o código próprio do laboratório

`01-preparar-linux.sh` usa `set -euo pipefail` para parar em erros e variáveis ausentes. `LAB_ROOT` e `SEED_ROOT` permitem escolher os diretórios. `prepare_repo` copia os arquivos já adquiridos ou clona da origem oficial, compara o commit e recusa código rastreado modificado. `python3 -m venv` cria o ambiente, `source` o ativa e pip instala somente as dependências de avaliação. `tee` preserva a saída e a exibe ao mesmo tempo. As consultas de versão e `dpkg-query` registram o ambiente realmente resolvido.

`02-executar-oficial.sh` seleciona o modelo com `case`, confere plataforma, dependências e revisão e impede sobrescrever um modelo já existente. `mktemp` cria uma pasta exclusiva para a execução. A função `download_zip` baixa para um arquivo `.part`, verifica o ZIP e só então publica o arquivo de entrada com `mv`. `trap` grava o código de saída mesmo quando uma etapa falha. `/usr/bin/time -v` mede a execução completa do script oficial, incluindo suas etapas internas; não é uma medição isolada do treinamento. Os hashes finais identificam os artefatos produzidos.

`03-atualizar-manifesto.ps1` pode ser executado no PowerShell, da pasta do projeto, com `& ./laboratorio/scripts/03-atualizar-manifesto.ps1`. Ele consulta os arquivos existentes, calcula tamanhos e SHA-256, compara MD5 de dados com os publicados por Matt Mahoney e registra commits e origens Git em JSON. Divergência de MD5 interrompe o inventário. O campo de treinamento representa o estado inicial desta sessão e deve ser atualizado com evidências após uma execução futura. MD5 é usado aqui para compatibilidade com a publicação histórica; SHA-256 também é preservado.

## 8. Execução por etapas do fastText e consulta Python GloVe

Enquanto RW estiver inacessível, `04-fasttext-etapas.sh embeddings` executa separadamente o comando de treinamento do exemplo oficial e uma verificação numérica própria, sem declarar RW avaliado. `04-fasttext-etapas.sh cooking` executa o primeiro exemplo do tutorial oficial de classificação, com a base e o corte treino/validação documentados pelos autores. Esses modos geram registros próprios e recusam sobrescrever modelos existentes.

`05-consultar-glove.py` lê `vectors.txt`, converte os números em uma matriz NumPy, normaliza cada vetor para comprimento unitário e calcula o produto escalar com a palavra consultada. Após normalização, esse produto é o cosseno. O código exclui a própria consulta da lista e informa quando a palavra não existe no vocabulário. Não inventa vetor para palavra ausente. Uso no Ubuntu após o treinamento:

```bash
source ~/tcc-lab/.venv/bin/activate
python '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/scripts/05-consultar-glove.py' --vectors ~/tcc-lab/GloVe/vectors.txt --word king --top-k 5
```

Essa consulta é uma demonstração funcional própria; os vizinhos retornados não constituem uma métrica de relevância no catálogo de animes.

## 9. Retomar somente a avaliação Rare Words

Depois que o endereço oficial voltar a responder, executar `07-avaliar-rw.sh` no Ubuntu. Ele usa o modelo já salvo em `fastText/result/fil9.bin`, baixa RW da origem original, prepara as consultas com os comandos do script dos autores e chama `eval.py` oficial. Não é necessário retreinar. O script não foi validado com o dataset nesta sessão, pois a origem está inacessível; foi preparado para essa retomada e submetido à checagem de sintaxe.

`06-exportar-registros.sh` copia logs e manifestos das execuções encerradas para a pasta do TCC, registra hashes dos modelos concluídos e confere o estado Git. Ele preserva tentativas com erro para auditoria. Os pesos volumosos permanecem no sistema de arquivos Linux.
