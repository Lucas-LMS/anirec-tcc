# Exemplo executável de recuperação estática

Este exemplo começa a demonstrar o mecanismo do produto após os comparativos. Não é a interface final, não importa o histórico pessoal e não mede qualidade de personalização. Usa o catálogo de 1.000 sinopses inglesas e os índices já calculados no benchmark. Não faz novas chamadas de API, não usa LLM, não carrega um classificador e não treina ou ajusta embeddings.

Arquivo: `demo_ir_estatico.py`. Depende apenas de Python e NumPy. Pode ser executado no ambiente Linux já existente `.venv-word2vec-py312` ou no runtime Windows de documentos. Os pesos dos vetores de documentos permanecem fixos.

## Como funciona

1. Ler o catálogo e a matriz `.npy` de documentos, mantendo a correspondência entre posição da linha e ID. Por padrão usa Word2Vec Skip-gram, o candidato estático provisório da rodada de recuperação. `--model` permite os outros estáticos, com os índices já preservados.
2. Procurar o anime escolhido por título exato ou MAL ID. O título identifica a entrada; não tratamos o nome isolado como se fosse a sinopse.
3. Sem favoritos, pontuar cada candidato por produto escalar entre os vetores normalizados da sinopse do candidato e da âncora. Isso é similaridade cosseno, não probabilidade de gostar.
4. Com favoritos, tirar a média dos seus vetores e normalizar o resultado para obter o vetor do perfil. É agregação determinística, sem aprendizado de parâmetros.
5. Combinar os scores: `score = alpha * similaridade_ancora + (1-alpha) * similaridade_perfil`. Valor inicial alpha=0,7, portanto 70% âncora e 30% perfil. Esse é um parâmetro de engenharia não otimizado nem validado cientificamente. O exemplo limita alpha a 0,4..1 para manter influência da âncora.
6. Excluir a própria âncora e os favoritos da lista retornada. Ordenar por score; empates exibidos por MAL ID. Isso é uma demonstração de operação, diferente da integração de empates usada nas métricas do benchmark.

## Comandos

No terminal, a partir da pasta TCC, com Python e NumPy disponíveis:

```powershell
python recomendador/demo_ir_estatico.py --list
python recomendador/demo_ir_estatico.py --anime 47
python recomendador/demo_ir_estatico.py --anime 47 --favorite 144 --favorite 387 --alpha 0.7
```

Os IDs acima foram verificados nesta amostra: Akira (47), Kanon (144) e Haibane Renmei (387). Os favoritos são fictícios para demonstrar a operação; não representam o histórico do usuário. Também é possível substituir pelos números exibidos no primeiro comando.

Comando completo no PowerShell usando o ambiente WSL que já tem NumPy:

```powershell
wsl -d Ubuntu -- /home/lucas/tcc-lab/.venv-word2vec-py312/bin/python "/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/recomendador/demo_ir_estatico.py" --anime 47 --favorite 144 --favorite 387 --alpha 0.7
```

As duas operações foram executadas e seus JSONs estão em `output/demo-ir-estatico`. A lista mudou com os favoritos, mas isso só confirma a combinação de pesos, não a qualidade humana dessas sugestões. Scores próximos de 0,94 não significam 94% de chance de gostar: são similaridades de representações médias, que podem se concentrar em uma faixa alta. Será necessário avaliar discriminação e relevância no produto.

Na primeira listagem em Windows, o console CP1252 não conseguiu imprimir o caractere estrela de um título. O código passou a configurar stdout como UTF-8 e a listagem e os dois modos funcionaram. Essa correção de exibição não muda os vetores ou rankings do benchmark.

O JSON informa os componentes de semelhança, os pesos e os gêneros da fonte. Não inventa justificativas de enredo. Se o título não estiver na amostra, informa isso em vez de trocar silenciosamente por outro. A base de 2020 não atende necessariamente aos exemplos atuais do produto; Lycoris Recoil e tags finas exigirão dados adequados na fase AniList.

## O que falta para o produto

Interface básica; pesquisa AniList sob demanda; entrada/persistência de preferências; importação limitada da lista pública autorizada; tags como Yuri e Cute Girls Doing Cute Things; controle de itens vistos e de relações de franquia; explicações determinísticas; validação anime-para-anime e de perfis com relevância revisada por pessoas. Um vetor médio de favoritos sozinho não comprova compreensão de todas essas preferências.

O cliente inicial `anilist_client.py` foi preparado para consultas públicas de leitura e já localizou o usuário informado. Isso não significa que a lista inteira foi importada ou que login OAuth está implementado. Não solicitar senha AniList ao usuário; acesso privado, se necessário futuramente, exigirá o fluxo oficial de autorização.
