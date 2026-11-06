# Manual completo do laboratório de modelos textuais AniRec

Registro consolidado de instalações testes códigos e decisões para o TCC

Lucas • 29 de outubro de 2026 • Preparado com assistência do Codex

## 1 Como ler este documento

Este manual explica o trabalho realizado até esta data para preparar modelos de representação de texto e experimentar busca de animes. O leitor não precisa conhecer programação ou inteligência artificial. Começamos pelos conceitos, apresentamos o que existe de fato na máquina, explicamos os procedimentos e terminamos com os resultados e limites. Há instruções práticas e anexos com código completo para quem quiser reproduzir ou auditar.

A conclusão atual tem duas partes. Primeiro, GloVe, fastText, Word2Vec CBOW e Skip-gram e MiniLM multilíngue funcionaram nos testes registrados. Segundo, Lucas confirmou que o sistema final do TCC deve usar modelos estáticos. O MiniLM venceu o piloto entre português e inglês, mas não pertence a essa classe: será um comparador, e não o modelo final escolhido. Ainda não há evidência suficiente para declarar qual estático será o melhor na configuração final.

O próximo candidato recomendado é fastText com vetores portugueses e ingleses alinhados. Essa variante não foi instalada nem testada. Também não há um gerador GPT, Llama, DeepSeek ou Qwen instalado ou avaliado neste laboratório. Sugestões não são apresentadas como execuções concluídas.

O documento tem quatro níveis de leitura. Os capítulos iniciais contam a história e explicam os conceitos. O guia prático mostra como usar os arquivos existentes. Os registros detalhados preservam os procedimentos e suas evidências. O anexo de código contém os programas próprios do laboratório, com numeração de linhas. Não é necessário ler todo o código para compreender as conclusões.

Esta é documentação de laboratório, não a redação final do TCC nas normas da instituição. Referências, licenças e metodologia precisam ser conferidas na etapa de submissão acadêmica. Não foi feita validação humana independente do piloto anime.

## 2 O objetivo do trabalho

O objetivo prático é receber uma descrição do que a pessoa deseja assistir e devolver animes do catálogo relacionados a essa intenção. Por exemplo, a consulta pode ser “uma história de pessoas presas em um jogo virtual”. O sistema deve procurar descrições pertinentes, sem exigir que a pessoa saiba o título.

O requisito de idioma confirmado é consulta em português e descrição do catálogo em inglês. Isso é mais difícil que comparar dois textos ingleses: palavras como “amizade” e “friendship” têm significados próximos, mas grafias diferentes. Um sistema puramente lexical não descobre essa relação automaticamente.

Os primeiros passos foram aprender a instalar, treinar, salvar, carregar e avaliar modelos pelos exemplos oficiais. Depois foi preparado um piloto comum para observar como os pipelines disponíveis se comportavam na busca. O TCC deverá concentrar-se no sistema com representação estática; a comparação ampliada, controlada e com mais modelos pode constituir uma iniciação científica.

Uma busca por conteúdo não é automaticamente uma recomendação personalizada. Nesta etapa não usamos histórico de avaliações de cada usuário nem aprendemos preferências individuais. Se o TCC incluir personalização, será necessário acrescentar esse requisito e sua avaliação explicitamente.

## 3 Conceitos sem exigir conhecimento prévio

### 3 1 Código biblioteca e modelo

Código é a receita executável: instruções que dizem ao computador o que fazer. Uma biblioteca reúne código reutilizável. Gensim e Sentence Transformers são bibliotecas. Um modelo treinado reúne números aprendidos a partir de dados; esses números são chamados pesos ou parâmetros.

Baixar o repositório de GloVe não é o mesmo que baixar um GloVe já treinado. Neste laboratório baixamos os programas de GloVe e fastText e os treinamos com bases dos exemplos oficiais. Para MiniLM, baixamos pesos prontos dos autores; não treinamos esse modelo do zero. Word2Vec foi treinado usando a implementação da biblioteca Gensim.

Instalar prepara programas e dependências. Compilar transforma código C/C++ em um executável que a máquina consegue rodar. Treinar aprende os parâmetros. Inferir ou consultar usa parâmetros existentes sem reaprender tudo. Avaliar compara saídas a algum critério. Cada operação tem custos e evidências diferentes.

### 3 2 Vetores e embeddings

Um vetor é uma sequência de números. Um embedding representa uma palavra ou texto por um vetor. A intenção é que textos relacionados tenham representações próximas segundo uma medida matemática. Um vetor com 100 dimensões tem 100 números, não cem palavras nem cem categorias visíveis.

Como analogia, um mapa localiza lugares com coordenadas. Embeddings localizam elementos linguísticos em um espaço aprendido. Não devemos imaginar que cada dimensão tenha um nome interpretável como “ação”, “romance” ou “tristeza”. As dimensões são aprendidas em conjunto.

Similaridade do cosseno compara a direção de dois vetores. No piloto, após normalizar os vetores para comprimento um, calculamos seu produto escalar: isso equivale ao cosseno. O valor não é uma probabilidade de o anime agradar ao usuário. Escores de modelos diferentes também não são diretamente intercambiáveis.

### 3 3 Estático contextual e gerador

GloVe e Word2Vec dão a uma palavra um vetor lexical que não muda a cada frase. fastText acrescenta partes de palavras para compor representações, inclusive para formas não vistas, mas nesse uso continua não contextual. Eles não produzem automaticamente uma representação completa de uma sinopse; precisamos definir como juntar os vetores.

Um encoder contextual como MiniLM processa o texto e produz uma representação dependente da entrada. Não é estático só porque congelamos seus pesos ou salvamos seus embeddings em disco. Ele também não é um chatbot gerador de respostas.

GPT, Llama, DeepSeek e Qwen incluem modelos geradores: recebem uma entrada e podem produzir uma sequência de texto. Podem ser usados para ordenar candidatos, mas isso exige definir prompt, formato de saída e avaliação. Um nome de família não identifica uma versão ou tamanho específico.

### 3 4 Vocabulário palavras desconhecidas e tokens

Vocabulário é o conjunto de palavras reconhecidas diretamente em uma tabela de vetores. OOV significa fora desse vocabulário. GloVe e Word2Vec instalados não inventam vetores para palavras ausentes; o fastText binário pode compor vetores por subpalavras. Ter um vetor numericamente válido não prova entendimento semântico do termo.

Token é uma unidade processada pelo sistema. Na parte lexical, tokenizamos sequências de letras. O tokenizer do MiniLM pode quebrar uma palavra em várias partes. Seu limite de 128 tokens não equivale a 128 palavras ou caracteres. Esta diferença importa para sinopses longas.

Corpus é uma coleção de textos para treino ou análise. Benchmark é uma base/protocolo de avaliação. Época é uma passagem de aprendizagem sobre os dados. Janela indica quantas palavras vizinhas participam de certos treinamentos. Threads/workers permitem trabalho paralelo; podem introduzir variação entre treinos mesmo com semente fixa.

### 3 5 Arquivos logs e integridade

Log registra o que um programa mostrou durante a execução, inclusive erros. Código de saída zero normalmente significa encerramento bem-sucedido; ele não prova qualidade do modelo. Manifesto é um inventário estruturado de versões, origens, arquivos e resultados.

SHA-256 é uma impressão digital calculada sobre os bytes de um arquivo. Ajuda a identificar exatamente o artefato usado. Só calcular um hash não prova autenticidade: para isso, é preciso compará-lo a uma referência confiável quando existir. MD5 foi usado para conferir valores historicamente publicados para os corpora, juntamente com SHA-256 local. A verificação CRC de um ZIP testa sua estrutura, não a qualidade ou licença do conteúdo.

## 4 O computador e a organização dos arquivos

O inventário registrou Windows 10 Home de 64 bits, Ryzen 5 2400G com quatro núcleos/oito processadores lógicos, aproximadamente 13,9 GiB de RAM utilizável e GPU integrada Radeon Vega 11. Não foi validada aceleração por GPU. Todos os modelos aqui foram treinados ou executados em CPU.

O Ubuntu executa dentro do Windows por WSL2. O ambiente observado foi Ubuntu 26.04.1 LTS, com aproximadamente 6,7 GiB de RAM atribuída e 2 GiB de swap. Swap é espaço de apoio em disco para memória; não equivale a RAM rápida. O tamanho lógico do disco virtual Linux não é espaço livre físico garantido no Windows.

Há três locais importantes. A pasta do TCC no OneDrive contém documentação, códigos próprios, dados pequenos e evidências. C:/tcc-lab contém clones e downloads preparatórios no Windows. /home/lucas/tcc-lab contém os executáveis, ambientes Python e pesos usados no Linux. Ter o TCC no OneDrive não sincroniza automaticamente o diretório Linux nem garante backup dos pesos.

O Windows usa caminhos como C:/tcc-lab. O Ubuntu pode acessar esse disco por /mnt/c/tcc-lab. A pasta pessoal Linux é /home/lucas e pode ser abreviada como ~. A distinção é importante: comandos Bash devem ser executados no Ubuntu; comandos PowerShell devem ser executados no PowerShell.

Foram criados ambientes Python separados para evitar que bibliotecas incompatíveis afetassem umas às outras. .venv usa Python 3.14.4 para ferramentas numéricas/avaliações. .venv-word2vec-py312 usa CPython 3.12.16 para Gensim. .venv-sentences usa o mesmo CPython separado para PyTorch e Sentence Transformers. O Python do sistema Ubuntu não foi substituído.

## 5 Histórico das decisões e dos problemas

Primeiro inspecionamos o projeto e a máquina. Git e Bash do Git for Windows estavam disponíveis; não havia um ambiente Linux utilizável confirmado. O atalho Python da Microsoft Store não foi tratado como um interpretador funcional do laboratório.

Foi considerada a instalação de Cygwin. O instalador foi baixado e sua ajuda foi consultada, mas a chamada de instalação foi rejeitada pela revisão automática antes de executar. Não houve instalação Cygwin funcional nem tentativa de contornar a rejeição. A solução adotada foi WSL/Ubuntu, seguindo os procedimentos de plataforma documentados.

O Windows foi reiniciado às 09:48:14 de 29/10/2026. Depois, Ubuntu/WSL2 e o usuário lucas foram verificados. Pacotes de compilação, Python, Git, Perl, certificados, ferramentas de download e GNU time foram instalados. Avisos de systemd apareceram durante instalação de pacotes, mas o processo concluiu com código zero e as ferramentas foram verificadas.

O código fastText v0.9.2 falhou com GCC 15: uint64_t não estava declarado por seus includes. Em vez de alterar os arquivos oficiais para inserir cstdint, instalamos G++ 12 e usamos make CXX=g++-12. O GloVe compilou com GCC 15. Trata-se de decisão de compatibilidade do ambiente, não mudança do algoritmo.

O servidor Stanford para Rare Words não respondeu no Windows e no Linux. No Linux, houve No route to host; resolver o DNS ou usar um alias que apontava para o mesmo IP não resolvia o acesso. Separamos o treinamento fastText da avaliação para continuar trabalhando sem inventar resultados. A avaliação foi concluída depois com uma cópia documentada e corroborada.

Gensim teve duas falhas no Python 3.14. A primeira indicou Python.h ausente; instalamos os headers Python. A segunda expôs incompatibilidades de compilação com APIs Python/NumPy, incluindo subarray e ma_version_tag. A solução foi compilar CPython 3.12.16 separado, instalar Gensim nesse ambiente e verificar sua extensão otimizada. Não foi uma simples troca de nome de executável.

A primeira auditoria da cópia RW esperava o nome de um bucket antigo. O notebook AWS recuperado apontava para um bucket regional. O auditor interrompeu antes da avaliação; o endereço e a expectativa foram ajustados conforme a evidência. O histórico da tentativa permaneceu preservado.

A consulta à API Jikan não forneceu os dados do piloto. Foi obtida uma release do Anime Offline Database. Seus metadados identificam animes reais, mas as descrições curtas utilizadas foram escritas com IA; não atribuímos essas descrições à fonte.

Após o piloto, foi inicialmente sugerido MiniLM como núcleo do protótipo devido ao maior nDCG. Lucas reiterou que o TCC final usará estáticos. A recomendação foi corrigida e documentada: MiniLM será comparação contextual; fastText alinhado é o próximo candidato estático, sem resultado ainda.

Também ocorreram erros pontuais de sintaxe/aspas em comandos de inspeção PowerShell, corrigidos antes de produzir os arquivos finais. Eles não foram falhas dos modelos nem alteraram os dados congelados. Este manual não pretende ser uma transcrição palavra por palavra da conversa: sintetiza operações e evidências preservadas, incluindo as tentativas malsucedidas relevantes.

## 6 De onde vieram programas dados e pesos

GloVe veio do repositório stanfordnlp/GloVe no GitHub, revisão 52f7dbc512be3f72e9c11e7cbb19dfdfa4651e9c. fastText veio de facebookresearch/fastText, tag v0.9.2, revisão 5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe. As revisões fixam o código que executamos. Cópias de README, licença, Makefile e scripts relevantes estão em laboratorio/fontes. Os clones Linux não receberam alterações rastreadas nos arquivos oficiais.

Comandos de aquisição registrados no PowerShell, apresentados para explicar a execução já realizada:

```powershell
git -c core.autocrlf=false clone https://github.com/stanfordnlp/GloVe.git C:/tcc-lab/GloVe
git -c core.autocrlf=false clone --branch v0.9.2 --depth 1 https://github.com/facebookresearch/fastText.git C:/tcc-lab/fastText
```

clone copia um repositório; --branch seleciona a tag; --depth 1 reduz o histórico baixado; core.autocrlf=false evita conversões automáticas de quebras de linha em scripts. Esses comandos descrevem a obtenção inicial, não uma instrução para sobrescrever as cópias existentes.

text8 e enwik9 vieram de Matt Mahoney, como indicado pelos exemplos oficiais. Usamos HTTPS no mesmo domínio/caminho em vez do HTTP histórico. text8.zip tem 31.344.016 bytes e expande para 100.000.000 bytes. enwik9.zip tem 322.592.222 bytes e expande para 1.000.000.000 bytes. O arquivo enwik9 foi limpo com wikifil.pl oficial, gerando fil9 de 713.069.767 bytes. Isso remove marcações e prepara texto para o fastText.

```bash
cd /home/lucas/tcc-lab/fastText
perl wikifil.pl data/enwik9 > data/fil9
```

perl executa o programa de limpeza; o primeiro caminho é a entrada; > grava a saída no arquivo indicado. Esse comando já foi usado na preparação, e uma nova execução sobrescreveria fil9. Não é necessário repeti-lo para consultar o modelo.

O corpus cooking veio de dl.fbaipublicfiles.com/fasttext/data/cooking.stackexchange.tar.gz. A base contém 15.404 exemplos; seguimos o corte do tutorial: 12.404 no treino e 3.000 na validação. Não se trata de base de animes.

O corpus Lee e o conjunto questions-words.txt foram distribuídos com Gensim. Lee tem 300 documentos; não baixamos o grande modelo Google News. Para as versões adicionais Word2Vec, reutilizamos text8 já existente. O tarball CPython veio de python.org, e Gensim de sua distribuição registrada pelo pip/PyPI.

MiniLM veio do repositório sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 no Hugging Face, revisão e8f8c211226b894fcb81acc59f3b34ba3efd5f42. snapshot_download preservou pesos safetensors, tokenizer e configurações. Não baixamos exportações ONNX/OpenVINO nem uma cópia alternativa pickle. O arquivo principal de pesos tem 470.637.416 bytes; o diretório salvo soma 487.726.515 bytes. O cache de aquisição e a cópia autocontida para uso local têm funções diferentes.

O Anime Offline Database veio da release 2026-27, com metadados de 04/07/2026, arquivo JSON de 62.331.136 bytes. O JSON completo está em C:/tcc-lab/Pilot; o subconjunto e a licença foram preservados no piloto. As condições ODbL/DbCL dos metadados devem ser respeitadas e não devem ser confundidas com licença de todos os textos possíveis sobre as obras.

## 7 Por que esses modelos foram incluídos

GloVe é uma referência clássica que aprende a partir de estatísticas de coocorrência: palavras que aparecem juntas fornecem informação para os vetores. fastText introduz composição por partes de palavras, pertinente a flexões e termos raros. Word2Vec acrescenta objetivos preditivos, com CBOW e Skip-gram como variantes. Compará-los permite estudar escolhas clássicas de representação sem precisar treinar um grande modelo de linguagem.

CBOW usa contexto para prever uma palavra; Skip-gram usa uma palavra para prever elementos do contexto. Essa é uma explicação conceitual: a implementação também usa mecanismos como amostragem negativa. Não escolhemos a variante melhor por intuição; testamos ambas nas condições registradas.

TF-IDF é uma referência simples que valoriza palavras frequentes em um documento e menos comuns no conjunto. Não tem pesos neurais pré-treinados. Se um método complexo não melhora em relação a ele, a complexidade precisa ser justificada. No piloto ele foi aprendido apenas sobre o catálogo, não sobre os julgamentos.

MiniLM foi incluído para observar um encoder contextual multilíngue já treinado. Ele responde mais diretamente à tarefa de representar frases. Sua inclusão permite comparar alternativas modernas, mas não muda a restrição do TCC em favor de estáticos.

O classificador cooking foi incluído para aprender o uso supervisionado oficial fastText, não como candidato a busca de animes. Um programa pode suportar várias tarefas; compartilhar o nome fastText não torna todos seus modelos intercambiáveis.

## 8 O que foi executado com GloVe

Executamos o demo.sh oficial preservado por meio de um wrapper próprio. O demo compila, conta palavras, constrói coocorrências, embaralha os dados, treina e avalia analogias. Configuração: 50 dimensões, 15 iterações, janela 15, frequência mínima 5, oito threads e x_max 10. O vocabulário resultante tem 71.290 palavras.

O demo levou 6 min 58,14 s e teve pico RSS de 1.942.808 KiB. O tempo inclui várias etapas, não só treinamento. RSS é memória residente observada do processo; não é memória agregada de todo o Windows/WSL.

Foram cobertas 17.827 de 19.544 analogias, ou 91,21%. Houve 4.190 acertos entre as cobertas, acurácia de 23,50%. Analogias semânticas: 2.038/7.416; sintáticas: 2.152/10.411. Uma analogia é uma relação lexical, não um teste de sinopses. Não existe aqui um limiar inventado para dizer que uma instalação está correta; execução e qualidade são verificações separadas.

Para usar os vetores já treinados no terminal Ubuntu:

```bash
/home/lucas/tcc-lab/.venv/bin/python '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/scripts/05-consultar-glove.py' --vectors /home/lucas/tcc-lab/GloVe/vectors.txt --word king --top-k 5
```

O script carrega os números, normaliza os vetores, calcula cossenos, exclui a própria palavra e mostra os vizinhos mais próximos. --word define a consulta e --top-k a quantidade. A consulta registrada a king incluiu emperor e henry entre vizinhos. Isso é inspeção qualitativa, não porcentagem de recomendações corretas. Se uma palavra estiver ausente, o script informa essa condição.

## 9 O que foi executado com fastText

O modelo de embeddings foi treinado com o comando do exemplo oficial de uma época: Skip-gram, dimensão 100, janela 5, taxa inicial 0,025, frequência mínima 5, cinco negativos, dois milhões de buckets, n-gramas de caracteres de 3 a 6 e quatro threads. A documentação interativa pode mostrar defaults diferentes: reproduzimos este script fixado, não todos os experimentos do artigo.

O treinamento levou 11 min 44,98 s, incluindo leitura/gravação. O pico RSS foi 1.224.096 KiB. O arquivo fil9.vec começa com 218316 100, indicando quantidade de entradas e dimensão. fil9.bin tem 978.480.868 bytes e guarda o modelo completo para composição por subpalavras.

Usos locais, no terminal Ubuntu, sem retreinar:

```bash
cd /home/lucas/tcc-lab/fastText
printf 'king\nqueen\nunseenwordexample\n' | ./fasttext print-word-vectors result/fil9.bin
printf 'king\n' | ./fasttext nn result/fil9.bin
printf 'berlin germany france\n' | ./fasttext analogies result/fil9.bin
printf 'an adventure about friendship\n' | ./fasttext print-sentence-vectors result/fil9.bin
```

printf prepara texto de entrada; | envia a saída para outro programa. print-word-vectors devolve números; nn busca vizinhos; analogies busca uma relação lexical; print-sentence-vectors produz um vetor de sentença pela operação da ferramenta. Os exemplos são demonstrações. No piloto usamos nossa agregação por IDF, que não deve ser confundida com a implementação interna do comando de sentença.

Verificamos dimensão, valores finitos e vetores não nulos. unseenwordexample estava ausente da tabela de vocabulário, mas recebeu vetor pelo binário. Isso comprova a operação de subpalavras no arquivo .bin; não comprova significado adequado para qualquer nome raro ou japonês. O binding Python import fasttext não foi instalado; usamos a CLI oficial, inclusive por subprocess em Python.

No tutorial cooking, o classificador foi salvo em /home/lucas/tcc-lab/tutorial-cooking/model_cooking.bin. Teve P@1 0,151 e R@1 0,0652 em 3.000 exemplos. Com cinco predições, P@5 0,0679 e R@5 0,147. O treino levou 2,10 s. Precisão e recall referem-se aos rótulos de culinária, não às relevâncias anime. As perguntas do tutorial retornaram baking e food-safety nos registros.

```bash
/home/lucas/tcc-lab/fastText/fasttext test /home/lucas/tcc-lab/tutorial-cooking/model_cooking.bin /home/lucas/tcc-lab/tutorial-cooking/cooking.valid
printf 'Which baking dish is best to bake a banana bread ?\n' | /home/lucas/tcc-lab/fastText/fasttext predict /home/lucas/tcc-lab/tutorial-cooking/model_cooking.bin -
```

## 10 Rare Words explicado e resolvido

Rare Words, abreviado RW, contém pares de palavras e notas humanas de similaridade. A avaliação calcula se os vetores ordenam similaridades de modo coerente com essas notas. O problema inicial era baixar rw.zip da origem Stanford; não era necessário treinar fastText outra vez para resolver isso.

Recuperamos no histórico oficial AWS um notebook que documenta o arquivo público datasets/text/stanford_rare_words/rw.zip. A revisão foi 4883224d0032906f1a2bafd4887544ff5ddae606. O notebook não foi executado e não criou endpoint pago na AWS; só consultamos sua referência ao dataset público.

Antes de avaliar, conferimos estrutura/CRC do ZIP, 2.034 registros, campos e notas finitas no intervalo 0 a 10. Comparamos cada par e sua nota média, preservando ordem e repetições, com uma cópia acadêmica de mfaruqui/eval-word-vectors. O conteúdo dessa cópia foi identificado pelo blob Git 35498f2fb426bc8e663cb426ed597455b3ecd8cf. Todos os pares e médias coincidiram.

Esse procedimento corrobora o conteúdo, mas não prova identidade byte a byte com o ZIP Stanford original: não encontramos checksum publicado dos autores para essa comparação. As notas individuais dos anotadores também não foram corroboradas pela cópia de três colunas. O arquivo efetivamente avaliado veio do ZIP AWS completo.

Executamos eval.py oficial sem alterar seus cálculos. Ele mostrou 42 porque arredonda rho multiplicado por 100. Para registrar a precisão completa, um pequeno script executou o mesmo avaliador via runpy e capturou suas variáveis: Spearman rho 0,4177019229655776; 2.034 pares avaliados; zero descartados.

Spearman mede associação de ordenações. O resultado não é “42% de acurácia” nem qualidade de recomendação. Zero pares descartados também não significa que todas as palavras estavam no vocabulário de treino, pois fastText gera vetores por subpalavras.

## 11 O que foi executado com Word2Vec

Compilamos CPython 3.12.16 obtido de python.org e verificamos o checksum publicado. Instalamos em /home/lucas/.local/tcc-python-3.12.16 com make altinstall. Esse procedimento evita trocar o Python usado pelo Ubuntu. Gensim 4.4.0 foi instalado em um ambiente dedicado, com relatórios pip e verificação da extensão otimizada.

O primeiro experimento seguiu o tutorial Gensim com corpus Lee. CBOW e Skip-gram produziram 1.750 palavras com 100 dimensões. Usaram cinco épocas, janela 5, frequência mínima 5, três workers e seed 1. O treino levou aproximadamente 0,74 s no CBOW e 1,08 s no Skip-gram.

Testamos consulta, vizinhos, números finitos, erro para palavra inexistente e igualdade do vetor após salvar/carregar. A analogia cobriu apenas 146 de 19.544 questões, cerca de 0,75%. CBOW acertou 0/146 e Skip-gram 2/146. Isso mostra a limitação do exemplo didático; não prova que Word2Vec é inferior a GloVe ou que uma variante vence a outra.

Para não levar somente esses exemplos pequenos à comparação anime, treinamos novas versões em text8: 100 dimensões, janela 5, min_count 5, cinco épocas, quatro workers e seed 20261029. Cada uma teve 71.290 palavras. CBOW levou 72,11 s; Skip-gram 239,07 s. Não usamos textos ou julgamentos anime nesse treino e não ajustamos hiperparâmetros após os rankings.

Exemplo de uso em um arquivo Python, executado pelo ambiente .venv-word2vec-py312:

```python
from gensim.models import Word2Vec
modelo = Word2Vec.load('/home/lucas/tcc-lab/Word2Vec/models/text8-skipgram-100d.model')
print(modelo.vector_size)
print(modelo.wv['king'])
print(modelo.wv.most_similar('king', topn=5))
```

load lê o modelo treinado; wv acessa as representações lexicais; most_similar compara vetores. O exemplo é uma instrução de uso da API, não uma nova execução com saídas inventadas. Para CBOW, mudar o nome para text8-cbow-100d.model. Para os exemplos Lee, usar lee-cbow.model ou lee-skipgram.model. .model preserva a estrutura Gensim; .vec é exportação das representações.

## 12 O que foi executado com MiniLM

Instalamos PyTorch pelo índice CPU oficial e Sentence Transformers em .venv-sentences. Versões observadas: torch 2.15.0+cpu, sentence-transformers 6.2.0, transformers 5.21.1 e huggingface-hub 2.3.0. Não foi configurado CUDA nem backend da GPU integrada.

Carregamos os pesos fixados com trust_remote_code=False. As duas frases do exemplo oficial geraram matriz 2 por 384, finita e não nula. Salvamos o modelo e recarregamos apenas com arquivos locais; os vetores permaneceram próximos dentro da tolerância registrada. Um exemplo sintético próprio de criança/cachorro retornou a descrição esperada entre três opções; é teste didático, não benchmark.

O runner inicial levou 1 min 2,95 s, incluindo download e verificações, com pico RSS de 1.760.632 KiB. O encode de duas frases levou cerca de 0,043 s naquela execução. Esses números não constituem uma distribuição controlada de latência.

```python
from sentence_transformers import SentenceTransformer
modelo = SentenceTransformer(
    '/home/lucas/tcc-lab/SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2',
    device='cpu', local_files_only=True, trust_remote_code=False,
)
consulta = modelo.encode(['Quero uma aventura sobre amizade.'], normalize_embeddings=True)
descricoes = modelo.encode(['Friends set out on a dangerous adventure.'], normalize_embeddings=True)
print(consulta @ descricoes.T)
```

Executar esse exemplo em .venv-sentences. Ele não baixa novamente os pesos. O exemplo ilustra a API; não deve ser citado como um novo resultado experimental. Para sinopses reais grandes, precisaremos tratar o limite de 128 tokens ou usar outro encoder na comparação. No piloto curto, o máximo foi 60 e não houve truncamento.

## 13 Como construímos o piloto de animes

Selecionamos 39 títulos reais no Anime Offline Database. As descrições curtas em português/inglês foram preparadas com IA, assim como consultas e julgamentos. Nenhuma sinopse oficial foi copiada dessa base. Há 58 consultas organizadas em 29 famílias de intenção: uma formulação direta e uma paráfrase por intenção.

Para cada consulta/anime definimos grau 2, fortemente pertinente; grau 1, parcialmente pertinente; grau 0, não selecionado como pertinente. São 2.262 pares completos. Grau 0 não é uma afirmação universal de que a obra jamais serve à consulta. É o julgamento operacional deste conjunto, sujeito a revisão humana futura.

O protocolo e os arquivos foram congelados antes da inspeção dos rankings, às 14:22:41 UTC, ou 11:22:41 em Brasília. Hashes identificam catálogo, consultas e relevâncias. A confirmação do idioma principal veio de Lucas. Os cenários secundários foram inglês/inglês e português/português, com as mesmas intenções; não são três amostras independentes.

Os modelos receberam apenas descrições e consultas, sem títulos, IDs, gêneros ou notas públicas no texto vetorizado. O codificador não lê julgamentos para gerar scores. A avaliação lê depois os scores salvos e os graus de relevância. Essa separação evita que o código de busca escolha resultados com conhecimento dos rótulos.

Na tokenização lexical, normalizamos Unicode com NFKC, aplicamos casefold para lidar com maiúsculas/minúsculas e preservamos sequências de letras. Não fizemos stemming nem removemos stopwords. Essas são escolhas explícitas; não alegamos que sejam as melhores possíveis.

Para GloVe, fastText e Word2Vec usamos média ponderada por IDF do catálogo e normalização L2. IDF dá maior peso a termos raros no conjunto de descrições. Palavras ausentes são ignoradas em tabelas sem composição. Se nenhuma palavra gera vetor, a consulta fica com vetor zero. Para fastText, um processo persistente da CLI gera vetores e o código os reutiliza por cache.

TF-IDF usa unigramas/bigramas e frequência sublinear, com ajuste apenas nas descrições. MiniLM usa seu tokenizer próprio e encode do texto completo, sem aplicar antes a tokenização lexical. O código preserva matrizes de documentos, consultas e scores em NPZ para auditoria.

## 14 O que significam as métricas

nDCG@5 avalia a ordem dos cinco primeiros itens, considerando os graus. Usamos ganho 2 elevado ao grau menos 1: grau 2 vale 3 e grau 1 vale 1 antes do desconto por posição. Normalizamos pelo ranking ideal daquela consulta. O resultado vai de 0 a 1; 0,805 não significa 80,5% de acurácia.

Hit@1 conta se o primeiro item é fortemente pertinente. MRR@10 considera o inverso da posição do primeiro grau 2 até o décimo; se não houver, é zero. Recall@5 mede a fração dos itens grau 1 ou 2 encontrada nos cinco primeiros. Precision@3, também preservada, mede a fração pertinente nos três primeiros.

Empates são importantes: uma consulta sem vetor pode atribuir score zero a todos os itens. Dar sempre o menor ID como primeiro geraria um resultado arbitrário. As métricas calculam a expectativa de permutações uniformes dentro do empate. O painel exibe uma ordem por ID apenas para mostrar os itens; não representa preferência adicional do modelo.

A nDCG própria foi conferida contra sklearn em 1.392 combinações consulta/modelo/cenário, com diferença máxima 3,33e-16. Um caso pequeno de empate também foi conferido. Para incerteza exploratória, fizemos 5.000 reamostragens bootstrap por família de intenção, mantendo as duas formulações juntas. Os intervalos não corrigem viés dos textos, anotação por IA ou falta de representatividade.

## 15 Como interpretar o resultado

As tabelas completas aparecem a seguir, geradas diretamente do JSON preservado. MiniLM obteve o maior nDCG entre português e inglês: 0,805 e 47 de 58 primeiros resultados grau 2. Nas consultas diretas foram 29/29; nas paráfrases, 18/29. Há 11 erros de primeiro lugar, que devem ser analisados em vez de escondidos pela média.

Em inglês, Word2Vec Skip-gram chegou a nDCG 0,739 e fastText a 0,723. Portanto, a queda entre idiomas não demonstra que algoritmos estáticos sejam incapazes de recuperar descrições. Os espaços treinados em inglês não foram alinhados ao português. Gerar vetor para todas as palavras com fastText não cria automaticamente esse alinhamento.

Os pipelines foram treinados com corpora, dimensões e orçamentos diferentes. MiniLM tem pré-treinamento muito maior. A comparação responde qual pipeline disponível funcionou melhor neste piloto, não qual arquitetura é causalmente superior em condições iguais.

O piloto é pequeno, curado e produzido com IA. Consultas foram formuladas a partir de temas conhecidos; isso pode facilitar correspondências. Não é amostra aleatória de usuários nem teste final do TCC. As relevâncias precisam de anotação independente e as descrições precisam ser substituídas/complementadas por sinopses reais de fonte adequada.

## 16 O que ainda não fizemos

Não instalamos geradores GPT/Llama/DeepSeek/Qwen, não fizemos chamadas pagas e não avaliamos a qualidade de um LLM neste problema. Não baixamos fastText PT/EN alinhado nem pesos NILC/Wang2Vec. Doc2Vec não tem modelo treinado/testado neste laboratório. Não treinamos um LLM do zero nem fizemos fine-tuning do MiniLM.

Não há interface final de busca implantada, API de produção, personalização, avaliação com usuários ou latência de serviço medida. O painel HTML apenas permite explorar resultados já calculados; selecionar opções não executa inferência nova.

Não podemos declarar que um estático já superou LLMs. Essa é uma hipótese de pesquisa. Mesmo se um estático perder um pouco em qualidade, pode atender aos requisitos com menor custo, independência de rede e maior simplicidade. Equivalência exige margem predefinida e avaliação adequada; ausência de significância estatística não prova igualdade.

## 17 Como retomar sem repetir instalações

Abrir o aplicativo Ubuntu ou executar wsl -d Ubuntu no PowerShell. Para consultas, usar diretamente o Python do ambiente correto, como nos exemplos. Não é necessário executar treinamento toda vez. Ativar um venv apenas muda o conjunto de bibliotecas do terminal atual; deactivate encerra essa ativação, sem apagar arquivos.

Para recalcular métricas dos scores já existentes, no terminal Ubuntu:

```bash
cd '/mnt/c/Users/lucas/OneDrive - dcc.ufrj.br/Documentos/ChatGPT/TCC/laboratorio/piloto-animes'
/home/lucas/tcc-lab/.venv-sentences/bin/python codigo/05-avaliar.py
```

Esse comando reescreve os resumos derivados com base nos resultados existentes; não treina nem consulta modelos. Preservar as versões se houver mudança de protocolo. O orquestrador 04-rodar-codificadores.sh pula saídas já existentes. Para executar modelos novamente, preparar outra versão de resultados em vez de apagar v1.

Não executar 02-criar-base.py para “melhorar” julgamentos depois de olhar as saídas. Ele recusa sobrescrever o congelamento. Uma nova base deve ter outra versão e justificativa. Os scripts de treinamento também protegem contra sobrescrever pesos; respeitar essas mensagens e preservar cópias anteriores.

## 18 Documentação fontes e cuidado com reprodução

Os comandos de instalação históricos aparecem nos anexos, junto de sua função. Um comando que baixa ou compila algo não deve ser confundido com consulta. Os exemplos apresentados aqui não foram todos reexecutados durante a criação deste manual: são instruções derivadas das APIs e operações já testadas, sem saídas novas atribuídas a eles.

Pacotes exatos estão em requirements-resolved.txt e relatórios pip; commits e revisões estão nos manifestos; hashes identificam os pesos usados. Várias threads podem produzir variação entre treinos apesar da semente. Preservar pesos é essencial para repetir a inferência desta execução.

O material de apresentação usou o runtime Python do Codex, separado dos ambientes dos modelos. matplotlib 3.11.2 e PyMuPDF 2.0 foram acrescentados para gráficos e inspeção de PDF; reportlab já estava disponível. PyMuPDF trouxe dependências transitivas registradas em ambiente-relatorios.txt. Isso não é um novo modelo nem alterou os pesos avaliados. O gerador deste manual e a lista de dependências acompanham a entrega.

Nenhum valor “pendente” em um log antigo deve prevalecer sobre uma execução posterior comprovada. Por exemplo, o wrapper de treino fastText conserva uma mensagem RW PENDENTE que era correta naquela etapa. A avaliação subsequente encerrou essa pendência. O inventário artefatos.json retrata a preparação inicial Windows; estado-linux-atual.json e o manifesto text8 posterior descrevem resultados subsequentes. Este manual faz essa consolidação sem apagar a história.

Uma cópia de documentação não é backup dos modelos: o pacote de evidências desta entrega não inclui os grandes pesos que permanecem no Linux. Para preservar tudo, é necessário salvar /home/lucas/tcc-lab e o CPython separado, ou exportar a distribuição WSL por procedimento apropriado. Não fizemos exportação completa do WSL nesta tarefa.

O computador ligado, por si só, não garante execução autônoma de novas etapas: um programa iniciado pode continuar enquanto o ambiente estiver ativo, mas suspensão, desligamento e encerramento do processo podem interrompê-lo. Este documento não configura acompanhamento remoto pelo celular ou automação persistente. O registro cobre as operações efetivamente observadas.
