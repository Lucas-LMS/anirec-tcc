# Word2Vec: instalação, teste oficial e próximos passos

Etapa iniciada em 29/10/2026, após autorização para continuar a preparação. Escolha: acrescentar Word2Vec, já recomendado como próximo embedding estático, usando a implementação Gensim. Isso não instala nem altera o código original C dos autores de Word2Vec; Gensim é a biblioteca escolhida para implementar esse algoritmo.

## Fontes oficiais e escopo

- [Instalação Gensim](https://radimrehurek.com/gensim/intro.html#installation): instalação com pip.
- [Tutorial Word2Vec Gensim](https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html): treinamento com `lee_background.cor`, consultas, salvamento/carregamento e avaliação com `questions-words.txt`.
- [Pacote Gensim 4.4.0 no PyPI](https://pypi.org/project/gensim/4.4.0/): versão selecionada pelo instalador.
- [Python 3.12.16](https://www.python.org/downloads/release/python-31216/): fonte do interpretador adicional.
- [Compilação do Python em Unix](https://docs.python.org/3.12/using/unix.html#building-python): `configure`, Make e `altinstall`.
- [Dependências de compilação CPython](https://devguide.python.org/getting-started/setup-building/#install-dependencies).

A documentação web consultada exibe Gensim 4.3.3; a instalação atual resolveu 4.4.0. A execução registra os parâmetros efetivos para não assumir que todo default de uma versão é idêntico ao de outra.

O tutorial permite começar pela seção de treinamento quando não se deseja baixar o modelo Google News de aproximadamente 2 GB. Foi escolhida essa rota: usar o corpus Lee já distribuído no pacote. Google News não foi baixado nesta etapa.

## Ambiente e falhas observadas

Um ambiente `.venv-word2vec` foi inicialmente criado com Python 3.14.4, separado do ambiente `.venv` usado nas avaliações anteriores. `pip install --upgrade gensim` baixou o código-fonte 4.4.0 e tentou compilá-lo.

1. A primeira tentativa falhou por ausência de `Python.h`. Instalado `python3-dev` via apt.
2. A segunda falhou em extensões C do pacote, com erros como acesso a `PyLongObject.ob_digit` e assinatura de `_PyLong_AsByteArray`. Não foi alterado o código Gensim para forçar compatibilidade com Python 3.14.
3. A rota selecionada foi instalar CPython 3.12.16 no diretório do usuário e criar `.venv-word2vec-py312`. O Python do Ubuntu e os ambientes anteriores são preservados. O ambiente de tentativa com Python 3.14 também foi preservado como evidência, mas não é o ambiente de uso.

Logs dessas etapas: `19-word2vec-instalacao.txt`, `20-python-dev.txt`, `21-word2vec-instalacao-dev.txt`, `22-cpython-dependencias.txt` e `23-python312-word2vec.txt`.

## Procedimento reproduzível

No Ubuntu, as dependências de compilação adicionais foram instaladas com:

```bash
sudo apt-get install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev libncurses-dev uuid-dev
```

Essas bibliotecas permitem compilar os módulos de TLS, compressão, leitura de terminal, SQLite, interfaces C e outros componentes do CPython. A chamada equivalente pelo Windows selecionou `root` no WSL para o apt; a compilação e o laboratório rodam como `lucas`.

`11-preparar-python-word2vec.sh` baixa o tarball oficial Python 3.12.16, confere o SHA-256 publicado, extrai, executa `./configure --prefix=...`, `make -j4` e `make altinstall`. O prefixo é `/home/lucas/.local/tcc-python-3.12.16`. `-j4` usa quatro processos de compilação; `altinstall` instala o binário versionado, seguindo a recomendação Python para evitar substituir o interpretador do sistema. A compilação não usa otimização por perfil, pois o objetivo é compatibilidade e isolamento.

O mesmo script verifica módulos essenciais, cria o venv, instala Gensim e registra relatório de instalação pip, versões e origem/hash dos pacotes. Preserva também o tarball Gensim 4.4.0. Os downloads ficam em `~/tcc-lab/Word2Vec/downloads`. Esses são componentes de infraestrutura e implementação; não são pesos pré-treinados.

## Testes preparados

`09-word2vec-lee.py` envolve a API oficial em código próprio de registro. Lê o corpus linha a linha e aplica `simple_preprocess`, seguindo o tutorial. Treina CBOW com o construtor padrão e Skip-gram alterando somente `sg=1`, uma variante adicional nossa com parâmetro documentado. Não são duas implementações independentes.

Para cada modelo, consulta um vetor e vizinhos, confirma valores finitos, verifica o erro para palavra ausente, salva e carrega o modelo, confere que o vetor se manteve idêntico após carregar e exporta `.vec`. O arquivo `.model` permite continuar o treinamento; o `.vec` exporta as representações para consultas por outras ferramentas.

Também chama `evaluate_word_analogies` com o conjunto distribuído no Gensim. Registra questões cobertas e acertos, sem confundir falta de cobertura com uma avaliação ampla. O corpus Lee é pequeno e didático: esses números não devem ser comparados diretamente aos do GloVe/text8. Não se trata ainda de um experimento comum entre modelos nem de recomendação de animes.

`10-word2vec-executar.sh` cria a pasta da execução, registra tempo/memória e código de saída e recusa sobrescrever modelos anteriores. Comando no Ubuntu:

```bash
bash '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/scripts/10-word2vec-executar.sh'
```

## Resultados reais

**Concluído com código de saída zero.** Execução `word2vec-lee-20261029T134527Z-1ST39z`, log `24-word2vec-lee.txt` e evidências em `logs/execucoes/`.

Ambiente: CPython 3.12.16, Gensim 4.4.0, NumPy 2.5.4, SciPy 1.18.1, smart_open 9.0.0, wrapt 2.5.1. A extensão otimizada foi importada, com `FAST_VERSION=0`. O tarball CPython teve SHA-256 conferido com a página oficial. O relatório pip registra os hashes publicados dos arquivos recebidos. O script de preparação foi fixado em Gensim 4.4.0 após a resolução inicial, para repetir a versão observada; as bibliotecas resolvidas estão no arquivo de requisitos.

O corpus distribuído no pacote tem 300 documentos e 360.082 bytes. Cada modelo produziu vocabulário de 1.750 palavras, vetores 100d, janela 5, frequência mínima 5, cinco épocas, três workers e seed 1. CBOW usou `sg=0`; Skip-gram, `sg=1`. Semente fixa com várias threads não implica reprodução bit a bit.

| Verificação | CBOW | Skip-gram |
|---|---|---|
| Treinamento | 0,74 s | 1,08 s |
| Consulta com vetor finito 100d | Passou | Passou |
| Salvar/carregar preserva o vetor consultado | Passou | Passou |
| Palavra ausente gera KeyError | Confirmado | Confirmado |
| Analogias cobertas | 146 / 19.544 | 146 / 19.544 |
| Acertos entre as cobertas | 0 / 146 | 2 / 146 |
| Acurácia entre as cobertas | 0% | 1,37% |

Cobertura: aproximadamente **0,75%** do benchmark. O conjunto pequeno e os poucos passos de aprendizagem não produziram bons vizinhos semânticos na inspeção de `king`; os resultados não sustentam uso desse modelo didático como recomendador pronto. A instalação e as operações da API funcionaram, mas qualidade para o catálogo precisa de outro experimento. Não concluir que Skip-gram é superior a CBOW ou que Word2Vec é inferior ao GloVe a partir desses números.

O runner completo levou 4,44 s e teve pico de RSS de 135.316 KiB; esse tempo inclui os dois modelos, avaliações e registros, mas não a instalação/compilação do Python. Modelos: `/home/lucas/tcc-lab/Word2Vec/models/lee-cbow.model` e `lee-skipgram.model`; representações exportadas nos arquivos `.vec` correspondentes. Metadados e hashes: `manifests/word2vec/` e `manifests/estado-linux-atual.json`.

## Próximas etapas propostas

Após os estáticos estarem utilizáveis: testar um modelo de embeddings de sentenças apropriado à busca de sinopses; avaliar um LLM pequeno com uma função bem definida; congelar o catálogo de animes, idiomas e protocolo comum de relevância. A escolha de um modelo gerador não deve substituir a definição da tarefa de recuperação. Esses próximos modelos não são instalados automaticamente pelo teste Word2Vec.
