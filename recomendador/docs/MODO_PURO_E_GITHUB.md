# Recomendação pura e distribuição GitHub — 06/11/2026

## Entrada sem perfil

O programa abre em **Só animes parecidos — recomendação pura, sem perfil**. Basta pesquisar, selecionar a obra e aguardar a recomendação automática. Não é necessário cadastrar interesses, dar notas, importar histórico ou criar conta. O painel pessoal fica oculto nesse modo.

Mesmo existindo um perfil salvo, suas notas, favoritos, temas preferidos/evitados, obras ocultadas e lista de vistos são ignorados no cálculo e na seleção de candidatos. A lista exibida é única: animes parecidos. Não classificamos obras como vistas ou inéditas sem utilizar o histórico. A combinação permanece 50% sinopse inteira e 50% temas da referência. Os filtros gerais de catálogo, como lançamento, não são preferências pessoais.

O perfil é preservado. Para usá-lo, selecione **Com minhas preferências — Geral e Para mim**. Geral admite as exclusões pessoais; Para mim combina a referência com os sinais positivos e negativos do perfil, mantendo as duas listas de até dez resultados.

Na implementação Python, `Engine.recommend(..., pure=True)` não calcula sinais do perfil e zera a personalização. No JavaScript, `AniRecIR.rank({..., pure:true})` substitui os sinais pessoais por conjuntos vazios. A adaptação online separa candidatos neutros de obras que só entraram por importação do histórico. A busca de candidatos em modo puro usa apenas a referência, não tags do usuário. Isso evita que apenas zerar o peso pessoal deixe exclusões ou coleta personalizada escondidas no fluxo.

Testes Python e JavaScript com perfil adversarial (obras ocultadas, gêneros evitados, notas e favoritos) confirmam que o ranking puro permanece igual. Um teste adicional verifica que os vetores distribuídos são idênticos aos do modelo principal para uma palavra de referência. Os 22 testes Python passaram, além dos testes JavaScript de paridade e modo puro.

## Repositório e execução portátil

- Repositório público: https://github.com/Lucas-LMS/anirec-tcc
- Site principal distribuído pelo GitHub: https://lucas-lms.github.io/anirec-tcc/
- Pasta local do checkout: `github/anirec-tcc`, dentro do workspace de desenvolvimento.

O repositório inclui aplicação, vetores públicos, SQLite público, código científico anterior, relatórios, documentação e documentos acadêmicos. Perfis, notas/listas pessoais, chaves, inventários da máquina e logs de execução privados não foram enviados. Pesos brutos de LLMs e corpora brutos de aquisição não são necessários ao site e não foram incluídos; os protocolos indicam as fontes para reproduzir os experimentos históricos.

O site pronto fica em `site/`. Pode ser servido com `python -m http.server 8000 --directory site`. O backend Python dispõe de inicialização por snapshot público e fallback para os vetores fragmentados incluídos, eliminando a dependência do caminho do modelo na máquina de desenvolvimento.

O workflow `.github/workflows/pages.yml` instala o ambiente em um runner novo, executa os testes e valida a distribuição antes de publicar apenas `site/`. O Pages foi configurado para GitHub Actions. Caminhos relativos preservam os links no subdiretório `/anirec-tcc/`. O endereço anterior do Sites foi mantido e atualizado como espelho da interface; a publicação contínua do GitHub Pages acompanha os pushes em `main`.

Na implantação inicial, a validação passou, mas o primeiro deploy ocorreu antes da habilitação do Pages e retornou “Not Found”. Após habilitar Pages por API, a execução seguinte completou validação e publicação com sucesso. Esse foi um problema de configuração inicial, sem mudança nos resultados dos testes.

O README da raiz é a referência atual para execução. Os guias mais antigos registram protocolos e versões históricas. `scripts/build_site.py` sincroniza a publicação; `scripts/validate_distribution.py` verifica dados, links e conteúdo privado; `scripts/update_manifest.py` registra os hashes dos blobs Git preparados para distribuição. O manifesto exclui a si próprio para evitar autorreferência.
