# Minha lista em números — método e execução

A página `perfil.html` calcula um ranking próprio a partir da lista pública importada. Ela não depende das primeiras 30 tags das estatísticas do AniList. Tabelas, gráficos e ordenação são executados no navegador ou no backend local. Nenhum perfil individual fica embutido nos arquivos públicos do site.

## Entrada e recortes

Importamos todas as entradas da lista, com paginação, deduplicação por AniList ID e sem corte por nota. Para cada entrada guardamos estado, nota em POINT_100, progresso e repetições. Para as obras, preservamos todos os gêneros/tags disponíveis, episódios e duração média por episódio. Obras sem nota e planejados também recebem metadados para o relatório; isso não os transforma em curtidas nem em obras assistidas.

Os recortes são:

- **Concluídas:** estado COMPLETED.
- **Iniciadas:** COMPLETED, CURRENT, REPEATING, PAUSED ou DROPPED.
- **Lista inteira:** todas as entradas, inclusive PLANNING.
- **Planejados:** somente PLANNING.

Cada obra conta uma vez em cada gênero ou tag presente. Na contagem de tags, consideramos qualquer presença registrada nos metadados, inclusive ranks baixos; isso é diferente do corte rank ≥50 usado na similaridade temática entre animes. A mesma obra em listas personalizadas duplicadas não é contada duas vezes. Revisitas completas aparecem em coluna separada. É possível ordenar por obras únicas ou por quantidade incluindo revisitas, sem confundir os dois números.

## Notas

A média é a média aritmética das notas pessoais fornecidas no recorte. Nota zero é ausência de avaliação, não uma reprovação. A tabela mostra quantas obras têm nota, pois seu denominador pode ser menor que o total de obras. A interface converte POINT_100 para escala de 0–10.

Não usamos `Media.averageScore` ou `Media.meanScore`, que são notas comunitárias, para calcular a média do usuário. As estatísticas podem diferir dos agregados exibidos pelo AniList por recorte, revisitas, metadados, atualização e critérios próprios do serviço; não afirmamos reproduzir sua fórmula interna.

## Tempo: duas estimativas diferentes

```text
assistido estimado = duração × (progresso + revisitas completas × episódios)
duração total das obras = duração × episódios
```

O primeiro utiliza progresso registrado e inclui revisitas. O segundo conta uma execução completa de cada obra única do recorte. Por isso, uma pessoa que reassiste pode ter tempo assistido maior que a duração única de suas obras concluídas.

Planejados contribuem com zero para o assistido. Sua duração total estimada é apresentada à parte. Se uma obra concluída não tiver progresso informado, inferimos o total de episódios e contabilizamos quantas vezes isso ocorreu; progresso zero explicitamente informado não é substituído silenciosamente.

Episódios ou duração ausentes/zero permanecem desconhecidos. Não usamos 24 minutos ou 12 episódios como preenchimentos arbitrários. Há contadores de cobertura por tema e no resumo. O total exibido é parcial quando há dados desconhecidos. Séries em lançamento podem não ter sua duração final conhecida.

Isso é uma estimativa, não um cronômetro: não sabemos se houve abertura pulada, velocidade acelerada, pausas ou reassistidas parciais não registradas.

**Sobreposição:** um anime pode pertencer a Comedy, Drama e várias tags. Seu tempo participa de cada um desses grupos. Somar todos os gêneros ou tags gera contagem repetida; o total único correto vem do resumo por obras do recorte.

## Gráficos e tabela

Os gráficos mostram dez gêneros e dez tags por quantidade, apenas para leitura. A tabela contém todos os temas com dados no recorte, com busca e ordenação por quantidade, média ou tempo. O limite de dez do gráfico não limita o perfil nem o conjunto exportado.

O JSON exportado contém estatísticas agregadas do perfil e pode conter opiniões pessoais. Fica no dispositivo até uma ação explícita do usuário para compartilhar; não há publicação automática.

## Integração com o perfil de recomendação

Quando a lista completa está disponível, a inferência temática usa as estatísticas próprias do recorte de iniciados. Continua aplicando frequência com peso 65% e avaliação relativa com 35%, além da regra documentada de favoritos. Todos os temas com suporte participam. As notas continuam formando também os centroides textuais; o modelo estático e o texto completo são preservados.

Perfis antigos no navegador podem não ter guardado estados e progresso completos. Ao abrir a página com um usuário já importado, fazemos uma atualização única da lista pública, com progresso visível. Sem usuário salvo, a página pede o nome. Preferências manuais são preservadas. O backend local dispõe das entradas completas após a atualização.

## Código e testes

- `user_statistics.py`: cálculo Python, sem rede.
- `shared/user-statistics.js`: cálculo equivalente no navegador.
- `shared/profile-page.html` e `online/lab/profile-dashboard.js`: página, gráficos e tabela.
- `anilist_client.py` e `online/anilist-import.js`: paginação, entrada completa e metadados.
- `test_user_statistics.py`: estados, deduplicação, revisitas, médias sem nota e duração ausente.
- `prepare_statistics_fixture.py` / `test_user_statistics.js`: equivalência Python/JavaScript nos quatro recortes.

Exemplo sintético: série com 12 episódios de 24 minutos, progresso 12 e uma revisita completa: assistido estimado 576 minutos; duração única 288 minutos; uma obra e uma revisita. Um filme planejado de 95 minutos soma 95 ao catálogo e zero ao assistido. Um episódio com duração desconhecida não recebe uma duração inventada.

A atualização local preservou um backup privado antes da reimportação. Metadados reaproveitados do cache e sem alteração não recebem artificialmente uma nova data de coleta no repositório operacional. O banco público continua separado do perfil e tem somente dados de obras e relações oficiais.
