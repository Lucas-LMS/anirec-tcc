# Comparação de conteúdo e recomendações da comunidade — 7/11/2026

Esta etapa é exploratória. O modelo principal permanece Word2Vec Skip-gram estático (text8, 100 dimensões), sem treinamento no programa. O ranking padrão não recebeu o bônus comunitário. O botão “Comparar com recomendações da comunidade” monta duas listas de até 20 séries, calculadas sobre exatamente os mesmos candidatos elegíveis na mesma chamada. Na aba Para você, o perfil é mantido nas duas listas; a única diferença é o bônus comunitário.

## O que os votos significam

`recommendations.rating` registra o saldo de votos de uma relação entre a referência e outra obra. Não é averageScore, meanScore, número total de pessoas que votaram, nem probabilidade. Não é simétrico por hipótese: buscamos as relações da referência consultada. Fonte oficial: https://github.com/AniList/docs; consulta GraphQL efetivamente utilizada em `anilist_client.py` e `online/browser-adapter.js`. A documentação estática retornou HTTP 403 durante esta consulta; os campos foram verificados na API e sua introspecção, sem inventar campos de votos positivos/negativos que não existem no objeto.

Para score de conteúdo S entre zero e um, usamos:

    v = max(0, saldo de votos)
    força = v / (v + 20)
    bônus = 0.35 × força × (1 − S)
    score combinado = S + bônus

Por exemplo, com S=0.60: sem registro, saldo zero ou negativo mantém 0.60; um voto gera aproximadamente 0.6067; 20 votos gera 0.67; 100 votos gera aproximadamente 0.7167. O denominador reduz o impacto de pouca evidência e o fator (1−S) mantém o score até um. São constantes de desenvolvimento, não parâmetros treinados ou validados como ótimos. Saldo negativo não aplica punição nesta versão. Não haver relação não significa não haver semelhança. Uma obra pode perder posições porque outras recebem bônus, mesmo mantendo seu score exatamente igual.

## Coleta e cobertura

O snapshot público `online/community-recommendations.json` contém relações de nove referências de desenvolvimento. Não copia todo o catálogo. Até seis páginas de 25 relações por referência, ordenadas por saldo. Armazenamos identificador da referência, alvo, saldo, origem, horário UTC e indicador `complete`. Code Geass atingiu 150 relações com cobertura parcial. Outras oito referências tiveram todas as páginas retornadas neste recorte. Obras ausentes do catálogo não são inseridas ou liberadas automaticamente só por terem votos. Todos os filtros e a vizinhança pessoal continuam valendo. Uma consulta nova pode usar a API, nos mesmos limites; sem conexão ou com falha, mantém conteúdo e informa ausência de evidência.

## Resultado reproduzível

O arquivo `data/community-comparison-v13.json` guarda nove comparações sem perfil privado. Catálogo congelado: 3.413 obras; 3.407 elegíveis em cada consulta pura. Mesmo grafo oficial para agrupar temporadas. Em Lycoris Recoil, Release the Spyce fica em **174 por conteúdo e 12 com comunidade**. Foram observadas 138 relações para essa referência. Os dois top 10 compartilham sete séries. A variação entre referências é grande: Spirited Away compartilha apenas uma; Monster, oito. Isso mede mudança de ranking, não precisão.

O protocolo não mede nDCG contra esses mesmos votos: isso seria circular, pois os votos já são ingrediente da segunda lista. Melhorias de relevância exigem julgamentos humanos independentes e, preferencialmente, referências que não participaram da escolha dos parâmetros. Esta configuração foi examinada com Lycoris Recoil durante o desenvolvimento; portanto seu sucesso nesse caso não é generalização comprovada.

## Diagnóstico do conteúdo e do perfil

Não encontramos uma soma aritmética incorreta que explique isoladamente Release the Spyce. A sinopse publicada de Lycoris Recoil descreve sobretudo o café e serviços; representar a sinopse inteira não recupera automaticamente a premissa de espionagem que o texto pouco descreve. Média de vetores estáticos não interpreta relações narrativas como um leitor: alta similaridade vetorial também pode ocorrer entre enredos distintos. Tags usam coincidências exatas ponderadas: Ninja, Assassins e Espionage não são sinônimos automaticamente. Os pesos IDF e a normalização penalizam os muitos temas não compartilhados. A obra Release the Spyce tampouco possui a tag Yuri no snapshot utilizado; não devemos acrescentá-la manualmente para forçar o resultado.

No perfil observado localmente, as componentes textuais positivas e negativas são próximas e produzem pouca variação; a parcela de temas divide pelos interesses positivos do perfil inteiro. Um perfil com centenas de temas tende a ter coberturas pequenas. Geral com perfil também respeita exclusões explícitas: isso já aproxima seus candidatos dos pessoais. Foram exploradas ponderações de tags, descrições das tags, centralização de vetores, coocorrências e normalização por percentis. Não houve validação suficiente para substituir o cálculo padrão com segurança; hipóteses não aprovadas foram preservadas no laboratório privado, fora do site. Não aumentamos scores artificialmente nem criamos regra por título. Uma revisão de personalização continua sendo trabalho separado, com avaliação independente antes de substituir o padrão.

## Código e verificações

`community_recommendations.py` aplica a fórmula em uma cópia do resultado, guarda os scores anteriores, mantém o conjunto elegível pessoal e geral, recalcula ordenação e diagnósticos e registra origem e parâmetros. `shared/community-core.js` executa a mesma operação no navegador. `test_community.py` testa ausência/zero/negativo, suavização de poucos votos, preservação de entradas e candidatos, soma das parcelas, validação dos parâmetros e paridade Python/JavaScript. `shared/app.js` reconstrói o ranking de conteúdo usando os scores guardados e mostra as duas listas separadamente; a lista principal permanece inalterada. `server.py` mede a consulta comunitária separadamente do tempo de cálculo. As duas listas são descritivas, não uma conclusão sobre qual método é melhor.

A aba Geral agora tem uma única lista. O par Todos os títulos/Para descobrir existe apenas na personalizada. A versão histórica do manual integral continua vinculada ao commit que documentou; este arquivo é o adendo desta alteração.
