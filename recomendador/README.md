> **Atualização de interface e experimentos v8:** seletor de quatro modelos estáticos em área separada, atlas visual e SQLite público, funil de filtros, julgamentos e expansão de descobertas. [Guia completo](docs/LABORATORIO_E_ATLAS_V8.md).

> **Versão atual: ir-v7-guided-profile.** Interface compartilhada online/local, assistente sem notas, duas listas de até 10, afinidade corrigida e 2.495 obras públicas. Consulte [o guia atualizado](docs/GUIA_PREFERENCIAS_V7.md). As referências a versões anteriores abaixo são históricas.

> **Versão atual (06/11/2026): ir-v6-profile-contrast.** Obras exclusivamente do AniList; sinopses inteiras; todas as avaliações; escala individual; contraste entre centroides positivos/negativos; 50% texto + 50% temas na âncora; 70% texto contrastivo + 30% temas no perfil; peso explícito de tema 1; vizinhança temática personalizada ajustável. Vistos e gênero idêntico são opcionais, desligados por padrão. As seções antigas abaixo são histórico de implementação. O guia atualizado da base está em [docs/DATASET_ETL_E_ARQUITETURA.md](docs/DATASET_ETL_E_ARQUITETURA.md).
>
> **Online:** https://anirec-ri-animes.givingbamboo.chatgpt.site — agora importa lista pública no navegador, com todos os registros avaliados. A semente pública de 204 obras não limita a importação. O perfil não é compartilhado entre visitantes. A versão local continua em http://127.0.0.1:8765.

> **Registro histórico: ir-v2-full-synopsis.** Desde esta atualização, o aplicativo usa a sinopse inteira disponível na fonte, sem corte de palavras, para catálogo, âncora, candidatos e perfil. As seções históricas que mencionam 80 palavras descrevem versões anteriores. Consulte a seção “Sinopses inteiras” ao final. Os comparativos científicos anteriores mantêm o protocolo original de 80 palavras e não foram recalculados.

# AniRec: primeiro protótipo funcional — 05/11/2026

Este programa recomenda animes por recuperação da informação. Você escolhe uma obra de referência e recebe duas ordenações: sem pesos positivos do perfil e com preferências pessoais. Usa Word2Vec Skip-gram fixo, sem treinamento, ajuste fino, classificador, MiniLM ou LLM durante a execução. A seleção deste vetor é provisória, baseada nos comparativos anteriores; não demonstra que seja o melhor para personalização.

## Abrir e encerrar

Na pasta do projeto, execute no PowerShell:

```powershell
.\recomendador\iniciar.ps1
```

Abra http://127.0.0.1:8765. O iniciador verifica se o servidor já existe, inicia o Ubuntu/WSL em segundo plano e aguarda a disponibilidade. Para encerrar:

```powershell
.\recomendador\parar.ps1
```

Não altera permanentemente a política de execução do PowerShell. Caso sua configuração bloqueie scripts, execute diretamente no Ubuntu/WSL `bash iniciar.sh`, dentro da pasta recomendador, e abra o endereço acima. Pré-requisitos já existentes nesta máquina: Ubuntu/WSL, Python em `/home/lucas/tcc-lab/.venv-word2vec-py312`, NumPy, Gensim, o modelo e o índice descritos abaixo. Este pacote de código não é uma instalação autossuficiente para outro computador.

Logs: `output/prototipo/logs/servidor.log` e `erros.log`. O serviço escuta somente em 127.0.0.1. Não está publicado na internet nem disponível automaticamente pelo celular.

## Como usar

1. Pesquise um título e selecione a versão correta. Sinopses e termos de preferência são em inglês.
2. Gere recomendações. As abas Geral e Para mim usam os mesmos candidatos e filtros, permitindo observar apenas a mudança de ordenação.
3. Opcionalmente importe uma lista pública do AniList pelo nome de usuário. Não há login OAuth, senha ou acesso a listas privadas nesta versão.
4. Salve temas desejados, como `Yuri, Cute Girls Doing Cute Things`, ou temas a evitar. Adicione favoritos manualmente se preferir não importar histórico.
5. Ajuste a influência do perfil entre 0 e 60%. O padrão é 35%. Expanda “Por que apareceu?” para consultar temas, similaridade e fonte.
6. “Ocultar” remove uma sugestão das próximas listas; a seção de itens ocultos permite restaurá-la. Favoritos manuais também podem ser removidos.

Os filtros padrão ocultam a própria âncora, itens vistos/iniciados/favoritos, itens explicitamente ocultos, lançamentos futuros quando o status é conhecido e candidatos sem nenhum gênero em comum com a âncora. Temas explicitamente evitados são excluídos das duas listas quando os metadados os identificam. Ausência de tag ou status não comprova ausência do tema ou lançamento. Não há filtro de franquia/continuação nesta versão.

## Arquitetura e fontes

- `web/index.html`: interface HTML/CSS/JavaScript, sem framework ou etapa de compilação.
- `server.py`: servidor HTTP da biblioteca padrão, valida origem local e encaminha operações ao motor.
- `engine.py`: representação de sinopses, montagem de perfil, filtros e ordenação determinística.
- `anilist_client.py`: consultas GraphQL somente de leitura, paginação, espera entre pedidos e cache.
- `test_engine.py`: testes com perfis temporários; não sobrescrevem o perfil real.
- `demo_ir_estatico.py` e `EXEMPLO_RI_SEM_TREINAMENTO.md`: demonstração didática anterior.

Vetores carregados de `/home/lucas/tcc-lab/Word2Vec/models/text8-skipgram-100d.model`. São 100 dimensões, treinamento histórico no text8 com janela 5, min_count 5, cinco épocas e semente 20261029. O aplicativo apenas chama `Word2Vec.load(...).wv`; não chama `train`. Word2Vec é um método de vetores estáticos: cada palavra conhecida possui o mesmo vetor, independentemente da frase. As limitações incluem palavras desconhecidas, polissemia e ausência de compreensão contextual.

O catálogo congelado de 1.000 títulos e seu índice estão em `laboratorio/anime-en-20261105/data/catalog.json` e `results/retrieval/w2v-sg/`. Sua origem e seleção estão documentadas no relatório do comparativo de anime. Esse catálogo antigo não representa todo o AniList atual.

Para ampliar uma busca, o AniList fornece até 20 recomendações comunitárias da âncora e até 50 títulos por popularidade do primeiro gênero da âncora, excluindo IDs conhecidos quando solicitado. A união com o catálogo local é deduplicada por ID. O motor local calcula a ordem final. Portanto há influência da seleção comunitária/popularidade na geração de candidatos, mesmo sem copiar sua ordenação final. Não é uma busca exaustiva sobre todos os animes existentes.

Documentação oficial utilizada: [consultas de listas](https://docs.anilist.co/guide/graphql/queries/media-list), [autenticação](https://docs.anilist.co/guide/auth/), [limites](https://docs.anilist.co/guide/rate-limiting), [termos](https://docs.anilist.co/guide/terms-of-use). São consultas educacionais delimitadas, sem espelhamento integral do catálogo. Capas são carregadas pelo navegador a partir da fonte; não são empacotadas.

## Cálculos explicados

Cada sinopse passa por limpeza de HTML, normalização Unicode NFKC e minúsculas. Extraímos palavras com letras, sem dígitos, limitando o texto a 80 palavras. Calculamos média dos vetores conhecidos, ponderada pelo IDF fixo do catálogo, e normalizamos o resultado para comprimento 1. IDF dá maior peso a palavras menos frequentes no catálogo; não há ajuste com o perfil. Palavras fora do vocabulário são ignoradas. Sem vetor utilizável, a obra não pode ser comparada por essa representação.

A similaridade cosseno é o produto entre vetores normalizados. Convertemos de [-1,1] para [0,1] por `(cos + 1)/2`. Temas incluem gêneros e tags não marcadas como spoiler. Gêneros têm peso 1; tags usam rank/100. A interseção temática da âncora usa Jaccard: número de temas comuns dividido pelo número de temas distintos na união.

```python
base = 0.8 * ((cos_anchor + 1) / 2) + 0.2 * jaccard_topics
profile_score = 0.6 * ((cos_profile + 1) / 2) + 0.4 * affinity
final = (1 - personalization) * base + personalization * profile_score
```

`base` representa a relação com o anime pesquisado. `profile_score` representa a afinidade com os sinais positivos. `personalization` é 0.35 por padrão. Sem sinais de perfil, o peso efetivo é zero e ambas as listas coincidem. Se existem somente temas explícitos e nenhum vetor de perfil, o componente pessoal é apenas a afinidade temática. Os scores são números relativos para ordenar candidatos, não probabilidade de gostar nem precisão medida.

Favorito explícito/manual tem peso 2. Uma nota positiva contribui apenas nos estados COMPLETED, CURRENT ou REPEATING e se for pelo menos 70/100. Seu peso é `0.5 + (nota - 70)/30`, limitado a 100. Sem nota ou nota zero não significa rejeição; PLANNING não significa aprovação. DROPPED não é sinal positivo, exceto favorito explícito. O vetor do perfil é a média ponderada dos vetores disponíveis dessas obras, normalizada.

Os 12 temas mais frequentes nos sinais positivos formam preferências inferidas. Cada tema desejado explicitamente recebe peso 3. Afinidade é a soma dos pesos de preferência encontrados no candidato, multiplicados pelo peso de sua tag/gênero, dividida pela soma dos pesos das preferências. São regras aritméticas escolhidas para o protótipo, não parâmetros treinados ou cientificamente otimizados.

## Histórico, cache e privacidade local

A importação coleta a lista leve em blocos de até 500 registros, até 10.000 entradas, verificando se há continuação. Busca metadados ricos para até 300 sinais fortes, priorizando favoritos e notas; atualização recente é critério secundário, não data comprovada de consumo. Obras disponíveis no catálogo congelado também podem contribuir. A lista inteira serve para ocultar itens conhecidos, mas somente obras com representação disponível formam o vetor do perfil.

Teste real: 2.940 entradas únicas importadas, sem truncamento; 1.561 sinais positivos identificados; 380 representações disponíveis para o perfil; 2.517 itens conhecidos. Esses números têm significados diferentes e não devem ser apresentados como 2.940 sinopses vetorizadas. Preferências iniciais Yuri/CGDCT refletem o exemplo fornecido pelo usuário.

Perfil salvo fora do OneDrive em `/home/lucas/tcc-lab/recomendador-private/profile.json`, com uma cópia anterior `profile.previous.json`. “Limpar importação” remove o histórico ativo, preservando preferências manuais; a cópia anterior pode continuar contendo o estado anterior. Não é apagamento seguro. O perfil real não é incluído no pacote de código.

Cache de consultas: uma hora, até 200 respostas; intervalo mínimo 2,2 s entre chamadas. Uma resposta 429 pode aguardar Retry-After até 60 s e tentar novamente uma vez. Metadados navegados ficam em cache temporário de até 200 obras. O cálculo do perfil usa snapshots salvos e catálogo imutável, evitando mudanças silenciosas ao navegar. Falha de rede permite uso dos dados locais, com aviso; uma busca exclusivamente local tem candidatos mais limitados.

## Exemplos de código

Este exemplo conversa com o servidor local já iniciado, sem usar chave, treinar ou enviar dados a um LLM:

```python
import json
from urllib.request import urlopen, Request

root = 'http://127.0.0.1:8765'
search = json.load(urlopen(root + '/api/search?q=Lycoris%20Recoil&online=true'))
# Examine os títulos para escolher a versão correta, em vez de aceitar qualquer homônimo.
chosen = next(item for item in search['items'] if item['title'] == 'Lycoris Recoil')
payload = dict(key=chosen['key'], personalization=0.35, exclude_seen=True,
               online=True, require_genre=True, exclude_upcoming=True)
request = Request(root + '/api/recommend',
                  data=json.dumps(payload).encode(),
                  headers={'Content-Type': 'application/json'})
result = json.load(urlopen(request))
for item in result['personalized']:
    print(item['title'], round(item['personalized_score'], 3))
print('Tempo local em ms:', result['ranking_ms'])
print('Tempo total em ms:', result['total_ms'])
```

`urlopen` recebe JSON da busca; `chosen` identifica a obra selecionada; `Request` envia as opções locais; a resposta contém ambas as listas e tempos. `ranking_ms` inclui montagem do perfil, representação/filtros e ordenação depois da rede; `scoring_ms` mede um trecho menor do cálculo; `total_ms` inclui consultas externas. Pedidos em cache não representam latência fria de rede.

Rotas adicionais: GET `/api/health`, `/api/config`, `/api/import-status`; POST `/api/profile/import` (`username`), `/api/profile/preferences` (`preferred`, `avoided`, listas de textos), `/api/profile/favorite` e `/reject` (`key`, `add`), `/api/profile/clear-import`, `/api/shutdown`. O servidor aceita JSON e rejeita origem/Host externos; não oferece CORS público. Perfil e preferências são de um usuário local, não de várias contas simultâneas.

## Verificações e problemas corrigidos

Seis testes passaram em 4,632 s na última execução: ocultar/restaurar/excluir tema; perfil grande com 20 candidatos relacionados; notas ausentes/planejados não virarem aprovação; ausência de perfil/peso zero; perfil independente do cache de navegação; decomposição dos scores e limite de influência. Executar no Ubuntu, na pasta recomendador: `/home/lucas/tcc-lab/.venv-word2vec-py312/bin/python -m unittest test_engine -v`.

Foi corrigida uma expulsão incorreta de candidatos do cache com histórico grande, separando catálogo, snapshots do perfil e cache transitório. Foi corrigida a dependência acidental do perfil em metadados de navegação. A importação inicial de muitos registros ricos foi substituída por lista completa leve e 300 metadados prioritários. Foram adicionados filtros de tipo ANIME, gênero compartilhado e futuro conhecido após inspeção de sugestões inadequadas. Essas regras pertencem ao protótipo e não alteram retroativamente os experimentos congelados.

Teste integrado de Lycoris Recoil: 1.064 candidatos únicos, 408 elegíveis, 20 relacionados e 50 por gênero retornados; cálculo local 179,94 ms; tempo completo 3.836,35 ms. Arquivo de evidência: `output/prototipo/verificacao-integracao.json`. Na interface, um pedido posterior em cache levou cerca de 0,09 s. São observações pontuais, sem repetição estatística ou garantia de desempenho.

As duas listas colocaram Noir em primeiro, e a personalização alterou outras posições. Entretanto Fairy Tail e outras sugestões amplas permaneceram no topo pessoal. Logo, funcionar tecnicamente não prova recomendar bem. Não forçamos Princess Principal a aparecer. Para avaliar qualidade, precisamos de julgamentos humanos independentes, casos e perfis previamente definidos, comparação sem perfil e com perfil, métricas de ranking e análise de cobertura/diversidade. A expansão por popularidade e a desigualdade de tags entre Kaggle e AniList podem introduzir viés.

Não foram instalados novos modelos ou dependências nesta etapa, usados serviços pagos, nem utilizados GPT/Groq/DeepSeek no aplicativo. Os relatórios anteriores de SMS e anime, com seus protocolos, permanecem em `output/comparacao-sms/` e `output/comparacao-anime-en/`. Este guia documenta o protótipo e não substitui aqueles relatórios.

## Atualização: seletor oficial de tags e filtros — 05/11/2026

Foi adicionada a rota GET `/api/tags`. O cliente executa a consulta oficial:

```graphql
query {
  MediaTagCollection { id name description category isAdult }
  GenreCollection
}
```

A referência está em https://docs.anilist.co/reference/query. No teste real, a API retornou 430 tags e 19 gêneros. Os números podem mudar no AniList. A taxonomia é consultada sob demanda, sem chave, e reutiliza o cache de uma hora. Não é uma lista inventada ou extraída das poucas obras do catálogo local. É a taxonomia de mídia do AniList, também utilizada para mangás; ter uma tag disponível não significa que existam candidatos de anime com ela nesta seleção.

Para usar: abra “Explorar todas as tags e gêneros do AniList”, clique em “Carregar lista oficial”, pesquise um nome ou definição, ou escolha uma categoria. Leia a definição em inglês. “Quero mais” acrescenta ao campo positivo; “Evitar” acrescenta ao campo de exclusão. Depois clique em “Salvar preferências” e gere as listas novamente. Máximo de 30 temas por campo, sem duplicação ao adicionar pelo seletor. Os campos manuais continuam disponíveis se houver falha de rede. A interface identifica tags adultas, mas a seleção de uma delas não desativa o filtro de conteúdo adulto dos pedidos de candidatos ao AniList.

A pedido do usuário, Male Protagonist foi adicionada e salva nas exclusões reais. Sua definição oficial é “Main character is male.” Não confundir com Primarily Male Cast: uma se refere ao protagonista, outra à composição do elenco. Excluir uma não equivale a excluir a outra, e obras de múltiplos protagonistas dependem de como foram etiquetadas no AniList.

Exclusões agora verificam todas as tags registradas, inclusive aquelas marcadas como spoiler. Essas tags continuam ausentes das explicações temáticas comuns; omiti-las da exibição não deve permitir que uma exclusão explícita seja ignorada. O sistema não tenta deduzir gênero de personagens com IA ou heurísticas de nomes.

Novo parâmetro POST `/api/recommend`: `require_tag_metadata`, booleano, padrão false. Se houver temas evitados e ele for true, candidatos sem nenhuma tag também são eliminados. A interface chama a opção de “Ao evitar temas, excluir também títulos sem tags registradas”. Ela vale para ambas as listas. Mesmo registros com tags podem estar incompletos: este modo NÃO certifica ausência de protagonistas masculinos. A indisponibilidade de informação é diferente da ausência do atributo.

Novos campos de resposta: `excluded_by_topic` e `excluded_unknown_tags`. São contagens na etapa dos filtros temáticos, depois dos filtros anteriores, e não uma decomposição exaustiva de todo o catálogo. Não devem ser somadas a qualquer contagem anterior supondo grupos completos. A interface apresenta os números para ajudar a entender por que há poucas sugestões.

Teste de integração com Lycoris Recoil, histórico ativo e exclusão Male Protagonist em modo restrito: 48 candidatos eliminados por tema e 357 sem tags eliminados; 3 elegíveis; tempo total pontual 5.752 ms. Evidência: `output/prototipo/verificacao-tags.json`. A lista final incluiu Noir, JoJo's Bizarre Adventure: STONE OCEAN e Baccano!. Esse resultado demonstra o funcionamento do filtro conforme os metadados, não comprova que todos os três atendam à interpretação pessoal de ausência de protagonistas masculinos. É necessário avaliar cobertura e qualidade das tags antes de fazer uma afirmação forte no TCC. O modo restrito permanece opcional e não foi ativado por padrão para não esconder grande parte do catálogo antigo sem explicação.

Foi adicionada exportação “Exportar este resultado (JSON)”: salva localmente a resposta de recomendação e o horário da exportação, com listas, scores, parâmetros, filtros e tempos. O arquivo não inclui o histórico bruto importado, mas contém preferências inferidas e dados dos resultados; o usuário deve considerá-lo um registro de sua sessão. Exportar não envia o resultado a outro serviço. Este registro é útil para inspecionar resultados; não substitui uma avaliação científica com repetições, julgamentos humanos e dados congelados. Alterações futuras na API podem modificar candidatos/metadados.

Validação desta atualização: sintaxe JavaScript verificada com Node; consulta real à taxonomia; seleção, pesquisa, definição e gravação da exclusão verificadas na interface; persistência confirmada após reiniciar; sete testes de motor passaram em 3,863 s. O novo teste usa dados fictícios e verifica que uma tag indesejada marcada como spoiler é excluída e que candidatos sem tags são eliminados no modo restrito. O perfil real não é modificado pelos testes. A exportação foi implementada, mas o download do arquivo ainda não foi verificado interativamente nesta etapa.

Nenhuma nova dependência ou modelo foi instalado. Os pesos de recomendação e os relatórios comparativos anteriores permanecem preservados. A próxima prioridade de qualidade é avaliar candidatos e cobertura de metadados, e não aumentar o peso do perfil apenas para forçar uma resposta esperada.

## Atualização: menu sobreposto de seleção

O seletor anterior foi substituído por um `dialog` nativo do HTML, aberto por “Escolher tags e gêneros…”. As abas Tags/Gêneros mostram respectivamente todas as opções retornadas pela taxonomia oficial, com rolagem interna, busca por nome/descrição, categoria para tags e indicação de cada seleção. Não há paginação ou truncamento da lista apresentada. Todos os itens podem ser explorados; permanece o limite documentado de 30 preferências positivas e 30 negativas, que é diferente do tamanho da taxonomia.

Clicar em Quero mais ou Evitar alterna a marcação. Uma escolha feita no menu remove a mesma opção do campo oposto, evitando querer e excluir simultaneamente o mesmo tema. Esta resolução se aplica ao menu; texto manual ainda exige revisão do usuário. As alterações ficam em rascunho nos campos até “Salvar seleção”, que envia as duas listas ao endpoint existente. Cancelar, fechar com X ou Escape restaura os campos ao estado da abertura, sem gravar. O dialog nativo isola a interação da página ao fundo e restaura o foco ao fechar. Layout adaptado à tela pequena com rodapé de ações visível. Sem nova dependência ou mudança de pesos/modelo.

Verificações: Node validou a sintaxe JavaScript; teste interativo abriu o menu, alternou para os 19 gêneros, adicionou Action e cancelou (campos originais restaurados); salvar a seleção existente foi exercitado; reabertura exibiu Male Protagonist marcada em Evitar. A busca ordena correspondência exata antes de correspondência parcial: Female Protagonist também contém a sequência “male protagonist”, mas Male Protagonist aparece primeiro. Evidência visual: `output/prototipo/menu-sobreposto.jpg`.

Sugestões para a versão definitiva, ainda NÃO implementadas: (1) melhorar cobertura e consistência de tags antes de ampliar catálogo; (2) separar filtros obrigatórios de preferências graduais com pesos manuais; (3) reduzir repetições de franquias e permitir controle determinístico de diversidade; (4) onboarding manual com favoritos e temas; (5) avaliação humana com protocolo congelado e comparação geral/personalizada; (6) detalhar decomposição de score e ausência de metadados; (7) congelar snapshots experimentais permitidos e versões de parâmetros para reprodução; (8) instalador/iniciador e recuperação de falhas de rede. Prioridade proposta: qualidade dos metadados e avaliação, antes de login privado e recursos sociais. Todas essas opções podem manter o motor estático, sem treinamento no programa.

## Atualização: evidência do uso das sinopses e diagnóstico de cobertura

A sinopse participa do motor desde a primeira versão. A pontuação geral é `B = 0.8 * ((cos_ancora + 1)/2) + 0.2 * Jaccard_temas`. O perfil pessoal, quando há vetor disponível, é `P = 0.6 * ((cos_perfil + 1)/2) + 0.4 * afinidade_temas`. O resultado personalizado é `(1-lambda)*B + lambda*P`. Com lambda=0.35, os coeficientes são 0.52 para sinopse da âncora, 0.13 para temas da âncora, 0.21 para sinopses do perfil e 0.14 para temas do perfil. São coeficientes da fórmula; não percentuais de precisão, nem necessariamente a proporção observada de cada parcela do score. Se não houver vetor do perfil, a afinidade temática ocupa todo o componente pessoal.

A média ponderada dos vetores das palavras representa apenas o trecho usado, de até 80 palavras; não é uma leitura contextual completa da sinopse. Sinopses já congeladas no índice mantêm sua representação original do experimento. Não usamos o título sozinho como substituto semântico de uma sinopse ausente. Quando a descrição AniList falta, pode ser reutilizado o texto do catálogo imutável da mesma obra.

Agora cada resultado inclui `contributions`: `anchor_text`, `anchor_topics`, `profile_text`, `profile_topics`. Esses quatro valores já incluem o fator lambda e somam o score personalizado. Para a lista geral, a interface apresenta separadamente as duas parcelas de B. A tabela evita confundir o cosseno bruto com sua contribuição após normalização e pesos. A resposta JSON exportada também contém essas parcelas.

`quality` informa quantas palavras tokenizadas estão no vocabulário e fora dele, sua proporção reconhecida e a presença de tags, gêneros e status. `anchor_quality` faz o mesmo para a âncora. Palavras são ocorrências, não termos únicos. A proporção de vocabulário reconhecido não mede relevância ou compreensão. O limite de 80 palavras é aplicado antes da tokenização, então a contagem de tokens pode diferir por pontuação/hífens.

`metadata_coverage` resume presença de texto, tags, gêneros e status no conjunto de candidatos ANTES dos filtros. Presença de texto não garante uma sinopse informativa, nem presença de tags garante anotação completa. Não houve nova coleta em massa nem alteração dos vetores para produzir o diagnóstico. A avaliação da qualidade dos metadados deve anteceder qualquer alegação de filtro infalível.

Validação: oito testes passaram em 5,672 s, com perfis temporários e sem rede. O novo teste confirma que (a) mudar apenas o texto, mantendo gêneros/tags iguais, altera a representação; (b) a soma das contribuições reproduz o score personalizado; (c) palavras reconhecidas e desconhecidas somam a contagem total; (d) uma palavra artificial fora do vocabulário tem cobertura zero. Sintaxe JavaScript verificada com Node. Esta mudança adiciona diagnóstico e explicações; não ajusta pesos para melhorar artificialmente os resultados nem altera relatórios comparativos anteriores.

Verificação integrada adicional: para Lycoris Recoil, 82 de 85 tokens reconhecidos (96,5%); entre 1.064 candidatos, todos tinham texto/gêneros, mas somente 97 tinham tags e status registrados no conjunto consultado. Isso identifica a desigualdade de cobertura como prioridade real de melhoria. Para Noir, as parcelas pessoais foram 0,501513 (texto da âncora), 0,028889 (temas da âncora), 0,207222 (texto do perfil), 0,048018 (temas do perfil), total 0,785642. Evidência: `output/prototipo/verificacao-sinopses.json`. Diagnóstico e tabela conferidos na interface; screenshot em `output/prototipo/explicacao-sinopse.jpg`. Essas observações são inspeção de um caso, não avaliação de relevância.

## Sinopses inteiras — versão ir-v2-full-synopsis

A pedido do usuário, o protocolo do APLICATIVO agora usa todo o texto de sinopse disponível na fonte, sem truncamento por quantidade de palavras. Isso abrange âncora pesquisada, candidatos locais/remotos e sinopses que compõem o perfil. O tamanho das listas, limite de metadados do perfil e número de candidatos remotos continuam delimitados; esses limites não cortam cada sinopse.

O catálogo resumido do experimento não podia recuperar palavras removidas. Por isso, o motor faz a correspondência por MAL_ID dos mesmos 1.000 títulos com `laboratorio/anime-en-20261105/data/raw/anime_with_synopsis.csv`, coluna original `sypnopsis`, e carrega o texto completo. Falta de uma sinopse original impede inicialização em vez de usar silenciosamente a versão curta. O arquivo bruto já existia: não houve novo download de dataset. O código remove somente marcação HTML e normaliza espaços/entidades. Não resume ou traduz o texto.

Para descrições do AniList, `materialize` mantém toda a descrição recebida. Se ela não existir, pode reutilizar a sinopse completa do catálogo original para o mesmo ID. “Completa” significa sem corte feito pelo aplicativo; não podemos garantir que a fonte tenha uma sinopse detalhada ou que corresponda ao enredo integral da obra. Texto vazio continua sem representação válida; palavras fora do vocabulário continuam ignoradas.

O índice científico antigo não é mais reutilizado pelo aplicativo. Em cada inicialização, reconstruímos as médias ponderadas a partir das sinopses inteiras. O IDF é calculado sobre os mesmos 1.000 documentos completos: `idf(t) = log((1+N)/(1+df(t))) + 1`. Para termo conhecido do Word2Vec mas ausente do catálogo, usamos `log(1+N)+1`. DF conta documentos contendo o termo; não ocorrências totais. Trata-se de estatística determinística de indexação da coleção, sem treinamento de embeddings. O modelo Word2Vec continua congelado, com as mesmas 100 dimensões. Os pesos 80/20, 60/40 e lambda padrão 0,35 foram preservados.

O campo de parâmetros `document_words` agora é null (sem limite), `synopsis_policy=entire_available_source`, `idf_policy=full_local_catalog_smooth`, `version=ir-v2-full-synopsis`. Novos campos `synopsis_source` e `synopsis_complete` registram a fonte textual e se o aplicativo usa a versão integral da fonte. Os parâmetros e os scores podem mudar em relação a ir-v1, pois tanto os textos quanto seu IDF mudaram. Não atribuir uma diferença apenas à extensão da sinopse sem experimento controlado que separe os fatores.

Os registros importados ricos já mantinham `description` original no perfil privado; só a representação em memória era cortada. Um favorito manual antigo guardava apenas o resumo público. O script `migrate_full_synopses.py` recuperou esse favorito na API oficial e gravou uma nova snapshot, preservando os demais dados e a cópia anterior. Foi executado com servidor parado. O script coleta somente os favoritos antigos ainda sem marcador de texto completo (máximo de 30 favoritos da aplicação), interrompendo sem gravar em caso de falha; não reimporta todo o histórico ou espelha o AniList.

Procedimento para uma cópia antiga desta instalação: parar servidor, executar no ambiente Python WSL `python migrate_full_synopses.py`, iniciar novamente. A instalação atual já foi migrada. Favoritos adicionados a partir desta versão guardam o texto completo. Restaurar manualmente um backup de perfil anterior pode exigir nova migração. Dados privados continuam fora do pacote/OneDrive.

Validação: nove testes passaram em 7,303 s. O teste adicional usa uma descrição com mais de 100 palavras, verifica a preservação das palavras finais e confirma que elas alteram o vetor em relação às primeiras 80. Verifica também que o catálogo local utiliza sinopses originais completas. Os testes anteriores cobrem score, perfil estável e filtros. Nenhum teste treina o modelo.

Integração real: Lycoris Recoil teve 127 tokens na sinopse inteira, 124 reconhecidos pelo vocabulário; antes eram 85 tokens no trecho de 80 palavras separadas por espaços. Noir teve 126 tokens, 120 reconhecidos. São tokenizações, não comparação literal de número de palavras. Cálculo local pontual 254,95 ms e pedido completo 6.022,96 ms (inclui rede). Noir permaneceu no topo pessoal, com score 0,791174; isso não demonstra melhoria de relevância. Evidência: `output/prototipo/verificacao-sinopses-inteiras.json`.

Os relatórios congelados de comparação entre modelos mantêm as entradas originais de 80 palavras, necessárias àquele protocolo comum aos modelos locais. Não alteramos seus arquivos, métricas ou conclusões retroativamente. Um futuro comparativo com sinopses inteiras deverá ter nova versão, entradas comuns e tratamento explícito dos limites de contexto dos modelos comparados.


