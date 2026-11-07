# Séries agrupadas e preferências por recorrência — 07/11/2026

## O que muda para o visitante

A recomendação apresenta **uma entrada por série**, com um menu discreto para ver suas temporadas e filmes relacionados. A lista começa com dez grupos e o botão **Carregar mais** acrescenta outros dez, até esgotar os grupos elegíveis. Não há uma busca nova na API a cada clique: o programa apresenta mais resultados que já calculou.

Sem preferências, a busca continua independente de notas e interesses. Com preferências, o usuário pode alternar entre recomendações gerais e personalizadas. A lista geral permite revisitar séries conhecidas; **Para descobrir** prioriza séries ainda não iniciadas, não apenas temporadas novas de uma série já vista. Séries da própria referência ficam fora das sugestões de outras séries.

O perfil passa a reconhecer recorrência de tags e gêneros, mesmo quando suas médias não estão entre as maiores notas. Não há exclusão automática de outros gêneros por terem menos ocorrências. Exclusões que o usuário escolheu explicitamente continuam respeitadas.

O modelo de palavras continua Word2Vec Skip-gram. Não há treinamento ou uso de LLM no aplicativo.

## Agrupamento baseado em relações oficiais

O coletor `collect_series_relations.py --execute` consultou somente os 3.413 IDs já presentes no snapshot. Retornou **6.647 relações** e **5.602 nós auxiliares**. Os nós adicionais são referências leves — título, formato, estado e data — não novas obras com sinopse/vetor incorporadas ao ranking. O dataset de recuperação continua tendo 3.413 obras.

O grafo usa componentes conectados por `PREQUEL`, `SEQUEL`, `SIDE_STORY`, `SUMMARY`, `COMPILATION` e `CONTAINS`. Não utilizamos semelhança de nomes para adivinhar franquias.

**PARENT foi excluído do agrupamento:** na inspeção, ligava Gundam: The Witch from Mercury e Iron Blooded Orphans por meio do Gundam original. A relação é oficial, mas não comprova continuidade narrativa. `ALTERNATIVE`, `SPIN_OFF`, `CHARACTER`, `OTHER`, `SOURCE` e `ADAPTATION` também não unem grupos automaticamente. Isso evita fundir remakes, universos alternativos, adaptações e crossovers. Filmes que só tenham uma relação excluída podem permanecer em outro grupo; é uma limitação deliberada da regra conservadora, não uma promessa de catálogo perfeito de franquias.

O grupo conserva a posição de sua melhor correspondência. Para apresentar uma porta de entrada, procuramos a obra elegível com data de lançamento anterior, sem substituir seus metadados ou falsificar seu score. Se a melhor correspondência for outra temporada, a explicação informa isso. A ordem de lançamento tem prioridade sobre cronologia: um prequel lançado depois pode exigir conhecimento da série original.

O agrupamento ocorre **depois dos filtros**, sem recolocar obras excluídas. Uma continuação cujo prequel não esteja disponível no recorte nem no histórico recebe aviso e não é oferecida como descoberta para começar do zero. O grafo depende da qualidade e cobertura das relações cadastradas no AniList.

Arquivos: `online/franchises.json`, `data/series-relations-protocol-v12.json` e `shared/franchise-core.js`. O SQLite público agora tem seis tabelas: `works`, `genres`, `tags`, `vectors`, `series_nodes` e `series_relations`. A sétima consulta auditada mostra relações de SPY x FAMILY. As relações possuem chaves para os nós auxiliares e são verificadas quanto a referências órfãs.

## Frequência e avaliação são sinais distintos

O método anterior somava os pesos relativos das notas e guardava só os 12 temas de maior magnitude. Isso podia classificar um gênero muito consumido como afastamento quando suas notas médias eram menores que o ponto neutro individual. Também podia omitir uma tag recorrente fora daquele resumo.

Agora calculamos **todos os temas com suporte no histórico**, sem corte top 12 ou top 30. Há dois canais distintos:

- Os centroides textuais continuam usando as notas individuais positivas e negativas, relativas à escala do usuário.
- A preferência temática combina recorrência e média relativa de notas, com mais peso para recorrência, conforme a decisão do usuário nesta etapa.

Para um tema, `c` é a quantidade de obras, `N` a quantidade de obras de referência do histórico, `m` a média das notas do tema, `n` o ponto neutro da escala e `h` metade da amplitude observada:

```text
frequência = ln(1+c) / ln(1+N)
qualidade = limitar((m-n)/h, -1, 1)
confiabilidade = c / (c+10)
peso_base = confiabilidade × (0,65 × frequência + 0,35 × qualidade)
```

A transformação logarítmica dá retornos decrescentes: mil ocorrências não valem mil vezes uma. O fator de confiabilidade impede que uma única ocorrência vire forte preferência. Não é uma probabilidade nem um teste estatístico de confiança. Os coeficientes são fixos e documentados; não foram aprendidos ou otimizados automaticamente.

Quando não há nota, qualidade é neutra — média zero informada por ausência não significa reprovação. Com escala de nota sem amplitude, não inventamos contraste. Favoritos acrescentam um reforço separado, limitado a 0,35 por tema; o peso final fica entre -1 e 1. Interesses explícitos continuam tendo prioridade como evidência declarada. Frequência alta pode resultar em aproximação mesmo com média moderada; notas ainda podem reduzir esse incentivo.

O programa não presume que consumo seja uma prova causal de gosto. Pode haver obrigações, exploração ou abandono; essa é uma hipótese de personalização que precisa de avaliação. Tempo assistido foi coletado como contexto, mas **não entra no peso**: séries longas poderiam dominar sem representar maior preferência.

### Estatísticas públicas e cobertura fora do top 30

A API permite consultar:

```graphql
query($name: String!) {
  User(name: $name) {
    statistics {
      anime {
        count meanScore minutesWatched
        tags(limit: 1000, sort: COUNT_DESC) {
          count meanScore minutesWatched tag { id name }
        }
        genres(limit: 100, sort: COUNT_DESC) {
          genre count meanScore minutesWatched
        }
      }
    }
  }
}
```

Na execução registrada, recebemos 30 estatísticas de tags, apesar do limite maior solicitado. Portanto, não usamos essa resposta como se contivesse todas as tags do usuário. Completamos os temas a partir dos metadados das obras importadas. Essa descoberta motivou a extensão: com a lista completa importada, o método atual calcula as estatísticas localmente por estado, sem depender do top 30. Perfis antigos têm fallback temporário para os agregados disponíveis até atualizar a importação. A página `perfil.html` apresenta o ranking próprio, com fonte e recorte explícitos.

Novas importações enriquecem **todas as entradas da lista**, inclusive planejados, para permitir estatísticas completas. Planejados sem nota não se tornam evidência de consumo: a frequência do perfil é calculada no recorte de iniciados. Todas as notas disponíveis continuam consideradas. Perfis antigos podem atualizar a lista para completar metadados de obras iniciadas ainda ausentes. O navegador atualiza os agregados públicos mantendo notas e preferências locais; no backend há `refresh_user_statistics.py --execute`, com servidor parado e backup privado.

Nenhuma lista pessoal, nota ou estatística individual entra no repositório ou no SQLite público. Na interface simples, um resumo opcional mostra alguns interesses recorrentes; na pesquisa, a tabela completa informa contagem, média, peso e fonte.

## Diagnóstico de Release the Spyce

A obra já estava no dataset. A similaridade temática com Lycoris Recoil era aproximadamente **0,2056**, abaixo do corte personalizado anterior de **0,25**. Por isso, ficava fora da personalizada mesmo sendo uma hipótese plausível para avaliação humana. Espionage, Female Protagonist, Primarily Female Cast e LGBTQ+ Themes apareciam entre os temas compartilhados.

O padrão simples agora é **Equilibrar semelhança e seus gostos**, com corte 0,15. A opção mais próxima da referência mantém 0,25; a opção mais ampla usa zero. O corte não foi ajustado por nome de anime, e nenhuma regra promove Release the Spyce artificialmente.

Ficar elegível não implica entrar no top 10. No diagnóstico do snapshot congelado, ela continuou abaixo do top 10 pelo score. O carregamento adicional permite inspecionar sua posição. Esse caso permanece evidência de limitação do ranking, não um problema que a mera presença no catálogo resolveu. Não anunciamos que a recomendação chegou ao nível da lista comunitária.

## Sinopse: aproximação semântica, não compreensão narrativa

Mantemos o texto completo. Entretanto, a média dos vetores estáticos não representa explicitamente quem oprime quem, planos políticos, causalidade, negação ou o papel de um protagonista. Não podemos afirmar que ela entendeu a revolução de Code Geass e a comparou estruturalmente com outras narrativas.

Tags como Politics, Military, War, Anti-Hero e temas de estratégia podem registrar parte dessas semelhanças, desde que estejam presentes nos metadados. Ausência de uma tag não prova ausência do tema. Cosseno esparso também penaliza obras com muitos outros atributos, o que ajuda a explicar algumas diferenças frente a julgamentos humanos.

Foram coletadas referências comunitárias de **dois animes solicitados**, com até 50 recomendações por referência, para diagnóstico externo (`data/community-reference-v12.json`). Os votos não foram incorporados ao ranking nem tratados como gabarito humano incontestável. Sobreposição com a comunidade pode ser estudada como concordância; não equivale automaticamente a Precision@10, e não devemos usar os mesmos votos para ordenar e depois medir acerto.

Próximas hipóteses de RI: avaliar expansão controlada de conceitos e vocabulário, correspondência entre facetas narrativas e diversificação por aspectos. Precisam ser testadas em referências distintas das usadas para formular a hipótese. Não substituem os vetores estáticos por LLMs.

## Verificações

32 testes Python; equivalência Python/JavaScript nos cenários públicos sintéticos; testes de agrupamento real de SPY x FAMILY, separação entre universos de Gundam, exclusão do grupo da referência, descobertas por série, escolha da porta de entrada, preservação de mais de 30 temas e ausência de nota tratada como neutra. O teste de modo puro continua verificando independência completa do perfil.

A auditoria numérica das 3.413 sinopses foi repetida: vetores e IDF permaneceram consistentes. Os embeddings não foram treinados ou substituídos. Os testes e a publicação executam-se pelo workflow do GitHub.

Fonte oficial: [AniList GraphQL](https://docs.anilist.co/), por consultas de dados e introspecção dos tipos `UserStatistics`, `UserTagStatistic` e `UserGenreStatistic`. Regras de agrupamento, ponderação e exibição acima são decisões deste projeto, não garantias do serviço.


A extensão de estatísticas completas está documentada em [MINHA_LISTA_EM_NUMEROS_V12.md](MINHA_LISTA_EM_NUMEROS_V12.md).

Os estudos humanos comparativos preservados são por obra individual. A pesquisa solicita desativar o agrupamento antes de preparar esse protocolo; métricas por série e diversidade demandam uma avaliação específica, sem reutilizar resultados como se fossem equivalentes.
