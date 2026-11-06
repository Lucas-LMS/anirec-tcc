# Guia de leitura e uso - sem confundir vetores com respostas

## Onde começar

O relatório novo ficará em `output/comparacao-sms/relatorio-comparacao-sms.pdf` e na versão HTML ao lado. Os arquivos anteriores em `output/manual` explicam a instalação histórica de GloVe, fastText, Word2Vec e MiniLM; não foram apagados. O benchmark SMS é uma etapa nova, não substitui o piloto de anime anterior.

Para auditar os números, abra `laboratorio/llms-20261105/resultados/comparacao/comparacao.csv`. A fonte detalhada é o JSON na mesma pasta. Para uma decisão específica, encontre o ID em `dados/test-common-200.jsonl` e no `predictions.json` de cada pipeline. Os LLMs também têm `requests.jsonl`, com prompt e resposta brutos. Não há chave nesses registros.

## O que está instalado

No Ubuntu, em `/home/lucas/tcc-lab`: GloVe text8, fastText fil9, Word2Vec CBOW/Skip-gram text8 e os controles Lee, MiniLM multilíngue, runtime Linux llama.cpp e ambientes Python. No Windows: os três GGUF (Llama 3.2 1B Instruct, DeepSeek-R1-Distill-Qwen 1.5B e Qwen3 0.6B), runtime Windows llama.cpp e exemplos PowerShell/Python. GPT-OSS 20B é acesso remoto via Groq; não está instalado localmente.

Ter um modelo instalado significa que conseguimos carregar seus pesos e executar sua função. Isso não significa 100% de acerto, ausência de limitações ou prontidão para qualquer tarefa/idioma. Os testes de instalação e o benchmark medem coisas distintas.

## Exemplos mínimos dos embeddings

Os exemplos abaixo são didáticos. O benchmark usa tokenização, média IDF, normalização, classificador e ambientes definidos no protocolo. Rodar uma consulta vetorial isolada não reproduz a classificação.

### GloVe

Execute no Python do ambiente Word2Vec no Ubuntu:

```python
from gensim.models import KeyedVectors

# O arquivo original não tem cabeçalho com contagem/dimensão.
vetores = KeyedVectors.load_word2vec_format(
    '/home/lucas/tcc-lab/GloVe/vectors.txt',
    binary=False, no_header=True,
)
print(vetores['computer'].shape)  # 50 números, não uma frase.
print(vetores.most_similar('computer', topn=5))
```

`most_similar` calcula proximidade entre vetores de palavras conhecidas. Não procura automaticamente um anime nem devolve uma probabilidade de spam. Uma palavra ausente gera erro de chave; é preciso verificar `palavra in vetores`.

### Word2Vec

```python
from gensim.models import Word2Vec

modelo = Word2Vec.load(
    '/home/lucas/tcc-lab/Word2Vec/models/text8-cbow-100d.model'
)
print(modelo.wv['computer'].shape)  # 100 dimensões.
print(modelo.wv.most_similar('computer', topn=5))
# Para Skip-gram, mudar somente para text8-skipgram-100d.model.
```

`wv` é a coleção de vetores de palavras. O objeto Word2Vec também contém informações de treinamento. CBOW e Skip-gram são pesos diferentes: mudar só o nome exibido sem mudar o arquivo não troca o modelo.

### fastText

No terminal Ubuntu:

```bash
printf 'computer\ncomputerrrr\n' | /home/lucas/tcc-lab/fastText/fasttext print-word-vectors /home/lucas/tcc-lab/fastText/result/fil9.bin
```

O programa lê uma palavra por linha e escreve palavra + 100 coordenadas. O segundo termo ilustra composição por subpalavras para uma grafia nova; a existência de vetor não demonstra que o significado foi aprendido corretamente. O benchmark mantém o processo aberto e se comunica por pipes, em vez de recarregar o binário para cada palavra.

### MiniLM

No ambiente `/home/lucas/tcc-lab/.venv-sentences`:

```python
from sentence_transformers import SentenceTransformer

modelo = SentenceTransformer(
    '/home/lucas/tcc-lab/SentenceTransformers/models/'
    'paraphrase-multilingual-MiniLM-L12-v2',
    device='cpu', local_files_only=True, trust_remote_code=False,
)
vetor = modelo.encode(
    ['No pic. Please re-send.'], normalize_embeddings=True
)
print(vetor.shape)  # (1, 384): uma mensagem, 384 coordenadas.
```

O Transformer considera contexto e produz um vetor de sentença. Para classificar, a regressão logística deve ter sido ajustada em vetores do mesmo modelo e nos rótulos de treino. Não reutilizar uma cabeça ajustada em GloVe com vetores MiniLM: dimensões e significado das coordenadas são diferentes.

## Exemplos dos geradores

Os scripts `04-iniciar-servidor.ps1` e `05-consultar-api-local.py`/`.ps1` documentam o uso manual no Windows. Para o benchmark usamos o runtime Linux equivalente. O `09-benchmark-geradores.py` mostra os comandos completos e parâmetros específicos de cada GGUF; não trocar raciocínio/amostragem depois de avaliar o teste.

Uma vez iniciado o servidor local na porta escolhida, o fluxo HTTP é:

```python
import json
from urllib.request import Request, urlopen

# Exemplo de estrutura: substituir a porta pela exibida no servidor.
url = 'http://127.0.0.1:8080/v1/chat/completions'
corpo = {
    'model': 'local',
    'messages': [{'role': 'user', 'content': 'Return exactly one word: hello'}],
    'max_tokens': 512,
    'temperature': 0.6,
}
req = Request(url, data=json.dumps(corpo).encode(),
              headers={'Content-Type': 'application/json'})
with urlopen(req, timeout=180) as resposta:
    objeto = json.load(resposta)
print(objeto['choices'][0]['message'].get('content'))
```

Llama, DeepSeek e Qwen compartilham essa forma de acesso; o arquivo GGUF carregado e as opções do servidor determinam qual modelo responde. Modelos com raciocínio podem gastar parte dos 512 tokens antes do conteúdo final. Uma resposta vazia não prova que o servidor falhou: verificar `finish_reason`, raciocínio e orçamento.

Para Groq, o SDK oficial instalado no ambiente separado permite:

```python
from pathlib import Path
from groq import Groq

# Ler localmente; nunca imprimir a chave ou incluí-la em código/versionamento.
chave = Path('/mnt/c/tcc-lab/secrets/groq-api-key.txt').read_text().strip()
cliente = Groq(api_key=chave)
resposta = cliente.chat.completions.create(
    model='openai/gpt-oss-20b',
    messages=[{'role': 'user', 'content': 'Return exactly one word: hello'}],
    reasoning_effort='low', max_completion_tokens=512,
)
print(resposta.choices[0].message.content)
```

Esse exemplo adicional gera uma nova chamada se executado. Para o benchmark, usar somente o script com controle de cota e orçamento, não um loop irrestrito com o exemplo. O cliente do benchmark usa httpx depois do diagnóstico de transporte; isso não altera o endpoint ou os pesos do modelo. Sem conta/chave ativa e cota disponível, a API não funciona; os modelos locais continuam utilizáveis.

## Como refazer a análise sem gastar tokens

Reexecutar `12-avaliar-comparacao.py` no ambiente `.venv-sentences` lê predições já gravadas e recalcula métricas. Não envia SMS à Groq. `13-gerar-relatorio.py`, no runtime de documentos Windows, lê o JSON agregado e produz tabelas, gráficos, Markdown, HTML e PDF. O gerador exige que todos os 13 resultados estejam completos.

Para repetir a inferência, abrir outra rodada com saídas separadas e registrar mudanças. O treino da cabeça logística faz parte do script de classificação; os pesos pré-treinados dos embeddings permanecem congelados. Os arquivos brutos desta rodada não devem ser editados para melhorar resultados.
