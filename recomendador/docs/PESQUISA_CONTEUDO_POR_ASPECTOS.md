# Investigação por conteúdo — 7/11/2026

Status: hipótese de desenvolvimento, não aplicada em produção. Consulta pura: perfil e comunidade desligados; 3.413 obras no snapshot, 3.407 elegíveis. Mesmos filtros e agrupamento nas duas listas.

Resultado focal: Release the Spyce passa de 174 para 16 com a hipótese de aspectos. Não há regra por título: o ID de Lycoris/Spyce aparece apenas no script de avaliação. A função de pontuação usa gênero, categorias oficiais das tags, rank das tags e IDF.

Para cada categoria c em Theme-Action e Cast-Main Cast:

- Selecionar tags da referência com rank >=50.
- Peso de uma tag: rank/100 × sqrt(IDF).
- Normalizador: maior peso entre as tags da referência nessa categoria.
- Correspondência: máximo, entre tags da referência, de min(rank da referência, rank do candidato)/100 × sqrt(IDF), dividido pelo normalizador.
- A média geométrica das correspondências das duas categorias define F.
- Resultado: 0,5 × score anterior + 0,5 × F. O score anterior preserva a sinopse inteira. Sua contribuição final é 25%; os temas antigos, 25%; a nova combinação, 50%.

Se a referência não for Action ou faltar uma das duas categorias, preservar o método anterior. Um candidato sem correspondência em uma categoria recebe F=0; isso pode penalizar metadados incompletos e é limitação conhecida. Nenhum candidato elegível é excluído pelo experimento.

O IDF é um peso descritivo do snapshot, não treinamento de embeddings ou de classificador. Raiz do IDF reduz a dominância de tags raras comparada ao uso direto; a combinação de aspectos busca distinguir ação com determinado elenco de semelhanças contextuais como café/restaurante. É uma hipótese de projeto, não um método publicado cuja superioridade foi demonstrada.

Foram examinadas 64 configurações de métricas exatas de tags (Jaccard, Dice, cobertura e cosseno; quatro cortes e quatro expoentes), quatro modelos estáticos, seis configurações de aproximação semântica de tags, 12 combinações BM25 normalizadas por limite teórico, 16 configurações de pseudo-feedback e 27 de balanceamento por categorias. Nenhuma dessas famílias simples chegou ao top 20. Ablacões focadas e combinação de aspectos foram exploradas depois, com a referência focal já conhecida; portanto existe viés de seleção. Versões não normalizadas foram apenas protótipos e não sustentam conclusões nem scores de produção.

O teste final é reproduzível por `node scripts/research_content_facets.js`; dados em `data/content-facets-development.json`. Somente Lycoris e Code Geass ativaram a regra entre as nove referências; sete permaneceram idênticas e não validam o novo método. Em Code Geass, 86 caiu de terceiro para 17º, mostrando risco de perder elementos narrativos importantes. Fresh Precure! e The Apothecary Diaries aparecem no top 20 de Lycoris: precisam de julgamento humano. Não declarar precisão, nDCG ou superioridade global sem julgamentos independentes. Não usar votos comunitários como ingrediente desta experiência.

Código: `research/facet-content.js` calcula os dois aspectos e a mistura sem mutar entradas; `scripts/research_content_facets.js` carrega artefatos públicos, executa nove consultas puras, aplica o cálculo, verifica limites, conjunto de candidatos e peso zero, e grava as listas. O relatório visual local contém os dois rankings e as limitações. O site principal e sua fórmula permanecem inalterados.

Fonte das categorias: taxonomia AniList já registrada no snapshot. Vetores, IDF e grafo: artefatos públicos existentes. As páginas acadêmicas consultadas nesta execução não responderam; não atribuir a elas a proposta nova. Próxima validação: mais referências de ação e julgamentos cegos, separando desenvolvimento e avaliação.
