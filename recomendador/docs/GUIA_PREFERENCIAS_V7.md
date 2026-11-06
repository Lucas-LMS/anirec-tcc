# Preferências e recomendações — versão ir-v7-guided-profile

Atualização de 06/11/2026. A interface e o fluxo são compartilhados entre local e online. Online: https://anirec-ri-animes.givingbamboo.chatgpt.site. Local: http://127.0.0.1:8765.

## Criar um perfil sem conta ou notas

Clique em **Montar minhas preferências**. O assistente tem três etapas: gêneros, tags e favoritos. Sugere cerca de três de cada, mas permite pular etapas e não exige avaliações. Gêneros têm sugestões e lista completa. Tags têm sugestões, busca, categorias e definições oficiais em inglês. Favoritos têm sugestões de popularidade do AniList e busca por outras obras. A gravação acontece apenas ao concluir; cancelar preserva o perfil anterior.

Favoritar sem nota fornece um sinal positivo explícito, com peso 2. Não cria uma avaliação fictícia no AniList. Notas importadas usam a escala observada do usuário: ponto neutro = (menor nota + maior nota)/2. Para notas de 5 a 10, neutro = 7,5. Todas as avaliações entram no perfil; não selecionamos apenas as mais altas. Centroides positivos e negativos são normalizados separadamente.

## Duas listas em cada modo

**Geral** usa a obra de referência. **Para mim** combina a referência com o perfil. Em cada modo há duas colunas, com até dez resultados cada: **Todos os títulos**, que admite obras vistas, e **Para descobrir**, que exclui obras iniciadas/conhecidas e favoritos manuais. Planejados podem aparecer. Uma obra iniciada sem nota também é excluída de descobertas. Ambas usam o mesmo universo e filtros; não precisam ter resultados diferentes se o usuário ainda não conhece nenhum candidato.

O limite de dez é de apresentação, não de importação de histórico. A personalizada mantém uma vizinhança temática da referência: limite padrão 0,25; opções 0,15 e 0 permitem ampliar. Se existem apenas dois resultados inéditos elegíveis, mostramos dois: não completamos dez com itens que violam os filtros. Consultas adicionais podem buscar candidatos relacionados e inéditos por tema. A base continua sendo um recorte, não todo o catálogo do AniList.

## Por que a afinidade era 0,281?

A versão anterior dividia a soma assinada de interesses correspondidos pela massa global de pesos positivos e negativos. Assim, uma preferência negativa ausente da obra ainda aumentava o denominador e reduzia a afinidade. Esse efeito duplicava a penalização e dificultava interpretar o valor.

Foram avaliadas quatro alternativas sobre o mesmo perfil e candidato **Noir**: fórmula global anterior 0,280556; cobertura somente positiva 0,615531; cobertura com contrapesos separados 0,526894; cosseno positivo 0,213529. Não são medidas intercambiáveis nem quatro estimativas de probabilidade.

A nova fórmula é **cobertura positiva × (1 − cobertura negativa)**. Cada cobertura divide a soma de pesos de interesses encontrados, multiplicados pela intensidade da tag da obra, pela massa dos interesses daquele sinal. No exemplo: 0,615531 × (1 − 0,144001) = 0,526894. Preferências negativas ausentes deixam de diluir os positivos. Aversões presentes continuam reduzindo o resultado. Gêneros correspondidos têm intensidade 1; tags usam rank normalizado. Sem interesses positivos, mas com negativos, a cobertura positiva neutra é 0,5; sem interesses, a afinidade é zero.

A afinidade inclui interesses inferidos do histórico inteiro, não apenas as tags explicitamente escolhidas. Portanto não atingir 0,9 é esperado: isso exigiria cobertura quase completa dos interesses positivos e pouco contrapeso negativo. A tela mostra interesses explícitos correspondidos e as duas coberturas. Não usamos normalização pelo melhor candidato, que poderia apresentar uma lista fraca como excelente.

## Parâmetros do ranking

Referência: 50% sinopse + 50% temas. Sinopse: média ponderada por IDF dos vetores Word2Vec fixos, sinopse inglesa inteira; cosseno convertido de [-1,1] para [0,1]. Temas: 85% cosseno de tags com rank/IDF e 15% Jaccard de gêneros. Perfil: 70% contraste textual positivo/negativo e 30% afinidade temática; se não há sinal textual, usa a afinidade temática. Combinação final: (1 − influência) × referência + influência × perfil. Influência padrão 35%, ajustável até 60%. Exclusões explícitas permanecem filtros.

As parcelas mostradas já incluem os pesos. Por exemplo, uma parcela com máximo 0,105 não pode atingir 0,9. O índice final ordena candidatos: 0,60 não é 60% de chance de gostar. Word2Vec captura associações de palavras; a média não compreende ordem, negação e contexto como um modelo contextual. Melhora de fórmula não demonstra melhora de relevância: precisamos de julgamentos humanos e avaliação de ranking para essa conclusão.

## Igualdade entre local e online

O catálogo público passou de 204 para 2.495 obras não adultas do snapshot operacional de 2.507. Publicamos apenas campos de obras, sinopses e vetores, sem notas, lista de usuário, nome de usuário ou perfil privado. A seleção contém viés de uso e popularidade; não representa uma amostra aleatória. IDF e vetores são congelados para que navegar não altere o perfil. Metadados novos são codificados com o mesmo modelo/IDF.

O navegador calcula com JavaScript; o servidor local usa Python. Quatro cenários de paridade (com notas, só favoritos, vazio e obra vista sem nota) passaram, com 72 comparações numéricas e diferença máxima 0,000000004686, tolerância 0,000001. Isso valida equivalência de cálculo nos cenários, não a qualidade das recomendações. Os 17 testes Python passaram, incluindo sinopse inteira, escala individual, exclusão, decomposição do score e cadastro sem notas.

Na importação online de teste: 2.940 entradas, 2.439 avaliadas, 2.518 iniciadas/conhecidas, zero registros indisponíveis. Metadados compatíveis e recentes do catálogo são reaproveitados; as páginas de histórico são sempre percorridas por completo. Para perfis importados na versão antiga, importe novamente para identificar também obras vistas sem nota. O perfil online fica no armazenamento deste navegador; o local fica na máquina. Não há sincronização automática entre os dois.

## Código e evidências

- `affinity.py`: nova afinidade e diagnóstico das coberturas.
- `engine.py`: ranking Python e gravação atômica do assistente.
- `shared/ir-core.js`: fórmulas JavaScript equivalentes.
- `shared/onboarding.js`, `shared/app.js`, `shared/app.css`: assistente, listas e interface comum.
- `online/browser-adapter.js`, `online/anilist-import.js`: persistência no navegador e importação pública.
- `build_online.py`: exportação de campos públicos e modelo estático fragmentado.
- `test_affinity.py`, `test_engine.py`, `test_etl.py`, `test_ir_core.js`: verificações.
- `../output/prototipo/afinidade-v7/comparacao-formulas.json` (a partir da raiz do projeto): valores auditados; `output/prototipo/listas-vistos-descobertas-v7.json`: integração local com expansão de candidatos.

Exemplo de execução dos testes, no ambiente WSL já instalado:

```bash
python -m unittest test_engine test_etl test_affinity -v
python prepare_parity_fixture.py
node test_ir_core.js ../tmp/parity-v7.json
```

Os resultados dos comparativos científicos anteriores permanecem com seus protocolos originais. Esta atualização do aplicativo não os recalcula nem altera suas conclusões.
