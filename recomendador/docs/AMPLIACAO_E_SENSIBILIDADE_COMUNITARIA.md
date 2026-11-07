# Ampliação e sensibilidade comunitária — 7/11/2026

## Inventário real

Catálogo publicado e ativo: 3.413 obras. Banco local de origem: 3.698 registros AniList. Uma extração offline dos registros já coletados resultou em SQLite de pesquisa com 3.685 animes não adultos, 272 além do snapshot ativo e seis sem sinopse. Não houve download de obras nesta etapa. A base de pesquisa não substituiu o snapshot do motor: seus vetores e IDF ainda precisam ser reconstruídos e validados antes de ativação. Ela não contém notas de usuários ou nomes de usuário. Artefatos locais: output/dataset-expansion/anilist-research-expanded.sqlite3 e expansion-audit.json. Verificação PRAGMA integrity_check: ok.

## Meta e escopo pendente

Meta proposta: superar 10 mil obras, começando com um corpus delimitado de 10.500 animes, não com um espelho integral. Critérios de seleção devem cobrir décadas, formatos, gêneros e popularidade, com deduplicação por ID e quotas documentadas. Não limitar o corpus aos gostos de um usuário nem usar apenas as obras populares. Obras sem sinopse permanecem identificadas como metadados incompletos; não inventar texto para completar o número. Separar contagem de obras, obras vetorizáveis e grupos de franquias.

Os termos atuais proíbem hoarding/mass collection e mencionam flexibilidade educacional. Fonte verificada: https://raw.githubusercontent.com/AniList/docs/master/docs/guide/terms-of-use.md. A menção educacional não é confirmação específica do pedido de coleta ampla. O pedido de autorização previamente enviado permanece sem resposta localizada na consulta desta data. Não foram enviadas novas mensagens. Não foi iniciado coletor de catálogo integral ou coleta massiva lenta. A meta >10K não foi alcançada nesta etapa.

Antes da aquisição ampla, confirmar escopo autorizado: limite e campos, retenção SQL local, demonstração online, redistribuição de metadados e vetores, atualização e atribuição. Após essa definição, o protocolo deve ter orçamento explícito de obras/requisições, respeito ao rate limit e Retry-After, checkpoints, cache, deduplicação, interrupção por limite, origem e data por registro. O plano é proposto, não um coletor em execução nem permissão concedida.

Para ativação de cada snapshot: validar campos e IDs, preservar texto original e tratado, registrar viés de seleção, gerar hash, recalcular IDF e vetores dos modelos estáticos sem treinamento, reconstruir SQLite público sem dados pessoais, testar paridade e separar a avaliação do efeito de mudar o catálogo daquela de mudar o ranking. Preservar snapshot anterior. Não atribuir automaticamente a melhoria de ranking ao algoritmo quando os candidatos também mudaram.

## Comparação dos pesos comunitários

Execução reproduzível: `node scripts/research_community_weights.js`. Saída: data/community-weight-sensitivity.json. Nove referências, catálogo congelado, modo sem perfil, mesmos candidatos e agrupamento, pesos 0, 0,10, 0,20 e 0,35, escala de suporte 20. Fórmula S + peso × v/(v+20) × (1−S), v=max(0,saldo). Sem saldo positivo mantém o score; a posição pode mudar quando outros recebem bônus.

Em Lycoris Recoil, Release the Spyce: 174 → 62 → 28 → 12. Em Spirited Away, interseção com o top 10 de conteúdo: 10 → 7 → 5 → 1; em Monster: 10 → 10 → 8 → 8. Logo o mesmo peso tem impacto diferente conforme referência, suporte e proximidade dos scores. Isso justifica avaliar o peso, não escolher 0,35 apenas porque resolve um exemplo.

Não foram calculadas Precision@10 ou nDCG@10 porque faltam julgamentos independentes completos. Os votos que entram no ranking não são usados como gabarito. Todas essas nove referências possuem evidência comunitária; o conjunto ainda não representa casos sem votos nem valida desempenho em referências pequenas. No relatório, `no_positive_evidence_at_10` conta séries cujo melhor membro não possui saldo positivo observado, e não obras sem votos em todo o serviço. Relações de Code Geass têm cobertura parcial. O teste é sensibilidade descritiva, não validação de precisão ou recomendação de peso ótimo. O site mantém a configuração anterior, sem alteração nesta execução.
