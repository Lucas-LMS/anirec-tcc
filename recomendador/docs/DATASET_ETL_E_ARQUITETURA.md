# Dataset AniList, ETL e arquitetura — 06/11/2026

## O que existe agora

A fonte das **obras do aplicativo atual é exclusivamente o AniList**. O Kaggle permanece apenas nos experimentos históricos, cujos protocolos e resultados não foram reescritos. O Word2Vec continua sendo o modelo estático pré-treinado no text8: a origem do modelo de palavras é diferente da origem das sinopses e metadados do dataset.

O banco operacional privado é `/home/lucas/tcc-lab/recomendador-private/anirec.sqlite3`. Ele tem 2.507 registros de obras AniList na versão auditada. Os 1.000 registros Kaggle legados foram retirados da tabela operacional depois de criar `legacy-before-anilist-only.sqlite3`, fora do material publicado. O perfil do usuário fica separado em `profile.json`; não foi publicado.

O tamanho não torna a amostra representativa. A seleção atual combina obras avaliadas pelo usuário de teste, buscas feitas no aplicativo e uma amostra pública de popularidade. Portanto há viés de usuário e de popularidade. A versão pública inicial tem 204 obras coletadas independentemente das notas do usuário; esse é um ponto de partida, não um limite definitivo do dataset ou da importação.

## Extração

`anilist_client.py` consulta a API GraphQL oficial, exclusivamente com queries de leitura. A importação percorre os blocos de 500 entradas até `hasNextChunk=false`, sem o antigo corte de 10.000 itens. Depois busca metadados de **todas as obras com nota maior que zero** e favoritos explícitos, em lotes de 50 IDs, sem o antigo corte de 300 sinopses. Bloco/lote é paginação, não seleção das melhores notas. Há proteção contra paginação que não avança, espera entre chamadas e tratamento de 429.

A importação completa observada teve 2.940 entradas de lista, 2.439 obras avaliadas e 2.439 registros ricos de metadados. Nenhuma dessas obras ficou sem registro de metadados. Isso não significa que a fonte tenha sinopse não vazia para cada obra: conteúdo ausente é identificado separadamente.

`collect_dataset.py` produz uma amostra pública inicial: quatro páginas de popularidade, ANIME, sem conteúdo adulto e sem títulos ainda não lançados, mais quatro obras de regressão (MAL 47, 144, 387 e 54). Total: 204 obras. `data/dataset-manifest.json` registra recorte, fonte, data e SHA-256. Esse script não é um raspador do catálogo inteiro e não deve ser descrito como amostragem aleatória ou representativa.

Os campos coletados incluem IDs AniList/MAL, títulos inglês/romaji, descrição integral, gêneros, tags e ranks, flags de spoiler, status, formato, ano de temporada, país, episódios, duração e data de início. Uma migração buscou novamente metadados antigos que ainda não tinham formato/ano. Não inferimos dados ausentes com um LLM.

## Transformação e carga SQL

`repository.py` guarda a última resposta usada, data de obtenção, texto tratado e hash. `etl_dataset.py` transforma esses registros, sem fazer novas chamadas de rede. As operações são:

1. Usar ID AniList como identidade. Foi encontrada uma colisão de MAL ID; as duas obras continuam separadas. Nunca juntar animes apenas porque compartilham MAL ID.
2. Preservar resposta original e hash, decodificar entidades HTML, remover marcação e normalizar espaços. Não resumir, traduzir ou truncar a sinopse.
3. Desdobrar gêneros e tags em relações muitos-para-muitos, remover duplicatas dentro da mesma obra, limitar ranks ao intervalo válido e preservar flags de spoiler.
4. Registrar NULL para ano/formato desconhecido. Sinopse vazia continua vazia. Texto repetido é apontado para auditoria, sem eliminar automaticamente sequências ou obras diferentes.
5. Gerar versão pelo hash dos IDs e respostas originais. Reexecutar com a mesma entrada não duplica os registros; mudar uma resposta cria outra versão e preserva a anterior.
6. Gerar relatório de qualidade e os vetores fixos derivados, com modelo, dimensionalidade, hash do texto e hash do IDF.

| Tabela | Conteúdo |
|---|---|
| `media` | Último registro operacional por fonte/ID |
| `dataset_raw` | Respostas originais distintas por ID e hash |
| `dataset_runs` | Versão, protocolo, data, hash e qualidade da ETL |
| `dataset_works` | Obras tratadas e sinopses inteiras por versão |
| `dataset_genres` | Relações obra–gênero |
| `dataset_tags` | Dicionário de tags observadas na versão |
| `dataset_work_tags` | Relações obra–tag, rank e flags de spoiler |
| `dataset_vectors` | Vetores float32, modelo e proveniência da representação |

As tabelas do dataset não contêm as notas ou a lista do usuário. Entretanto a seleção de obras pode refletir o histórico que originou a coleta; isso também é um viés e um cuidado de divulgação. A solicitação ao AniList pergunta explicitamente sobre redistribuição, e não presumimos que as descrições tenham licença CC0.

## Resultado auditado da ETL

Versão: `anilist-etl-v1-0e61971ca86d`. Relatório em `output/prototipo/dataset-etl.json`.

| Verificação | Resultado |
|---|---:|
| Obras | 2.507 |
| Com sinopse | 2.504 |
| Com tags | 2.491 |
| Com gêneros | 2.499 |
| Com ano de temporada | 2.476 |
| Com formato | 2.506 |
| Tags distintas observadas | 402 |
| Relações obra–gênero | 8.002 |
| Relações obra–tag | 40.089 |
| Grupos de sinopses não vazias idênticas | 8 |
| Colisões de MAL ID | 1 |
| Vetores derivados, 100 dimensões | 2.507 |
| Vetores zerados por falta de texto utilizável | 3 |

O catálogo ativo de candidatos exclui conteúdo adulto, mas os dados das obras avaliadas continuam disponíveis para calcular o perfil. Por isso contagem da ETL, contagem de candidatos e contagem de representações efetivas não são iguais. Notas neutras também não entram como vetor positivo ou negativo. O usuário pode consultar a auditoria pela seção “Dataset AniList e processo de ETL” na interface local.

## Como executar e consultar

No Ubuntu/WSL, dentro da pasta `recomendador`, com o ambiente Python já instalado:

```bash
/home/lucas/tcc-lab/.venv-word2vec-py312/bin/python etl_dataset.py
```

Esse comando transforma o que já foi coletado. Para ativar o conjunto operacional atualizado no motor, pare o servidor, execute `python refresh_dataset.py` nesse mesmo ambiente e reinicie. O snapshot anterior é preservado. A navegação não muda silenciosamente o IDF ou o perfil: novas obras entram no catálogo congelado apenas na atualização explícita do snapshot. `consultas_dataset.sql` contém exemplos de consultas de cobertura, gêneros, tags, duplicatas e vetores. A versão é um parâmetro de cada consulta.

```sql
SELECT genre, COUNT(*) AS obras
FROM dataset_genres
WHERE version = :version
GROUP BY genre ORDER BY obras DESC;
```

Esse exemplo mede a composição de gêneros da versão. Não mede qualidade de recomendação. Para inspecionar a representação armazenada, cada vetor float32 de 100 posições ocupa 400 bytes; o banco guarda BLOB e hashes do modelo/texto/corpus. Não existe treinamento durante essa etapa.

## Interpretação das notas por usuário

Para notas válidas maiores que zero, sejam `min` e `max` as menor e maior nota observadas. Definimos `neutro=(min+max)/2` e `peso=(nota-neutro)/((max-min)/2)`. A menor nota recebe -1, a maior +1 e o centro zero. Em uma escala de 5 a 10: 5→-1, 7,5→0, 10→+1. A escala é relativa ao usuário; não significa que 5 seja objetivamente 1/10.

Se não há variação, todas as notas têm peso zero: não inventamos quais obras são rejeitadas. Obras sem nota não viram aprovação. Favorito sem nota contribui com peso 2; quando há nota explícita, ela prevalece, inclusive se negativa ou neutra. Esse desenho é determinístico e sensível a outliers nas notas extremas; média, mediana e ponto neutro configurável são alternativas de avaliação futura, não modelos treinados.

O perfil textual é a soma ponderada assinada dos vetores, normalizada. Notas negativas subtraem a representação. Para os temas, acumulamos pesos assinados e preservamos até 12 temas inferidos de maior magnitude; preferências explícitas recebem peso 3. O denominador tem soma de valores absolutos para não dividir por um número negativo ou quase zero. A afinidade temática final é limitada a [0,1]. Um peso negativo é evidência relativa de afastamento, não uma certeza sobre cada tag isolada.

## Por que havia somente cinco recomendações de Lycoris Recoil

O teste reproduziu exatamente cinco elegíveis quando “ocultar vistos” estava ativado e a exclusão Male Protagonist permanecia ativa. Como o usuário tem uma lista extensa, esse filtro retirava quase toda a base atual. Desativá-lo, mantendo a exigência de gênero comum, deixou 845 candidatos.

O filtro de gênero idêntico também era excessivo para recomendações entre gêneros: retirava El Cazador, Magical Revolution e KimiShinu, apesar de temas relevantes em comum. Vistos e gênero idêntico passaram a ser filtros opcionais desativados por padrão. Male Protagonist continua sendo uma exclusão explícita do usuário: PSYCHO-PASS tem essa tag e é eliminado por ela. Não removemos a exclusão escondido para fazer um exemplo aparecer.

A versão `ir-v5-thematic-audit` usa 50% similaridade de sinopse e 50% similaridade temática. O componente temático é 85% cosseno de tags ponderadas por rank e raridade (IDF do catálogo) e 15% Jaccard de gêneros. Tags com rank menor que 50 não entram nesse cosseno. Tags marcadas como spoiler podem contribuir para relevância sem serem expostas automaticamente na lista de temas comuns. Exclusões explícitas também verificam tags marcadas como spoiler. As contribuições e o diagnóstico deixam isso auditável.

Esse ajuste corrige um desequilíbrio de engenharia observado: a descrição AniList de Lycoris fala bastante do café, enquanto armas/espionagem são descritas nas tags. Não prova que os pesos sejam ideais e não é treinamento supervisionado nos exemplos do usuário. Os exemplos não são inseridos manualmente no topo.

Com vistos permitidos, gênero comum opcional e Male Protagonist excluída, o teste local encontrou 1.291 elegíveis. Gunslinger Girl ficou em 7º geral; a primeira posição foi de sua sequência Il Teatrino. Symphogear G liderou a lista personalizada com Yuri explícito. Há resultados ainda questionáveis e concentração de franquias: qualidade e diversidade precisam de avaliação humana. `refinamento-lycoris-v5-resumo.json` guarda as observações pontuais. O diagnóstico de cada título informa se foi excluído e sua posição em cada lista, sem fingir que toda ausência é falha do embedding.

Geral e Para mim ordenam o mesmo conjunto elegível; personalização não precisa eliminar títulos para ser válida. A interface apresenta mais títulos inicialmente na geral e permite “Mostrar mais”, preservando a ordenação completa. Não fabricamos listas disjuntas. Uma avaliação deve medir alteração útil de relevância, cobertura, diversidade e satisfação, além de simples mudança de score.

## Limites semânticos e de idioma

Word2Vec é estático, inglês e não entende a frase inteira. A média ponderada das palavras captura associações distribucionais, mas perde ordem, negação, relações causais e parte do contexto. Sinopse inteira não transforma esse método em um encoder contextual. Nomes japoneses fora do vocabulário são ignorados; a cobertura é informada. As sinopses inglesas do AniList e as tags padronizadas permitem comparação útil, sem garantir compreensão narrativa. Mantemos o compromisso de não treinar um modelo ou usar LLM no motor final.

## Crescimento do dataset e contato oficial

Termos oficiais: https://docs.anilist.co/guide/terms-of-use. Há proibição de hoarding/mass collection e menção de flexibilidade educacional; não é uma autorização genérica de copiar tudo. Coletar lentamente não muda, por si só, a natureza de uma cópia integral.

Com autorização explícita do usuário, foi enviado e-mail a contact@anilist.co, pedindo orientação/permissão sobre escopo amplo ou catálogo completo, armazenamento SQL, retenção, snapshots, vetores, demonstração e redistribuição. Cópia em `solicitacao-anilist.html`; ID de envio `1a1aec632893c7c0`, confirmado como SENT. Não foi solicitado aumento de limite. A resposta está pendente.

Enquanto isso, o projeto não fica parado: tratamos o conjunto já usado, auditamos qualidade, avaliamos recuperação e definimos um protocolo educacional delimitado para ampliar cobertura por anos, formatos e gêneros. O protocolo futuro deve registrar critérios, páginas, datas, falhas, deduplicação e viés, em vez de simplesmente coletar tudo e chamar de amostra. O coletor atual de 204 é a semente pública; uma amostragem estratificada ampliada ainda precisa ser implementada e registrada. Não há coleta integral em segundo plano ou promessa de autorização concedida.

## Decisão de arquitetura: local e online

**Status: implementada para demonstração, ainda em avaliação.** A versão local usa Python/NumPy/Gensim, SQLite e snapshots. A versão online usa HTML/JS estático, os mesmos vetores fixos e armazenamento do navegador. Isso preserva o laboratório local e oferece um link compartilhável sem expor o servidor da máquina.

GitHub Pages hospeda conteúdo estático e não executaria nosso servidor Python. A publicação atual usa Sites: https://anirec-ri-animes.givingbamboo.chatgpt.site. Nenhum projeto Google com cobrança foi criado. Firebase Spark/Firestore é uma opção futura de sincronização com limites gratuitos, mas não é necessário para a primeira demonstração. Cloud Functions e Cloud Storage têm requisitos de plano/cobrança diferentes; não presumir que toda a plataforma Google seja gratuita.

A amostra online começou com 204 obras públicas, sem perfil do usuário. A importação de lista pública amplia as obras processadas naquele navegador: lê todas as avaliações, busca sinopses inteiras e gera vetores usando o vocabulário Word2Vec congelado. Na primeira vez baixa aproximadamente 28,5 MB de vetores, mais vocabulário e IDF. O modelo tem 71.290 palavras, 100 dimensões e cinco blocos binários; não há treinamento no navegador.

As notas ficam em localStorage e metadados importados em IndexedDB, sem um banco central de usuários. A API AniList recebe as consultas necessárias; a hospedagem recebe acessos aos arquivos. Não prometemos ausência de logs de infraestrutura. O usuário não envia credenciais nem faz login para ler lista pública. Importação e armazenamento podem falhar por rede, cota, privacidade do navegador ou limite do serviço; o perfil anterior é mantido até concluir.

Os resultados local/online não são necessariamente idênticos: o catálogo e o IDF de cada snapshot diferem, e a local tem controles adicionais. São versões relacionadas de um motor determinístico, não um experimento controlado de paridade. A seleção inicial de 204 não é o destino final do dataset e não limita o número de obras avaliadas importadas.

## Validação

Doze testes automatizados passaram na execução de refinamento (4,488 s): sinopses inteiras incluindo palavras tardias, assinatura das notas e neutralidade individual, score decomposto, estabilidade de snapshot, filtros, registros grandes, metadados ausentes, ETL idempotente, preservação de versões e colisões de MAL ID. A consulta real do dataset e o envio oficial foram confirmados. JavaScript validado com Node. Observações de tempo e rankings são pontuais, não intervalos de confiança ou métricas científicas de relevância. Consulte as evidências de interface e relatórios de integração ao lado do código.

## Refinamento v6: interpretação do score e ancoragem da personalização

Os valores da tabela são CONTRIBUIÇÕES já ponderadas, não quatro probabilidades. O exemplo informado pelo usuário (0,3059 + 0,0711 + 0,0112 + 0,0997) soma 0,4879. Na versão v5 com lambda=0,35, os máximos das quatro linhas eram 0,325; 0,325; 0,21; 0,14. Portanto 0,3059 na sinopse da âncora equivalia a um componente textual normalizado de 0,9412, não a “30,59% de semelhança”. O componente de temas da âncora era 0,2188; texto do perfil 0,0533; temas do perfil 0,7121. Não são percentuais de acerto/gosto. O texto do perfil tão baixo foi investigado, em vez de mascarado por reescala.

Foi identificado um defeito na representação agregada assinada: os vetores das obras em inglês compartilham uma direção frequente (anisotropia), e um grande volume de notas abaixo do neutro podia dominar a soma e inverter essa direção comum. O cosseno do perfil ficava próximo de -1 para muitas obras, mesmo sem evidência de que todas fossem rejeitadas.

A versão ir-v6-profile-contrast mantém todos os pesos individuais e calcula separadamente um centroide normalizado das obras positivas e outro das negativas. Quando ambos existem, a afinidade textual é `clip(0.5 + 0.5*(cos(positivo,candidato)-cos(negativo,candidato)),0,1)`. Assim um centro negativo muito numeroso não domina apenas por quantidade. Igual proximidade aos dois centros resulta em 0,5, neutro. Se há apenas centro positivo, usamos `(cos+1)/2`; apenas negativo, `(1-cos)/2`; sem centro, o componente pessoal pode usar apenas temas explícitos. Não há treinamento ou tentativa de interpretar a direção oposta de palavras como uma classe semântica.

O peso de tema explicitamente desejado caiu de 3 para 1. O perfil agora combina 70% afinidade textual contrastiva e 30% afinidade temática. Com lambda padrão 0,35, os máximos das quatro contribuições passam a 0,325; 0,325; 0,245; 0,105. A interface mostra o máximo de cada linha e o componente textual do perfil antes de aplicar seu peso. Para a geral são duas parcelas de máximo 0,5 cada.

Geral: `B=0.5*texto_ancora+0.5*temas_ancora`. Personalizada: `P=0.7*texto_perfil+0.3*afinidade_temas`, `S=(1-lambda)*B+lambda*P`. O resultado não precisa atingir 0,9. Exemplo: texto 0,94 e temas 0,22 geram B=0,58. Um B de 0,9 com esse texto exigiria temas 0,86, ou seja, alinhamento muito alto das representações temáticas completas, não apenas alguns elementos comuns. Não usamos min-max por busca para forçar o primeiro resultado a 1: isso faria até uma lista ruim parecer ótima. Qualidade real exige julgamentos humanos e métricas de ranking.

Foi introduzida vizinhança temática na personalizada: padrão 0,25 no componente temático da âncora, opção ampla 0,15 ou todo o conjunto 0. Não é 25% de probabilidade. Sem perfil ativo ou com lambda zero, as listas continuam coincidindo. A geral permite exploração ampla, enquanto a personalizada pode restringir a reordenação a obras suficientemente ligadas à âncora. O filtro é exibido e configurável; candidatos descartados recebem motivo no diagnóstico. Obras sem o mesmo gênero podem entrar por suas tags.

No teste local de Lycoris Recoil com Yuri explícito e Male Protagonist evitado: 1.291 elegíveis na geral e 38 na vizinhança personalizada padrão. As primeiras posições pessoais observadas foram Noir, Symphogear G, Lycoris Recoil -Friends are thieves of time.-, Gunslinger Girl -Il Teatrino- e Harmony. Há ainda sugestões questionáveis e temporadas repetidas; isso não é uma prova de qualidade ideal. Um threshold pode retirar exemplos que o usuário julga relevantes; as opções mais amplas e o diagnóstico permitem avaliar esse efeito sem esconder a regra.

Treze testes passaram em 4,734 s. O novo teste usa 50 obras fictícias com nota baixa e uma com nota alta, verificando que a afinidade do candidato positivo permanece acima de 0,5 e a do negativo abaixo de 0,5. Os testes anteriores de decomposição foram atualizados para as fórmulas v6. Nenhum teste impõe posições a títulos reais. Evidência numérica em `output/prototipo/contraste-perfil-v6.json`.

## Importação online validada

A versão publicada passou a incluir importação direta de lista pública AniList. Teste real no navegador: 2.940 entradas de lista, 2.439 obras com nota, 2.439 registros processados, zero registros indisponíveis, escala observada 5 a 10 e neutro 7,5. Os binários Word2Vec de 100 dimensões foram carregados em cinco blocos; todas as sinopses recebidas foram representadas integralmente, ignorando apenas termos fora do vocabulário estático. Importação demora minutos pela paginação e limites da API. Não pede senha nem API key, não envia avaliações ao servidor do site e não as distribui a outros visitantes. IndexedDB guarda metadados importados; localStorage guarda notas. Visitantes na mesma instalação de navegador compartilham seu armazenamento local, portanto não tratar como isolamento por login.

A online e a local usam snapshots/IDF distintos, portanto podem gerar ordens diferentes. A online não importa favoritos AniList sem nota nesta implementação: importa todas as obras com nota, que foi o requisito prioritário. O aplicativo local também possui favoritos manuais e importação de favoritos. Um registro recuperado sem descrição não passa a ter sinopse inventada; a ausência continua uma limitação a auditar. A amostra pública inicial de 204 é ampliada pelas obras importadas no próprio navegador, sem um limite artificial de 204 ou de 300 avaliações.

A auditoria da interface online encontrou notas decimais importadas que não eram múltiplas de 0,5. A lista de opções agora inclui o valor exato importado, evitando apresentar visualmente “Sem nota” para um registro que tem avaliação. O IDF temático online é recalculado quando o conjunto no navegador é ampliado/restaurado; a raridade de tags não fica artificialmente limitada às 204 obras iniciais. O IDF lexical usado para representar os documentos importados permanece o da semente pública, enquanto a local usa seu snapshot ativo. Isso é mais uma razão para não tratar as versões como comparação controlada de paridade.

## Artefatos e verificação final desta etapa

Foi exportado um banco de pesquisa separado em `output/dataset-anilist/anilist-etl-v1-0e61971ca86d.sqlite3`, com 2.507 obras, 2.507 respostas originais, 8.002 relações de gêneros, 402 tags, 40.089 relações de tags e 2.507 vetores. `PRAGMA integrity_check` retornou `ok`. O manifesto declara ausência de perfil e notas pessoais. Este arquivo é um artefato local de pesquisa, não foi enviado ao site público; redistribuição ampla continua dependente das condições do AniList.

A versão online foi publicada com sucesso (versão de hospedagem 5, motor ir-v6-profile-contrast) em https://anirec-ri-animes.givingbamboo.chatgpt.site. Importação real, restauração após reload, notas decimais exatas, busca de Lycoris Recoil, preferências explícitas e troca de listas foram verificados na interface. No navegador testado, 2.488 obras estavam carregadas após combinar semente e importação. Com os mesmos filtros Male Protagonist/Yuri e vizinhança padrão, foram 1.291 elegíveis gerais e 38 personalizados; o tempo pontual de cálculo no navegador foi aproximadamente 1,56 s. A primeira posição pessoal online diferiu da local, conforme as diferenças documentadas de corpus/IDF e cobertura. Não chamar isso de paridade demonstrada ou benchmark de desempenho.

A interface local mostrou, para Noir: texto da âncora 0,3165/máx.0,3250; temas da âncora 0,1183/máx.0,3250; texto contrastivo do perfil 0,1233/máx.0,2450; temas do perfil 0,0295/máx.0,1050. O total foi aproximadamente 0,5876; texto bruto do perfil 0,503 (perto do neutro), sem o colapso negativo anterior. Evidência visual em `output/prototipo/score-contraste-v6.jpg`.

O ZIP de código/documentação inclui o esquema, consultas SQL, ETL, exportador, interface, testes e sementes públicas. Os blocos binários e vocabulário completo do modelo online são gerados por `build_online.py` e não acompanham esse ZIP para evitar duplicação dos pesos; o site publicado contém todos os ativos necessários. O pacote não inclui o perfil privado, banco operacional, credenciais, chave Groq ou qualquer variável secreta da hospedagem. O modelo Word2Vec local e ambiente Python continuam sendo pré-requisitos da instalação de laboratório.

## Atualização v7
A publicação atual usa 2.495 obras públicas do snapshot, sem perfil ou notas. O recorte inicial de 204 descrito acima é histórico. Consulte GUIA_PREFERENCIAS_V7.md para fórmula, parâmetros, privacidade e testes atuais.
