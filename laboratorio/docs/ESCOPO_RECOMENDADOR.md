# Escopo do produto confirmado por Lucas

Atualização de 05/11/2026, durante os comparativos. O objetivo é recomendação anime-para-anime, com um modelo estático principal. Não reduzir o produto a busca por palavras ou classificação de gêneros.

**Restrição técnica explicitamente confirmada:** Lucas autorizou vetores estáticos pré-treinados (GloVe/Word2Vec/fastText), sem treinamento ou ajuste de modelos no programa. O sistema final seguirá recuperação da informação: indexação, similaridade e combinação determinística de pesos. Não usar regressão logística, MiniLM, LLM, fine-tuning, learning-to-rank ou otimização aprendida no produto final. Esses sistemas podem continuar em experimentos comparativos identificados separadamente. Preferências e histórico fornecem pesos por regras aritméticas explícitas, não um modelo treinado. Na redação, reconhecer que os vetores foram originalmente aprendidos pelos seus autores; não afirmar que embeddings não têm origem em aprendizado de máquina. TF-IDF/BM25 permanecem baselines e alternativas de RI.

## Duas modalidades

1. Sem perfil: pesquisar/selecionar um anime, por exemplo Steins;Gate, e recuperar títulos parecidos. Não exigir login. O anime escolhido é a âncora; não é somente uma string de consulta. Usar seu texto e metadados para a representação.
2. Com perfil: manter a âncora, mas ajustar o ranking pelos gostos explícitos e pelo histórico. Exemplo do usuário: Lycoris Recoil pode aproximar Princess Principal por combinar ação com os elementos que ele procura, como relações entre garotas e cotidiano. Isso é um exemplo de intenção, não um rótulo de verdade universal nem promessa de uma posição predeterminada.

Consultas de gênero do benchmark English anime são diagnósticos de recuperação/negação. Sozinhas não avaliam o produto inteiro nem personalização. Será necessária uma avaliação adicional de anime-para-anime e perfil, com cenários de afinidade e preservação da âncora. Não alterar os qrels já congelados para acomodar o exemplo desejado.

## Perfil e interface inicial

Recomendação: interface local simples e funcional, com pesquisa/seleção da âncora, alternância geral/personalizado, controle de intensidade da personalização, preferências editáveis, importação de lista pública por username, explicação dos componentes do score e opção de excluir itens já vistos. Permitir uso integral sem conta externa.

Preferências explícitas: temas/tags/gêneros, animes favoritos, itens não desejados. Importação: notas, favoritos e estado da lista. Assistiu não significa gostou; planejados não devem ser tratados como positivos, nota ausente não deve virar zero/aversão, abandono não significa automaticamente rejeição temática. Exibir de onde veio cada sinal e permitir correção pelo usuário.

Tags específicas importam: Yuri e Cute Girls Doing Cute Things não são bem representadas apenas por gêneros amplos. A taxonomia real deve ser consultada no AniList; não inventar equivalência automática entre romance, elenco feminino e Yuri. Não explicar uma recomendação como contendo um tema que não foi identificado nos dados.

O histórico pessoal de Lucas foi autorizado pelo username público `banthisworld`. Importar de forma limitada e guardar localmente em pasta privada de perfil, separada dos corpora e relatórios públicos. Não inserir sua lista como verdade de avaliação dos benchmarks já congelados.

## Pontuação proposta, a validar

Calcular separadamente: semelhança da sinopse com a âncora; proximidade temática da âncora; afinidade com o vetor do perfil; aderência a tags explícitas; exclusões/penalidades de itens vistos ou rejeitados. Normalizar e documentar componentes antes de combinar, mostrando que score não é probabilidade de gostar. Manter peso positivo da âncora para a personalização não virar uma lista genérica de favoritos.

Pesos iniciais são decisões de engenharia, não resultados já validados. Realizar ablação: sem perfil, só temas explícitos, só histórico e combinação. Verificar mudança de ranking sem perder semelhança com a âncora. Não forçar Princess Principal ao topo apenas para satisfazer o exemplo: mostrar o resultado real e seus componentes. O questionário resolve cold start; o histórico pode melhorar a evidência, mas também reproduzir vieses e interesses antigos.

## AniList: possibilidades verificadas na documentação oficial

Dados de anime e listas públicas não exigem autenticação. É possível login OAuth2 para dados privados. Authorization Code requer aplicação registrada, redirect URI coincidente e credenciais de aplicação no servidor. Não pedir senha AniList no nosso formulário. A implementação inicial pode importar lista pública por username; OAuth pode ser acrescentado sem tornar login obrigatório.

Fontes: https://docs.anilist.co/guide/auth/ ; https://docs.anilist.co/guide/auth/authorization-code ; https://docs.anilist.co/guide/graphql/queries/media-list . A documentação informa que não há scopes e tokens têm acesso amplo; não apresentar OAuth como uma permissão tecnicamente restrita só à leitura. Nosso aplicativo deve usar apenas consultas, sem modificar listas.

A API está documentada com limite temporário de 30 requisições/minuto e cabeçalhos para acompanhar cota; respeitar Retry-After. Consultar sob demanda e manter cache pequeno com expiração. Não criar espelho/mass collection de toda a base: os termos proíbem uso como backup/armazenamento e coleta em massa, embora indiquem flexibilidade para projetos educacionais. O projeto será recomendação complementar, não um novo tracker concorrente. Fontes: https://docs.anilist.co/guide/rate-limiting ; https://docs.anilist.co/guide/terms-of-use .

## Sequência autorizada

Concluir SMS, realizar comparação English anime, depois validar o fluxo do programa com âncora e perfil. Preparar código/documentação em paralelo não significa declarar essas fases concluídas. Notificar o usuário com resultados observados; nunca afirmar que uma execução terminou apenas porque há um supervisor em segundo plano.
