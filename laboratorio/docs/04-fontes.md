# Fontes primárias

Consultadas em **29 de outubro de 2026**. Os links com `main`/`master` podem mudar; para GloVe e fastText, as revisões efetivamente baixadas constam em `manifests/artefatos.json` e há cópias dos arquivos relevantes em `fontes/`.

| Fonte | Uso |
|---|---|
| [GloVe, repositório Stanford](https://github.com/stanfordnlp/GloVe) | Requisitos, compilação e demonstração |
| [demo.sh na revisão preservada](https://github.com/stanfordnlp/GloVe/blob/52f7dbc512be3f72e9c11e7cbb19dfdfa4651e9c/demo.sh) | Corpus, parâmetros e encadeamento das etapas |
| [fastText, repositório Meta](https://github.com/facebookresearch/fastText) | Plataformas, requisitos e instalação |
| [fastText v0.9.2](https://github.com/facebookresearch/fastText/tree/v0.9.2) | Versão escolhida para a CLI |
| [Exemplo oficial fixado](https://github.com/facebookresearch/fastText/blob/5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe/word-vector-example.sh) | Pré-processamento, treinamento e Rare Words |
| [Tutorial de vetores fastText](https://fasttext.cc/docs/en/unsupervised-tutorial.html) | Uso de enwik9, comandos e interpretação dos arquivos |
| [Tutorial de classificação fastText](https://fasttext.cc/docs/en/supervised-tutorial.html) | Base cooking, corte treino/validação, treinamento, predição e métricas |
| [Rare Words, autores](https://nlp.stanford.edu/~lmthang/morphoNLM/) | Origem do benchmark; acesso direto falhou nesta rede |
| [Notebook AWS na revisão preservada](https://github.com/aws/amazon-sagemaker-examples/blob/4883224d0032906f1a2bafd4887544ff5ddae606/introduction_to_amazon_algorithms/blazingtext_word2vec_subwords_text8/blazingtext_word2vec_subwords_text8.ipynb) | Referência primária AWS para a cópia RW usada |
| [Cópia acadêmica RW](https://github.com/mfaruqui/eval-word-vectors/blob/master/data/word-sim/EN-RW-STANFORD.txt) | Corroboração de 2.034 pares/notas, blob Git registrado |
| [Matt Mahoney, dados](https://mattmahoney.net/dc/textdata.html) | Origem dos corpora apontados pelos exemplos |
| [WSL, Microsoft Learn](https://learn.microsoft.com/en-us/windows/wsl/install) | Requisitos Windows e instalação Ubuntu |
| [GCC, documentação Canonical](https://github.com/canonical/ubuntu-for-developers-docs/blob/main/docs/howto/gcc-setup.md) | Compiladores no Ubuntu |
| [build-essential, Ubuntu](https://packages.ubuntu.com/build-essential) | Metapacote de compilação |
| [venv, documentação Python](https://docs.python.org/3/library/venv.html) | Isolamento das bibliotecas |
| [Cygwin, instalação](https://cygwin.com/install.html) | Alternativa considerada; não instalada |
| [Word2Vec, Gensim](https://radimrehurek.com/gensim/models/word2vec.html) | Modelo adicional sugerido |
| [Tutorial Word2Vec, Gensim](https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html) | Corpus Lee, salvamento e avaliação; executados na continuação |
| [Gensim 4.4.0, PyPI](https://pypi.org/project/gensim/4.4.0/) | Versão efetivamente instalada |
| [CPython 3.12.16, Python.org](https://www.python.org/downloads/release/python-31216/) | Fonte e checksum do interpretador separado |
| [Compilação Python Unix](https://docs.python.org/3.12/using/unix.html#building-python) | Configure, Make e altinstall |
| [Doc2Vec, Gensim](https://radimrehurek.com/gensim/models/doc2vec.html) | Representações de documentos |
| [Sentence Transformers, quickstart](https://www.sbert.net/docs/quickstart.html) | Recuperação semântica com embeddings de sentenças |
| [MiniLM multilíngue, autores](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) | Encoder 384d, idiomas e exemplo de uso executado |
| [Sentence Transformers, instalação](https://www.sbert.net/docs/installation.html) | Ambiente de inferência de sentenças |
| [PyTorch, instalação](https://pytorch.org/get-started/locally/) | Backend CPU |
| [Llama 3.2, Meta](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/MODEL_CARD.md) | Tamanhos, idiomas e licença |
| [DeepSeek-R1, autores](https://github.com/deepseek-ai/DeepSeek-R1) | Modelo completo e variantes destiladas |
| [Qwen2.5-0.5B-Instruct, autores](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | Alternativa pequena para inferência |
| [GPT-2, OpenAI](https://github.com/openai/gpt-2) | Pesos e implementação histórica abertos |
| [gpt-oss, documentação OpenAI](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers) | Formatos e requisitos de execução |
| [API OpenAI, quickstart](https://developers.openai.com/api/docs/quickstart) | Uso de modelos hospedados |
| [llama.cpp, documentação de compilação](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md) | Runtime independente para inferência CPU/Windows |

## Referências acadêmicas iniciais

Os artigos abaixo são os indicados pelas documentações dos algoritmos. Ainda será necessário formatá-los na norma exigida pelo TCC e conferir os metadados na etapa de redação final.

- Pennington, Socher e Manning. *GloVe: Global Vectors for Word Representation*. EMNLP, 2014. [Projeto Stanford](https://nlp.stanford.edu/projects/glove/).
- Bojanowski, Grave, Joulin e Mikolov. *Enriching Word Vectors with Subword Information*. 2017. [Artigo](https://arxiv.org/abs/1607.04606).
- Luong, Socher e Manning. *Better Word Representations with Recursive Neural Networks for Morphology*. CoNLL, 2013. [Página dos autores](https://nlp.stanford.edu/~lmthang/morphoNLM/).

O guia e os wrappers deste laboratório foram preparados com assistência do Codex. Comandos, saídas e estados devem ser conferidos antes de transpor afirmações para o texto acadêmico. Preservar fontes e evidências permite distinguir sugestões, procedimentos preparados e experimentos realmente executados.
