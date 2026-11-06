# Roteiro para a reunião das 15h - 29/10/2026

**Proposta:** usar MiniLM multilíngue como encoder principal do protótipo de busca do TCC; comparação ampla como IC.

## Relato em um minuto

Instalações verificadas: GloVe, fastText, Word2Vec CBOW/Skip-gram e MiniLM multilíngue. Rare Words resolvido: 2.034 pares, Spearman 0,4177, com origem alternativa documentada. Nenhum GPT/Llama/DeepSeek gerador instalado.

Piloto concluído: 39 animes reais, 58 consultas em 29 intenções e julgamentos congelados antes dos rankings. Cenário principal: consultas em português e descrições inglesas. MiniLM obteve nDCG@5 0,805 e Hit@1 47/58 (81,0%). Nas paráfrases, Hit@1 cai para 18/29: ainda há erros relevantes.

**Limitação indispensável:** descrições, consultas e relevâncias preparados com IA, sem validação humana independente. É evidência exploratória para uma decisão técnica, não resultado científico final nem benchmark oficial.

## Justificativa da escolha

MiniLM atende ao requisito entre idiomas e já roda localmente em CPU. Modelos estáticos ingleses não foram alinhados ao português; fastText gera vetores fora do vocabulário, mas isso não equivale a tradução. Em inglês, Skip-gram text8 teve nDCG 0,739 e fastText 0,723, portanto não devem ser declarados ruins ou descartados da IC.

## Decisões para discutir

- O TCC é busca semântica por descrição ou inclui personalização por usuário?
- Aprovar o encoder como candidato inicial e delimitar o protótipo.
- Definir fonte de sinopses reais, consultas humanas e avaliação cega.
- Tratar textos acima de 128 tokens e medir latência com catálogo pré-indexado.
- Separar implementação/avaliação do sistema (TCC) da comparação controlada de modelos (IC).

## Não afirmar

“MiniLM tem 80,5% de acurácia”; “o sistema final está pronto”; “fastText é sempre pior”; “LLMs perderam o teste”. nDCG é uma métrica de ranking e geradores não foram comparados.
