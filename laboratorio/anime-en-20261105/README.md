# Comparativo completo de anime em inglês - 05/11/2026

Concluído após o comparativo SMS. Relatórios [HTML](../../output/comparacao-anime-en/relatorio-anime-en.html), [PDF](../../output/comparacao-anime-en/relatorio-anime-en.pdf), [CSV](../../output/comparacao-anime-en/comparacao-anime-en.csv) e [guia de métricas](METRICAS_EXPLICADAS.md). Não houve treinamento ou ajuste dos pesos dos modelos nesta rodada.

## Dados e cenários

Kaggle Anime Recommendation Database 2020, Hernan Valdivieso, versão 7; 16.214 registros no CSV com sinopses, 8.409 elegíveis após filtros, amostra congelada de 1.000. São 24 consultas em inglês, duas formulações de 12 intenções. Input de documento: primeiras 80 palavras da sinopse. Títulos, notas, gêneros e popularidade não entram na representação ou no prompt. Os gêneros servem como referência automática de relevância: não são julgamentos humanos de preferência.

As intenções cobrem gêneros únicos, combinações e exclusões. O teste é um diagnóstico de recuperação por conteúdo e reordenação; não valida ainda anime-para-anime personalizado nem usa o histórico real do usuário. Não misturar seus resultados com o piloto menor anterior, de consultas/desenhos PT/EN preparados com IA.

## Resultados que orientam a próxima fase

- No catálogo completo: MiniLM teve nDCG@5 0,3886; o melhor estático pontual foi Word2Vec Skip-gram, 0,3443, seguido de fastText, 0,3199. BM25 ficou em 0,3160 e deve continuar como baseline forte de RI. Os intervalos são amplos, com somente 12 famílias de intenção.
- Na mesma lista de cinco candidatos: fastText 0,6126; Qwen sem raciocínio 0,6167; GPT-OSS 0,6453. São valores próximos descritivamente, não prova de equivalência. Outras métricas, como Hit@1, diferem.
- Prioridade provisória do produto: Word2Vec Skip-gram já preparado, usando RI e pesos determinísticos. MiniLM/LLMs não são elegíveis para o produto final confirmado; continuam comparadores.
- Qwen thinking, Llama e DeepSeek tiveram muitas saídas fora do formato. O relatório separa respostas brutas e fallback TF-IDF. Isso avalia esse pipeline de saída livre e o orçamento de 512 tokens, não a capacidade máxima das famílias.

## Parâmetros essenciais

Seed 20261105; uma execução por configuração; CPU quatro threads, um modelo local por vez. Estáticos: média IDF do catálogo e L2, sem alteração dos vetores. TF-IDF: unigramas/bigramas, TF sublinear e L2. BM25 k1=1,2, b=0,75 e IDF positivo especificado no protocolo. MiniLM conserva max_seq_length 128: 100/1.000 documentos ultrapassaram esse limite, máximo 164 tokens, e foram truncados pelo encoder. Os mesmos trechos originais de 80 palavras foram oferecidos a todos.

Geradores locais: contexto 2.048, saída máxima 512, seed por índice. Auditoria antes das predições: maior prompt renderizado 707 tokens no Llama, 683 no DeepSeek, 689 no Qwen thinking e 693 no non-thinking; todos cabem com a reserva de saída e margem. Qwen thinking usa temperatura/top_p 0,6/0,95; non-thinking 0,7/0,8; ambos top_k20, min_p0, presença1,5. Llama e DeepSeek 0,6/0,95, raciocínio off/on respectivamente. GPT-OSS low, 0,6/0,95. Os modos Qwen mudam também a amostragem, não apenas o raciocínio. Ver [protocolo completo](PROTOCOL.md).

Groq: 25 chamadas nesta rodada, incluindo warmup sintético; 17.915 tokens conhecidos. SMS havia usado 36.886, além de 93 do diagnóstico de transporte. Sem provedor pago, upgrade ou pagamento configurado pelo código. Cota/conta mantida Free conforme escolha do usuário. Tempos incluem rede e serviço; pausas de cota são separadas, e RAM remota permanece desconhecida.

## Evidências e reprodução

`data/freeze.json` e `data/shortlists-freeze.json`: hashes de dados e candidatos. `data/frozen-code`: snapshot anterior à primeira recuperação. Mudanças posteriores de apresentação/QA não alteraram prompts, qrels ou predições; os fontes atuais também ficam preservados no pacote de entrega. `results/retrieval`: scores completos, tempos, índices reutilizáveis e RSS. `results/reranking`: cada requisição/resposta, auditoria de contexto e metadados. `results/evaluation/comparison.json`: resultados completos, cenários, intervalos e diferenças pareadas. `qa.json`: conferência de 720 linhas de ranking contra scikit-learn, além de consistência do parser e hashes.

Para reavaliar sem inferência, executar `08-evaluate.py` e `12-qa.py` no ambiente Linux `.venv-sentences`. Para gerar apresentação, executar `11-report.py` no runtime Windows de documentos com NumPy, Matplotlib e ReportLab. Isso não envia novas chamadas nem treina modelos. Os scripts de inferência preservam resultados concluídos; repetir um experimento exige uma pasta de rodada separada.

Índices persistidos: `.npy` para vetores de documento; matriz esparsa e vetorizador do TF-IDF; contagens BM25; configurações com IDs, IDF e origem. Não são modelos ajustados com os julgamentos do teste. A consulta de um anime novo na aplicação futura exigirá obter seu texto e agregá-lo com os mesmos vetores/IDF; pesquisar só o nome não equivale a representar sua sinopse.
