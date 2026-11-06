# Exibição de tags e estatísticas comunitárias — 06/11/2026

## Preferências: ocultação padrão de temas adultos/sexuais

O editor de preferências agora omite, por padrão, tags marcadas `isAdult=true`, categorias contendo `Sexual Content` e uma lista explícita de exceções na interface (por exemplo, Nudity). Não usamos uma busca genérica pela palavra “sex” nas definições: ela ocultaria indevidamente orientações e temas de romance.

Yuri, Boys' Love, romance, temas LGBTQ+ e **Ecchi continuam visíveis**. Ecchi foi mantido por solicitação expressa do usuário; Hentai permanece oculto. No snapshot de taxonomia com 430 tags e 19 gêneros, o padrão mostra 356 tags e 18 gêneros. As categorias do seletor também respeitam a visibilidade.

A opção discreta fica em **Opções de exibição → Mostrar temas adultos/sexuais**. A ativação vale durante a abertura atual do editor; ao reabrir, o padrão volta a ocultar. A busca não contorna o filtro. O usuário pode revelar todas as 430 tags. Preferências existentes são preservadas: se uma escolha salva estiver oculta, aparece uma contagem, sem remoção silenciosa de dados.

É uma política de **apresentação do seletor**, não uma nova política de ranking ou mudança no conteúdo do catálogo. O catálogo público já exclui obras com `isAdult=true`; Ecchi não é equivalente a essa marcação. O modo puro e os pesos do ranking continuam iguais.

QA de interface: categoria Sexual Content ausente no modo padrão; busca de Nudity sem resultado até a ativação; Yuri disponível; ativação revela 430 tags; desativação volta a ocultar; reabrir o diálogo restaura o padrão; Ecchi permanece acessível no seletor de gêneros. O teste foi feito sem alterar o perfil pessoal.

## O que significam as estatísticas do AniList

Fonte oficial: https://docs.anilist.co/reference/object/media

| Exibição no AniList | Campo GraphQL | Significado |
|---|---|---|
| Weighted Score | `averageScore` | Média ponderada das notas da comunidade, fornecida pelo AniList |
| Mean Score | `meanScore` | Média das notas da comunidade |
| Popularity | `popularity` | Número de usuários que têm a obra em sua lista; não equivale ao número de avaliações nem ao número de espectadores que concluíram a obra |
| Favorites | `favourites` | Número de usuários que favoritaram a obra |

As notas comunitárias são apresentadas na escala de 0 a 100. `81` corresponde à apresentação 81/100 (ou 8,1/10); não é 81% de probabilidade de o usuário gostar. A documentação de referência descreve `averageScore` como ponderado, mas não fornece nessa definição a fórmula de ponderação: não devemos inventar pesos nem presumir um cálculo bayesiano específico.

Os valores ponderado e médio podem aparecer iguais por proximidade e/ou apresentação arredondada; a igualdade visual não prova que os cálculos sejam idênticos. `&#x20;` no texto copiado representa um espaço HTML, não parte da nota.

## Situação real do código nesta atualização

- O cliente Python (`anilist_client.py`, `MEDIA_FIELDS`) solicita **averageScore**. A resposta bruta é preservada em `media.raw_json` no SQLite operacional. Essa informação não tem coluna na tabela tratada `dataset_works`, não é usada pelo ranking e não chega aos cards por `engine.public`.
- O frontend online (`online/anilist-import.js`, `ANI_FIELDS`) não solicita essas quatro estatísticas. O snapshot público e o banco público do atlas não têm essas colunas. Não afirmar que a estatística comunitária já está integrada ao dataset tratado ou ao produto online.
- `meanScore`, `popularity` e `favourites` não são coletados consistentemente como campos das obras no fluxo atual.
- A popularidade participa **indiretamente da seleção de candidatos**: amostra pública, sugestões iniciais e certas buscas usam ordenação `POPULARITY_DESC`. A ordenação final é calculada pelo nosso motor, sem somar popularidade, favoritos globais ou nota global ao score.
- Notas do histórico (`entries.score`) e favoritos pessoais importados/manuais são sinais de **um usuário**, separados das estatísticas gerais da obra. Esses sinais são usados somente quando a personalização está habilitada; o modo puro os ignora.

### Auditoria do banco bruto operacional

Em 06/11/2026, a leitura dos registros AniList no SQLite operacional encontrou 2.655 obras brutas: 2.653 com averageScore não nulo; zero com meanScore, popularity ou favourites. Essa contagem é do cache operacional ampliado pelo uso, distinta do snapshot público congelado de 2.495 obras. Os dois valores ausentes não foram inventados nem preenchidos com zero.

## Próxima integração proposta, ainda não implementada

É recomendável coletar e preservar os quatro campos de forma uniforme, com data de coleta, valores nulos explícitos e colunas tipadas. Consultas online, SQLite operacional, ETL tratado e exportação pública precisam concordar; ausências não devem virar zero. Os valores podem mudar ao longo do tempo, logo qualquer experimento deve congelar o snapshot.

Uma primeira aplicação seria exibir essas estatísticas e disponibilizar filtros opcionais. Não as somar silenciosamente à similaridade: uma obra muito popular ou bem avaliada pode ser pouco parecida com a referência. Uma eventual regra de desempate ou bônus pequeno precisaria de versão, parâmetros explícitos e avaliação de relevância antes de ser adotada. Popularidade não deve substituir a contagem real de votos para estimar confiança de uma média.

## Melhorias de relevância recomendadas

1. **Cobertura e variedade de candidatos:** ampliar o dataset autorizado para além da concentração atual em obras já conhecidas pelo usuário. Nenhum ranking recupera uma obra ausente do conjunto de candidatos.
2. **Julgamentos humanos separados por cenário:** avaliar semelhança com a referência e adequação ao perfil em âncoras variadas, medindo Precision@10 e nDCG@10. Congelar parâmetros e testar ajustes em consultas separadas das usadas para escolhê-los.
3. **Comparador lexical de RI:** testar BM25 ao lado dos vetores, ou uma combinação determinística, para verificar se termos raros e conceitos específicos ajudam. Isso é uma hipótese a avaliar, não ganho já demonstrado.
4. **Peso dos aspectos narrativos:** testar pesos explícitos por grupos de temas (premissa, ambiente, elenco etc.) para evitar que características genéricas dominem a relação com a âncora. Preservar uma versão de referência para medir o efeito.

Referências primárias: avaliação de ranking em https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html e BM25 em https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html . Essas propostas mantêm a linha de RI e vetores estáticos, sem treinamento no aplicativo.
