# Embeddings de sentenças: MiniLM multilíngue

Em 29/10/2026 foi instalado e testado `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, modelo dos autores do Sentence Transformers. Ele representa sentenças em vetores densos de 384 dimensões e inclui português entre os idiomas declarados no model card. É um encoder contextual, não um LLM gerador de respostas.

## Fontes e ambiente

- [Instalação oficial Sentence Transformers](https://www.sbert.net/docs/installation.html).
- [Model card dos autores](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
- [Instalação oficial PyTorch](https://pytorch.org/get-started/locally/).

Criado o ambiente `/home/lucas/tcc-lab/.venv-sentences`, usando o CPython 3.12.16 separado já preparado. PyTorch foi instalado pelo índice CPU oficial, evitando dependências CUDA que não seriam usadas neste teste. Não foi configurado backend de GPU.

Comandos efetivamente usados na instalação inicial:

```bash
/home/lucas/.local/tcc-python-3.12.16/bin/python3.12 -m venv ~/tcc-lab/.venv-sentences
~/tcc-lab/.venv-sentences/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
~/tcc-lab/.venv-sentences/bin/python -m pip install sentence-transformers
```

Ambos os comandos pip também receberam `--report`, para preservar origem e hashes. Versões resolvidas: PyTorch **2.15.0+cpu**, Sentence Transformers **6.2.0**, Transformers **5.21.1**, Hugging Face Hub **2.3.0** e NumPy **2.5.4**. Dependências completas e relatórios em `manifests/sentence-transformers/`; saída da instalação em `26-sentence-transformers-instalacao.txt`.

O script `17-sentencas-instalar.sh` fixa as versões principais observadas para reprodução. As versões transitivas exatas estão no arquivo de requisitos. O script de reprodução foi preparado depois da instalação inicial; não é descrito como uma segunda instalação executada.

## Aquisição dos pesos e código de teste

`15-sentencas-minilm.py` consultou a revisão do repositório dos autores e a preservou: **e8f8c211226b894fcb81acc59f3b34ba3efd5f42**. A revisão agora é o default fixado para reproduzir a execução, podendo ser alterada explicitamente por `MODEL_REVISION` em um novo experimento.

`snapshot_download` recebeu a revisão e filtros para pesos safetensors, configurações e tokenizer. Não foram baixadas exportações ONNX/OpenVINO nem uma segunda cópia de pesos em formato pickle. O cache fica em `~/tcc-lab/SentenceTransformers/cache`; uma versão autocontida salva pela biblioteca fica em `~/tcc-lab/SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2`. O arquivo principal de pesos ocupa 470.637.416 bytes, além do tokenizer e das configurações.

O teste carrega o snapshot em CPU, com `trust_remote_code=False`, e executa `encode` nas duas frases do model card. Verifica formato e números finitos, salva com `save_pretrained`, recarrega com `local_files_only=True` e confere que os embeddings permanecem próximos numericamente. A origem e o hash de cada arquivo salvo constam no JSON da execução.

Um segundo exemplo, de autoria do laboratório, compara uma consulta em português com três descrições sintéticas. Não é uma base de anime nem um benchmark público. O texto sobre criança/cão ficou em primeiro lugar, conforme o teste didático; isso não estabelece qualidade geral ou um limiar de relevância.

`16-sentencas-executar.sh` organiza a execução, logs, versões, tempo/memória e código de saída. `06-exportar-registros.sh` copia as evidências concluídas para a documentação e registra o diretório do modelo no manifesto atual.

## Resultados observados

Execução `sentences-minilm-20261029T135750Z-FKRSao`, **código zero**. Log: `30-sentencas-minilm.txt`; evidências completas em `logs/execucoes/`.

| Verificação | Resultado |
|---|---|
| Duas entradas oficiais | Matriz 2 × 384, finita e com vetores não nulos |
| Dispositivo | CPU, quatro threads configuradas |
| Salvar e recarregar localmente | Passou; embeddings próximos com tolerância registrada no código |
| Consulta didática em português | Documento esperado em primeiro entre três candidatos |
| Limite de entrada observado | 128 tokens |
| Tempo do encode de duas frases | Cerca de 0,043 s nesta execução |
| Runner completo | 1 min 2,95 s, incluindo download, carregamento, gravação e verificações |
| Pico de RSS do runner | 1.760.632 KiB, aproximadamente 1,68 GiB |

O tempo curto do encode não é um benchmark controlado: não houve séries de aquecimento, repetições, distribuição de tamanhos ou avaliação de concorrência. Os escores do exemplo são cossenos, não probabilidades de relevância.

## Uso local posterior

No Ubuntu, ativar `.venv-sentences` e carregar o diretório salvo:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(
    '/home/lucas/tcc-lab/SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2',
    device='cpu', local_files_only=True,
)
vetores = model.encode(['Uma descricao curta de exemplo.'])
```

Para sinopses maiores, definir e documentar uma estratégia de divisão/agregação ou selecionar outro modelo. O limite de 128 é de tokens do tokenizer, não de palavras ou caracteres. Sem tratar esse limite, partes de sinopses podem ser truncadas. Essa decisão e a avaliação de relevância no domínio anime continuam pendentes; não há modelo de recomendação homologado a partir destes testes funcionais.
