# Piloto AniRec - execução de 29/10/2026

**Atualização de escopo:** Lucas confirmou que o sistema final usará modelos estáticos. MiniLM venceu este piloto, mas é contextual e permanece como comparador. A recomendação anterior de adotá-lo no TCC foi substituída; os resultados numéricos continuam válidos dentro das limitações. Ver [análise atualizada e alternativas estáticas/PT-EN](../docs/09-estaticos-llms-e-escopo-tcc.md).

Materiais da execução inicial, anteriores ao esclarecimento de escopo: [relatório detalhado](relatorios/RELATORIO_COMPARACAO.md), [painel offline](relatorios/painel-comparacao.html), [roteiro da reunião](relatorios/ROTEIRO_REUNIAO_15H.md) e [PDF](../../output/pdf/relatorio-comparacao-anirec.pdf). Ler suas recomendações junto da atualização acima; as predições e métricas não foram alteradas.

39 títulos reais; descrições, consultas e julgamentos preparados com IA, sem validação humana independente. Resultado exploratório, não benchmark oficial. O [protocolo](PROTOCOLO.md) antecede a inspeção dos rankings. O cenário principal PT_EN foi confirmado por Lucas.

## Arquivos e funções

| Arquivo | Função |
|---|---|
| codigo/01-treinar-word2vec-text8.py | Treina CBOW e Skip-gram fora do corpus anime; não usa relevâncias |
| codigo/02-criar-base.py | Cria catálogo, consultas, todos os pares julgados e congelamento; recusa sobrescrever freeze |
| codigo/03-codificar-modelo.py | Codifica um pipeline e salva scores/vetores; não lê julgamentos para produzir scores |
| codigo/04-rodar-codificadores.sh | Seleciona ambientes e executa os oito pipelines sequencialmente, preservando resultados existentes |
| codigo/05-avaliar.py | Calcula métricas com empates, verifica nDCG contra sklearn e faz bootstrap por intenção |
| codigo/06-gerar-relatorios.py | Gera Markdown, CSV agregado, gráfico PNG/SVG, HTML offline e PDF dos resultados prontos |
| dados/freeze.json | Hashes e procedência dos dados anteriores aos rankings |
| resultados/v1/ | Saídas originais por modelo, matrizes NPZ, metadados, tempo/RSS e exit code |
| resultados/resumo.json | Métricas, intervalos, cobertura, recursos, limitações e conferências |
| resultados/rankings.json | Todas as ordenações, scores e graus de relevância |
| resultados/metricas-por-consulta.csv | Métricas individuais, incluindo modelos Lee diagnósticos |
| resultados/metricas-agregadas.csv | Seis pipelines principais nos três cenários |

## Reexecutar com os modelos já instalados

No Ubuntu/WSL, o laboratório Linux está em `/home/lucas/tcc-lab`; os dados deste projeto ficam no diretório Windows montado. Exemplo no terminal WSL:

```bash
cd '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/piloto-animes'
bash codigo/04-rodar-codificadores.sh
/home/lucas/tcc-lab/.venv-sentences/bin/python codigo/05-avaliar.py
```

A orquestração preserva saídas existentes. Para uma nova execução de modelos, criar outra versão de saída e registrar a alteração; não apagar v1. Não é necessário retreinar Word2Vec nem recriar a base para recalcular métricas. O gerador da base exige o JSON original em `C:/tcc-lab/Pilot` (montado no WSL) e já foi executado. Os pesos e hashes dos novos Word2Vec estão em `/home/lucas/tcc-lab/Word2Vec/manifests/text8-piloto.json`.

No PowerShell, geração dos relatórios com o runtime utilizado nesta máquina:

```powershell
& 'C:/Users/lucas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' laboratorio/piloto-animes/codigo/06-gerar-relatorios.py
```

Esse runtime recebeu **matplotlib 3.11.2** para o gráfico e **PyMuPDF 2.0** para renderização/conferência do PDF; reportlab já estava disponível. pip também instalou dependências transitivas (contourpy, cycler, fonttools, kiwisolver, pyparsing, networkx, onnxruntime, pyyaml, psutil, tabulate, protobuf, flatbuffers, pymupdf-layout e pymupdf4llm). Esses pacotes de apresentação não alteram os ambientes dos modelos nem os resultados. A lista de versões efetivas está em `resultados/ambiente-relatorios.txt`. PyMuPDF foi usado somente para renderizar; o gerador usa reportlab e matplotlib. A geração pode ser feita em outro Python com essas duas bibliotecas.

Os ambientes dos modelos são separados: `.venv` (GloVe/CLI fastText e análise numérica), `.venv-word2vec-py312` (Gensim), `.venv-sentences` (Sentence Transformers/sklearn). Instalações oficiais, desvios de versão/épocas e seus motivos estão nos documentos e scripts do laboratório principal. Multithreading pode impedir reprodução bit a bit mesmo com seed; preservar pesos e hashes.

## Dados baixados nesta etapa

- Anime Offline Database release 2026-27: JSON completo de 62.331.136 bytes em `C:/tcc-lab/Pilot/anime-offline-database-2026-27.json`.
- SHA256: `395be786fb2f98f1fca9e963911b9332110098a080e7e2569902bbc5641d1a41`.
- URL: https://github.com/manami-project/anime-offline-database/releases/download/2026-27/anime-offline-database-minified.json
- Metadados da release, licença ODbL/DbCL e subconjunto com atribuição preservados em `dados/brutos/`.
- A fonte fornece a identificação dos títulos; as descrições deste piloto não foram baixadas dessa fonte e não são oficiais.
- Jikan foi tentado e não forneceu dados para este experimento.

Nenhum modelo adicional foi baixado para a comparação: reutilizamos os pesos existentes e treinamos dois Word2Vec adicionais com text8 já presente. Nenhum gerador GPT/Llama/DeepSeek foi instalado. Não houve ajuste com os julgamentos do piloto.

## Conferência e limites

1. 2.262 pares julgados, 58 consultas, 29 famílias.
2. nDCG conferido em 1.392 combinações modelo/cenário/consulta, erro máximo 3,33e-16.
3. Bootstrap exploratório com 5.000 amostras agrupadas por família.
4. Zero truncamentos no MiniLM; maior entrada com 60 de 128 tokens.
5. PDF renderizado e inspecionado visualmente; painel contém resultados salvos, não inferência ao vivo.

Não usar tempos em lote/cache como latência de API. Não usar nDCG como percentual de acurácia. Não interpretar a comparação de corpora e dimensões diferentes como efeito causal de arquitetura. O teste humano independente, o catálogo real e as medições do sistema permanecem como próximas etapas.
