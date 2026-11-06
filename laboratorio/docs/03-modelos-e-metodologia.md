# Modelos candidatos e metodologia para o TCC

## O que significa instalar e usar

Há três operações diferentes: instalar o programa; baixar pesos já treinados; treinar novos pesos com um corpus. Os exemplos GloVe e fastText escolhidos fazem a primeira e a terceira operações. O download do código-fonte sozinho não instala um modelo pronto. A instalação precisa incluir dependências, compilação e execução verificadas.

Nos embeddings estáticos, uma palavra tem uma representação independente da frase em que aparece. fastText utiliza partes da palavra para compor vetores e consegue representar termos novos por subpalavras. Isso é pertinente a nomes próprios no catálogo, mas não garante bons vetores para nomes japoneses ou conhecimento sobre animes.

## Quais modelos adicionais considerar

| Candidato | Papel no estudo | Recomendação |
|---|---|---|
| Word2Vec, Skip-gram e CBOW | Embeddings de palavras; contraponto ao treinamento por coocorrências do GloVe e às subpalavras fastText | Próxima inclusão prioritária |
| Doc2Vec | Representação de documentos, como sinopses completas | Opcional; não é um embedding estático de palavra equivalente aos três anteriores |
| TF-IDF + cosseno | Baseline lexical já previsto nos materiais AniRec | Manter; não é LLM nem embedding neural |
| Sentence Transformers | Embeddings de sentenças para busca semântica | Candidato contextual mais diretamente alinhado a recuperar sinopses |

Para Word2Vec e Doc2Vec, a implementação proposta é **Gensim**, seguindo a documentação oficial dessa biblioteca. Isso significa usar uma implementação reconhecida do algoritmo, não atribuir Gensim aos autores originais de Word2Vec. O conjunto `common_texts` dos exemplos serve para aprender a API, mas é pequeno demais para alegar qualidade científica. Na continuação, Gensim foi instalado e Word2Vec CBOW/Skip-gram foram testados no corpus Lee, conforme `06-word2vec.md`. O MiniLM multilíngue também foi instalado e testado, conforme `08-embeddings-sentencas.md`; Doc2Vec permanece sem modelo treinado e sem teste específico.

Fontes: [Word2Vec/Gensim](https://radimrehurek.com/gensim/models/word2vec.html), [Doc2Vec/Gensim](https://radimrehurek.com/gensim/models/doc2vec.html), [Sentence Transformers](https://www.sbert.net/docs/quickstart.html).

## LLMs que podem ser usados nesta máquina

**Inferência local de modelos pequenos é plausível; ainda não foi medida.** A análise abaixo parte do hardware observado e da documentação dos modelos. Não é certificação de instalação nem garantia de velocidade. Treinar um LLM moderno do zero está fora da proposta prática deste computador. Inferência, extração de embeddings e ajuste fino são operações distintas, com requisitos diferentes.

| Família | Candidato concreto | Avaliação para este computador |
|---|---|---|
| GPT por serviço OpenAI | Modelos hospedados acessados por API | Pode ser integrado via internet e credenciais; o modelo permanece remoto. Não houve chamada nem custo de API nesta sessão |
| GPT com pesos locais | GPT-2 | Possui código e pesos públicos oficiais; alternativa histórica e pequena. Não o escolheria como representante da qualidade dos GPT atuais |
| OpenAI gpt-oss | gpt-oss-20b | Não priorizar aqui: o guia descreve uso de MXFP4 e aproximadamente 16 GB; há apenas 13,9 GiB utilizáveis e parte é necessária ao Windows. O cenário deste PC não foi validado |
| Llama | Llama 3.2 1B ou 3B Instruct | Bons candidatos para testar inferência em CPU, preferencialmente com quantização documentada e contexto curto. Há licença própria e condições de acesso aos pesos |
| DeepSeek | DeepSeek-R1-Distill-Qwen-1.5B | Candidato pequeno; é uma destilação baseada em Qwen. Não equivale ao DeepSeek-R1 completo de 671B |
| Alternativa | Qwen2.5-0.5B-Instruct | Modelo pequeno para começar a aprender inferência; qualidade precisa ser avaliada no objetivo real |

O model card do [Llama 3.2](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/MODEL_CARD.md) informa variantes 1B/3B e português entre os idiomas suportados. O [README DeepSeek-R1](https://github.com/deepseek-ai/DeepSeek-R1) disponibiliza a variante destilada de 1,5B e recomenda parâmetros de uso. Não assumir que qualquer versão chamada DeepSeek cabe nesta máquina.

As opções GPT precisam ser distinguidas: [API OpenAI](https://developers.openai.com/api/docs/quickstart), [GPT-2 oficial](https://github.com/openai/gpt-2) e [guia gpt-oss](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers). Não há credencial necessária para esta análise documental. Para o [Qwen pequeno](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct), seguir o model card dos próprios autores.

Como ordem de grandeza, só os pesos de 1,5 bilhão de parâmetros em FP32 ocupam cerca de 6 GB decimais, antes de cache, buffers e sistema operacional. Quantização reduz parte desse custo; o consumo total depende também do contexto, precisão do cache e runtime. Estimativas por tamanho de pesos não substituem medição.

Uma opção de runtime local posterior é [llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md), que documenta CPU/Windows. O runtime é um projeto independente dos autores de Llama/DeepSeek. Usar um GGUF de terceiros muda a proveniência do artefato: registrar repositório, revisão, precisão, licença e procedimento de conversão. A rota estritamente centrada nos autores começa pelos pesos e exemplos dos model cards; conversão/quantização deve ser uma etapa explícita.

Ainda não foram baixados pesos LLM, instalados runtimes ou aceitas licenças pelo usuário. Não há um teste LLM concluído. Os candidatos acima permitem escolher um experimento pequeno depois da etapa estática.

## Como relacionar isso ao catálogo de animes

Os arquivos existentes do AniRec descrevem sinopses, gêneros, tags e ranqueamento baseado em conteúdo. Proposta para a fase seguinte, ainda sem execução:

1. Congelar um catálogo e sua origem, data de coleta, licença e idioma. Preservar os dados brutos e um hash da versão.
2. Definir consultas e julgamentos de relevância antes de comparar modelos. Tags compartilhadas podem ser um sinal auxiliar, mas não equivalem automaticamente à relevância humana.
3. Fixar treinamento/validação/teste e impedir que ajustes usem os julgamentos de teste. Documentar deduplicação e relações entre franquias.
4. Comparar TF-IDF, Word2Vec, GloVe e fastText com o mesmo texto disponível, filtros e protocolo. Para embeddings de palavras, declarar como obter um vetor da sinopse: média simples ou média ponderada por IDF. Essa agregação é uma decisão nossa.
5. Avaliar separadamente um bi-encoder de sentenças; se incluir LLM, definir uma função concreta, como reordenar uma lista de candidatos por prompt fixado.
6. Medir nDCG@k, Precision@k e Recall@k com relevância documentada, além de latência, memória, cobertura de vocabulário e armazenamento. Fixar k e os critérios antes de inspecionar resultados finais.

Não comparar a acurácia de analogias GloVe com Spearman/RW fastText como se fossem a mesma métrica. Os exemplos oficiais validam uso e instalação; a comparação científica exige um protocolo comum. Um gerador que responde nomes de memória também pode alucinar itens; um teste de recuperação deve devolver identificadores do catálogo e medir relevância verificável.

Multithreading e aleatoriedade podem produzir diferenças entre treinos mesmo com o mesmo código. Guardar parâmetros, versões, sementes quando expostas pelo programa e repetir execuções quando o objetivo passar a ser comparação estatística. Ainda não há evidência experimental de qual método é melhor para anime.
