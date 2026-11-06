# Fontes e componentes de terceiros

- **AniList**: metadados públicos de obras e sinopses, obtidos por consultas de leitura da API GraphQL. As condições da fonte continuam aplicáveis; não atribuímos licença própria a esses textos. https://docs.anilist.co/
- **Word2Vec/Gensim**: implementação e exemplos oficiais em https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html. Artefatos do projeto foram preparados anteriormente sobre text8; hashes e parâmetros em `site/lab/models.json`.
- **GloVe**, Stanford NLP: https://nlp.stanford.edu/projects/glove/ e https://github.com/stanfordnlp/GloVe. O corpus text8 deriva de Wikipedia; os dados e o código possuem suas próprias condições.
- **fastText**: https://fasttext.cc/docs/en/unsupervised-tutorial.html e https://github.com/facebookresearch/fastText. Artefato fil9 do exercício anterior; subpalavras preservadas na exportação documental.
- **Chart.js 4.5.1**: https://www.chartjs.org/ — licença MIT; cabeçalho de atribuição preservado no arquivo distribuído `site/lab/chart.umd.js`.
- **Kaggle Anime Recommendation Database 2020**, Hernan Valdivieso, versão 7: usado apenas nos experimentos históricos, com licença CC0 declarada no metadado original. https://www.kaggle.com/datasets/hernan4444/anime-recommendation-database-2020 . A cópia bruta de aquisição não integra a distribuição; os scripts indicam como obtê-la.
- **SMS Spam Collection**, modelos de comparação e demais corpora históricos: fontes e condições estão nos protocolos em `laboratorio/`.

Os nomes de bibliotecas, serviços e obras pertencem aos respectivos titulares. Esta distribuição não concede uma nova licença sobre dados, imagens ou software de terceiros. Os documentos acadêmicos e o código autoral permanecem sem licença geral definida neste repositório.
