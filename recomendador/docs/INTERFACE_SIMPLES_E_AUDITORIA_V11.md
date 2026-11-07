# Interface simples e auditoria das representações — 06/11/2026

## Decisão de produto

A página inicial passou a atender duas tarefas: **encontrar animes parecidos sem informar preferências** e **recomendar considerando os gostos do usuário**. Na segunda, é possível importar a lista pública do AniList ou escolher gêneros, temas e favoritos, sem notas obrigatórias. As recomendações gerais continuam acessíveis; a lista de descobertas distingue obras ainda não iniciadas, inclusive planejadas.

Foi fixada uma configuração na página inicial: **Word2Vec Skip-gram text8, 100 dimensões; 50% similaridade da sinopse e 50% temas; personalização padrão 35%; sem bônus comunitário experimental**. Isso é uma escolha provisória de engenharia apoiada no histórico de experimentos, não uma declaração de superioridade universal. As preferências pessoais e a escala relativa de notas foram preservadas.

O visitante não escolhe embeddings, BM25, k1, bônus, pesos numéricos ou métricas. Cards não exibem scores, fórmulas ou tabelas de parcelas. Uma explicação curta apresenta temas compartilhados e interesses positivos encontrados; a sinopse completa fica disponível. Quando não há perfil utilizável, o aplicativo informa isso e apresenta recomendações gerais em vez de fingir personalização.

O modo puro continua ignorando histórico, notas, exclusões e favoritos pessoais. Guardar um favorito não altera esse ranking; ele ajuda quando o usuário escolhe personalização. O visitante não precisa criar conta no projeto.

### Área de pesquisa separada

`pesquisa.html` preserva os controles técnicos, parâmetros, auditorias, exportações e preparação de julgamentos humanos. `laboratorio.html` permite os quatro embeddings; `experimentos.html` preserva o experimento BM25/comunidade anterior, identificado por corpus e data. O Atlas fica em `dataset.html`. São acessíveis no rodapé, em **Sobre o projeto e pesquisa**.

As duas interfaces compartilham o mesmo motor. O modo simples força sua configuração no código de requisição; não depende apenas de esconder um seletor. A construção é reproduzível por `python scripts/build_site.py`, que gera páginas equivalentes para backend local e hospedagem estática.

## Dataset ampliado

O snapshot público cresceu de **3.053 para 3.413 obras**, adicionando **360 (11,8%)**. Há **3.409 sinopses não vazias**, quatro documentos sem vetor utilizável e **13.652 vetores** no SQLite público, quatro por obra. Nota ponderada e média estão disponíveis em 3.412 obras. Ausências continuam nulas.

Foram usados oito cenários explícitos: Madoka Magica, Princess Principal, Gunslinger Girl, Flip Flappers, Frieren, A Place Further than the Universe, Sound! Euphonium e Non Non Biyori. Cada cenário consulta até 20 obras relacionadas e uma única página de até 50 descobertas por gênero ou tag. Reutilizamos os metadados já existentes; não fizemos nova atualização completa das obras coletadas minutos antes. A operação de rede levou aproximadamente 45 segundos, de 21:29:44 a 21:30:29 em 06/11/2026, horário de São Paulo.

O cenário Girls With Guns retornou zero descobertas novas na página consultada; não inventamos 50 resultados nem abrimos um laço de paginação. As obras relacionadas desse cenário ainda acrescentaram quatro títulos. O registro de todos os cenários e IDs está em [use-case-expansion-v11.json](../data/use-case-expansion-v11.json); o código está em `expand_use_cases.py` e requer `--execute`.

A fonte continua sendo exclusivamente AniList para metadados de obras. O corpus das palavras é outra coisa: text8 ou fil9, conforme o artefato estático. A autorização para um catálogo integral segue sem resposta; o crescimento é delimitado por uso, não um espelhamento progressivo de todo o serviço. O banco pode crescer, mas aumentar o número de obras sem controle de cobertura, qualidade e autorização não garante recomendações melhores.

## O que exatamente são nossos vetores?

### Sinopse: vetor denso de conteúdo textual

Para cada sinopse completa, aplicamos NFKC, letras minúsculas e tokenização. Cada palavra conhecida possui um vetor estático previamente aprendido. O programa não aprende novos vetores.

```python
# Esquema equivalente ao cálculo real de engine.vector:
tokens = tokenize(sinopse_inteira)
conhecidos = [p for p in tokens if p in vetores_das_palavras]
pesos = [idf.get(p, idf_de_termo_novo) for p in conhecidos]
documento = media_ponderada([vetores_das_palavras[p] for p in conhecidos], pesos)
documento = documento / norma_l2(documento)
```

O IDF é `ln((N+1)/(df+1))+1`. A repetição de uma palavra participa da média; não há corte por quantidade de palavras. O resultado principal tem 100 números. Comparamos documentos pelo produto escalar dos vetores normalizados, equivalente ao cosseno. A transformação `(cosseno+1)/2` é um índice no intervalo 0–1, não uma probabilidade.

### Tags: vetor esparso de atributos

Cada dimensão corresponde à **identidade de uma tag**, e não a uma palavra da sinopse. No componente temático de comparação entre obras, tags com rank pelo menos 50 recebem peso `(rank/100) × IDF_da_tag`; as demais não entram nesse componente. Comparamos esses vetores esparsos por cosseno. Duas tags distintas não são automaticamente consideradas sinônimas. Não passamos o nome das tags pelo Word2Vec.

### Gêneros: atributos binários

Um gênero está presente ou ausente. A comparação é Jaccard: quantidade de gêneros em comum dividida pela quantidade na união. Esse é um cálculo sobre atributos binários, não sobre embeddings linguísticos. O componente temático é **85% cosseno das tags + 15% Jaccard dos gêneros**.

Sinopse e temas são combinados depois; não misturamos um vetor denso de 100 dimensões com uma lista de tags de tamanho variável como se fossem o mesmo espaço. O perfil tem seus próprios vetores positivos/negativos de texto e pesos temáticos. O limite de 12 temas inferidos refere-se à síntese temática dominante; **não é um limite de obras ou notas usadas** nos centroides.

## Auditoria independente

O script `scripts/audit_representations.js` reconstrói os vetores a partir dos arquivos públicos de palavras e do texto completo. Não chama a função de codificação original. Também reconta o IDF, verifica matrizes dos quatro modelos e reconstrói a comparação esparsa de temas em 3.000 pares.

| Verificação no corpus de 3.413 obras | Resultado |
|---|---:|
| Sinopses recodificadas independentemente | 3.413 |
| Maior diferença entre vetor principal armazenado e recodificado | 0 |
| Maior diferença no IDF de palavras | 8,88 × 10⁻¹⁶ |
| Maior erro de norma L2 entre os quatro modelos | 2,81 × 10⁻⁸ |
| Maior diferença no cosseno esparso das tags | 1,12 × 10⁻¹⁶ |
| Diferença no Jaccard dos gêneros | 0 |
| Cobertura de ocorrências de palavras pelo modelo principal | 94,30% |

Essa cobertura conta ocorrências no conjunto todo; é diferente da média de cobertura por documento, aproximadamente 93,69%. fastText tem cobertura maior graças às subpalavras; isso não garante automaticamente maior relevância. Os quatro documentos vazios/sem vetor são explicitados no JSON e excluídos como candidatos semânticos.

Resultados completos: `output/auditoria-v11/representacoes.json` e `online/lab/representation-audit.json`. O workflow repete a auditoria antes da publicação.

### Limitação importante: concentração dos vetores

Em 2.996 pares aleatórios com vetores válidos, o cosseno textual teve percentis aproximados **P5=0,692; mediana=0,905; P95=0,952**. O sorteio não fornece rótulos humanos de irrelevância: é uma distribuição de pares aleatórios, que pode incluir obras relacionadas. Mesmo assim, a concentração elevada mostra que a média desses embeddings separa documentos em uma faixa estreita.

Isso não é uma falha aritmética, mas uma limitação da representação e do domínio do treinamento. A média não preserva ordem das palavras, negação, relações entre personagens ou estrutura narrativa. Um score alto não significa compreensão do enredo. A maior escala dos scores não deve ser corrigida artificialmente para agradar à expectativa de porcentagens.

Foi testado separadamente subtrair a média dos vetores documentais do corpus e renormalizar. É uma transformação aritmética exploratória, sem classificador ou ajuste supervisionado; não foi incorporada ao produto, pois o piloto julgado não mostrou melhora. Caso seja estudada novamente, deve ser descrita como representação alternativa e avaliada em novas consultas.

## Correções encontradas

1. **Normalização Unicode:** Python utilizava `casefold`, navegador usava minúsculas. A auditoria encontrou uma divergência em `reinweiß`, fora do vocabulário principal. Padronizamos NFKC + minúsculas; reconstruímos IDF e artefatos. Não era responsável por grandes mudanças no ranking, mas impedia equivalência completa do vocabulário.
2. **Referência sem vetor:** o backend já recusava sinopse sem vetor; o núcleo JavaScript agora também recusa, em vez de produzir uma lista com contribuição textual sem evidência. Vetores incompatíveis ou não finitos também geram erro explícito.
3. **Marca de conteúdo adulto em entradas dinâmicas locais:** a materialização Python agora preserva `isAdult` e verifica a marca na seleção. Isso fecha uma diferença de proteção frente ao navegador; não altera a decisão de manter Ecchi visível.
4. **Contexto de estudos humanos:** novas exportações incluem filtros e intensidade pessoal efetivamente usados, além do corpus. Arquivos antigos não adquirem retroativamente informações que não foram exportadas.
5. **Explicações do perfil:** a interface simples apresenta interesses positivos como motivos de afinidade; interesses negativos encontrados não são descritos como se fossem preferências positivas.

Validação: 27 testes Python, 72 comparações numéricas de referência entre linguagens, 135 comparações experimentais, teste de modo puro, proteção de dimensões e vetores ausentes, sintaxe JavaScript, integridade de SQLite e arquivos públicos. Uma execução inicial de testes coincidiu com a reconstrução do SQLite; foi repetida após concluir a escrita. Não tratamos essa corrida de arquivos como defeito no ranking.

## Avaliação humana e escolha do modelo

O arquivo recebido de Madoka foi preservado. As três respostas adicionais do chat foram registradas numa cópia local, com proveniência; a resposta de preferência ainda ausente permaneceu ausente. Foram recalculadas métricas independentemente da interface. Uma nota humana 2 ou 3 conta como relevante; nDCG usa ganho `2^nota−1` e desconto `log2(posição+1)`.

Além das estratégias anteriores, comparamos os quatro artefatos estáticos no mesmo conjunto de 18 candidatos com semelhança completamente julgada. As sinopses congeladas do arquivo foram preservadas, incluindo uma que mudou no AniList entre coletas. Utilizamos IDF comum do novo corpus e metadados comuns da referência. Código: `scripts/compare_judged_static.py`. Os resultados com opiniões pessoais ficam em arquivo local separado, fora do repositório público.

Esse piloto não isola apenas algoritmo: dimensões e corpus de treinamento diferem. O conjunto de candidatos foi selecionado por sistemas anteriores e uma consulta/um avaliador não validam o modelo para todo o domínio. A recomendação prática é manter Skip-gram na interface simples e continuar testando outros casos na área de pesquisa. Novos pesos/modelos devem ser avaliados em consultas não usadas na sua escolha.

## LLM: curiosidade separada

`scripts/pilot_local_llm.py` utiliza os GGUFs já instalados de Qwen3-0.6B Q8_0 e Llama 3.2 1B Instruct Q4_K_M, com llama.cpp b12110 local, CPU, quatro threads, raciocínio desligado, contexto 8.192 e até 512 tokens de resposta. Não chama API paga, não envia notas nem perfil e não é importado pelo aplicativo.

O teste mantém os 18 candidatos de semelhança do estudo de Madoka. Envia sinopses completas, gêneros e tags com rank pelo menos 50, sem notas humanas ou scores de modelos. A primeira serialização excessiva dos atributos consumiu mais de 14 mil tokens e excedeu dez minutos; substituímos objetos repetitivos por pares nome/rank, preservando a sinopse inteira. Não cortamos texto silenciosamente.

O protocolo inicial pede uma permutação dos 18 IDs em JSON e valida quantidade, unicidade e pertencimento. Qwen e Llama produziram repetições; essas saídas são rejeitadas e não recebem uma precisão fictícia. Uma variante de diagnóstico pede uma nota por ID em um objeto JSON e aplica ordenação determinística, para distinguir dificuldade no contrato de saída de relevância semântica. Variantes e tempos são registrados separadamente; não são uma correção silenciosa do resultado anterior.

Pequenos LLMs quantizados na CPU não representam todos os LLMs modernos. Uma lista curta pré-selecionada não equivale a busca em 3.413 documentos, e latência de reranking não deve ser comparada como se tivesse o mesmo trabalho da recuperação completa. Nenhum desses LLMs entra na versão final.

## Próximas melhorias com maior utilidade

- Avaliar várias referências e mais de um usuário, separando semelhança e preferência; manter um conjunto final que não orientou ajustes.
- Medir cobertura por gênero, tag, período e formato, além do tamanho bruto do dataset; priorizar lacunas e inéditos nos cenários usados.
- Usar relações oficiais de franquia, futuramente, para limitar sequências repetidas e evitar recomendar continuação sem apresentar a primeira temporada. A heurística por nome continua apenas experimental.
- Avaliar diversidade e novidade junto de precisão. Preencher dez vagas com obras fracas não constitui melhora.
- Preservar a interface simples enquanto novos métodos são testados na área de pesquisa.

Fontes: [termos oficiais AniList](https://github.com/AniList/docs/blob/master/docs/guide/terms-of-use.md), [Qwen oficial](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF), [avaliação de rankings — Stanford](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html). Parâmetros e transformações descritos aqui são decisões do experimento, não prescrições dos fabricantes.
