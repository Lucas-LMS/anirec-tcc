# Laboratório de representações textuais — AniRec

**Atualização final de 05/11/2026:** virtualização restaurada e WSL operacional. Os comparativos de [SMS](../output/comparacao-sms/relatorio-comparacao-sms.html) (13 pipelines, mesmos 200 exemplos) e de [anime em inglês](../output/comparacao-anime-en/relatorio-anime-en.html) (1.000 títulos, 24 consultas; recuperação e reranking separados) foram concluídos. Llama, DeepSeek destilado e Qwen estão instalados localmente; GPT-OSS 20B foi avaliado pela Groq Free, sem API paga. O Qwen SMS teve um timeout e foi retomado preservando as 185 respostas anteriores; o relatório registra a exceção de medição. Para iniciar a recuperação no produto, o candidato estático provisório é Word2Vec Skip-gram; fastText permanece concorrente importante. Isso não valida ainda anime-para-anime com perfil. A restrição confirmada é usar vetores estáticos prontos com RI e pesos determinísticos, sem treinamento ou ajuste de modelos no programa final. Os parágrafos históricos abaixo refletem fases anteriores e não substituem estes resultados novos.

Registro iniciado em **29/10/2026**, horário de Brasília. Objetivo desta etapa: aprender a instalar, treinar, carregar e avaliar as implementações oficiais antes de comparar modelos no catálogo de animes.

**Documentação consolidada:** [manual completo em PDF](../output/manual/manual-completo-anirec.pdf), [versão navegável em HTML](../output/manual/manual-completo-anirec.html) e [códigos e evidências em ZIP](../output/manual/anirec-evidencias-e-codigos.zip). O manual explica o histórico para leitores leigos e contém código completo, instruções de uso, resultados e limites. Os pesos grandes Linux não integram o ZIP.

## Situação registrada em 29/10 (histórico)

**Escopo confirmado:** o sistema final do TCC usará modelos estáticos. MiniLM permanece como comparador contextual; sua vitória no piloto não o torna candidato final dentro dessa restrição. O próximo candidato estático recomendado é fastText PT/EN alinhado, ainda não instalado/testado. Ver [análise de estáticos, LLMs e APIs](docs/09-estaticos-llms-e-escopo-tcc.md).

**GloVe, fastText, Word2Vec CBOW/Skip-gram e MiniLM multilíngue estão operacionais nos testes realizados no Ubuntu/WSL.** A avaliação Rare Words do fastText foi concluída usando cópia AWS corroborada com uma cópia acadêmica, mantendo o avaliador oficial. Um [piloto de busca de animes](piloto-animes/README.md) comparou seis pipelines principais e dois diagnósticos: MiniLM multilíngue obteve o maior nDCG no cenário PT/EN, mas não pertence à classe estática exigida para o sistema final. Os textos e julgamentos do piloto foram preparados com IA; a validação humana e o catálogo com sinopses reais ainda estão pendentes.

| Etapa | Situação |
|---|---|
| Inventário do computador | Executado; JSON em `manifests/` |
| Consulta às fontes oficiais | Executada; referências em `docs/04-fontes.md` |
| Código oficial GloVe | Baixado em `C:\tcc-lab\GloVe`; commit fixado no manifesto |
| Código oficial fastText | Baixado em `C:\tcc-lab\fastText`; tag v0.9.2 |
| Bases dos exemplos | text8 e enwik9 baixadas; consultar manifesto para integridade e arquivos extraídos |
| Pré-processamento fastText | Executado com o `wikifil.pl` oficial; `fil9` gerado, 713.069.767 bytes |
| Rare Words (RW) | Avaliação concluída em 2.034 pares, rho 0,4177; fonte original inacessível, cópia AWS com pares/notas corroborados |
| Ambiente de compilação | Instalado; GloVe com GCC 15 e fastText com G++ 12; NumPy/SciPy no ambiente virtual |
| Instalação Linux/WSL | Ubuntu 26.04.1 LTS validado no WSL 2 após reinicializar |
| GloVe | Demo oficial concluído: 23,50% de acurácia em analogias cobertas; cobertura 91,21% |
| fastText classificação | Tutorial cooking concluído, 3.000 exemplos de validação; P@1 0,151 e R@1 0,0652 |
| fastText embeddings | Treinamento em fil9 concluído; 218.316 entradas, 100 dimensões; carregamento, vetores e avaliação RW concluídos |
| Word2Vec | Gensim 4.4.0 em Python 3.12.16 separado; CBOW e Skip-gram treinados/testados no corpus Lee oficial |
| MiniLM multilíngue | Pesos oficiais baixados; 384 dimensões; encode e salvamento/carregamento local verificados em CPU |
| Doc2Vec e LLMs | Doc2Vec sem modelo treinado/testado; nenhum peso de LLM gerador instalado |

Não interpretar a existência de um diretório de código como instalação funcional. Somente compilação bem-sucedida e execução dos exemplos permitem essa classificação.

## Organização

- `docs/01-ambiente-e-decisoes.md`: diagnóstico e escolhas de plataforma.
- `docs/02-guia-de-execucao.md`: comandos, explicações, parâmetros e critérios de conclusão.
- `docs/03-modelos-e-metodologia.md`: modelos adicionais, viabilidade dos LLMs e cuidados experimentais.
- `docs/04-fontes.md`: fontes primárias e data de consulta.
- `docs/05-execucoes-reais.md`: ambiente validado, métricas observadas e limitações.
- `docs/06-word2vec.md`: instalação Gensim/Python separado e testes CBOW/Skip-gram no corpus Lee.
- `docs/07-rare-words-resolucao.md`: proveniência alternativa do RW, verificações e correlação observada.
- `docs/08-embeddings-sentencas.md`: instalação e teste do encoder MiniLM multilíngue.
- `scripts/`: automação própria que envolve os programas oficiais; não é código dos autores dos modelos.
- `logs/`: registros das operações realmente executadas.
- `manifests/`: hardware, hashes, versões e estado dos artefatos.
- `fontes/`: cópias selecionadas dos arquivos oficiais, com licenças preservadas.

Os dados volumosos ficam fora do OneDrive, em `C:\tcc-lab`, para evitar sincronizar corpora, arquivos de coocorrência e modelos. Os registros do TCC ficam nesta pasta. Os diretórios externos precisam de backup próprio; registrar um hash não faz backup.

## Instalação WSL e continuação

Para seguir a plataforma Linux documentada pelo fastText, a recomendação final é **Ubuntu no WSL**, seguindo Microsoft Learn. Cygwin foi apenas uma alternativa considerada; não foi instalado nem validado e não é apresentado como plataforma oficialmente suportada pelos modelos.

O comando abaixo **já foi executado** nesta continuação, com código de saída zero:

```powershell
wsl --install -d Ubuntu --no-launch
```

O instalador informou que a Plataforma de Máquina Virtual, o Subsistema do Windows para Linux e o Ubuntu foram instalados e que as alterações só terão efeito após reiniciar. Também emitiu uma mensagem de elevação ao final; por isso o código zero não foi tratado como prova de Linux operacional. Ver `logs/05-wsl-instalacao.txt` e `manifests/wsl-instalacao.json`.

**A reinicialização já ocorreu** e o Ubuntu está configurado com o usuário `lucas`. A execução de comandos Linux e os exemplos descritos na tabela foram verificados. Não é necessário reinstalar WSL. As métricas e evidências ficam em [execuções reais](docs/05-execucoes-reais.md) e no manifesto `manifests/estado-linux-atual.json`.

Os modelos efetivamente treinados ficam em `/home/lucas/tcc-lab` no Ubuntu. `C:\tcc-lab` preserva as fontes e os dados adquiridos inicialmente no Windows. Consulte o manifesto Linux atual para os caminhos dos modelos; `artefatos.json` preserva o estado inicial anterior à instalação. O script `06-exportar-registros.sh` copia os registros das execuções concluídas para este projeto, mantendo os modelos volumosos no Linux.

## Evidência e limites

O GloVe, o tutorial cooking e o treinamento de embeddings fastText foram executados com sucesso no Linux. Os resultados das tarefas oficiais são separados e não constituem comparação de qualidade entre algoritmos. Os corpora dos exemplos são em inglês e não substituem a futura avaliação de relevância no domínio de animes.

O pré-processamento foi executado com o Perl já existente no Git for Windows, antes da instalação Linux. Essa é uma etapa de dados, não treinamento. Os MD5 de `text8`, `enwik9` e `fil9` foram comparados aos publicados por Matt Mahoney; os SHA-256 locais também foram registrados. Ver `manifests/artefatos.json` e `logs/04-preprocessamento-fasttext.txt`.
