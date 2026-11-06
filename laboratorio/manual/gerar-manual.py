"""Consolida evidências locais em manual legível PDF HTML Markdown e pacote ZIP.

Não treina modelos nem altera o piloto. Depende de reportlab, Pillow e PyMuPDF
no runtime de apresentação. Os dados numéricos vêm dos JSON existentes.
"""
import csv
import datetime
import hashlib
import html
import json
import pathlib
import re
import textwrap
import zipfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageBreak,
    PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=pathlib.Path(__file__).resolve().parents[2]
LAB=ROOT/'laboratorio'
HERE=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'output/manual'
OUT.mkdir(parents=True,exist_ok=True)
PILOT=LAB/'piloto-animes'
R=json.loads((PILOT/'resultados/resumo.json').read_text(encoding='utf-8'))
STATE=json.loads((LAB/'manifests/estado-linux-atual.json').read_text(encoding='utf-8'))
W=json.loads((LAB/'manifests/word2vec-text8-piloto.json').read_text(encoding='utf-8-sig'))
Q=json.loads((PILOT/'dados/consultas.json').read_text(encoding='utf-8'))
C=json.loads((PILOT/'dados/catalogo.json').read_text(encoding='utf-8'))
K=json.loads((PILOT/'resultados/rankings.json').read_text(encoding='utf-8'))
parts=[(HERE/'conteudo-principal.md').read_text(encoding='utf-8')]

def table(headers,rows):
    clean=lambda s:str(s).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(clean(c) for c in row)+' |' for row in rows])

parts.append('\n## 19 Inventário dos modelos e seus arquivos\n\nOs caminhos abaixo são do Ubuntu. Os tamanhos são dos arquivos registrados, não a memória necessária para executar. Os pesos foram treinados localmente, exceto MiniLM, cujos pesos prontos foram baixados.\n')
models=[]
for m in STATE['models']:
    models.append([m['name'],f"{m['bytes']:,}".replace(',','.'),m['path_linux']])
for m in W['models']:
    models.append(['Word2Vec text8 '+m['name'],'ver arquivo/manifesto text8',m['path']])
parts.append(table(['Artefato','Bytes registrados','Local'],models))
parts.append('\n\nTF-IDF é ajustado no catálogo dentro do codificador. Não existe um grande arquivo de pesos pré-treinados TF-IDF baixado. As matrizes resultantes e scores estão nos arquivos NPZ.\n')

parts.append('\n## 20 Resultados numéricos preservados\n\n### 20 1 Cenário principal português para inglês\n\nA tabela usa os seis pipelines principais; as duas versões Word2Vec Lee são diagnósticos adicionais. Hit@1 e Recall@5 são apresentados em porcentagem; nDCG e MRR são índices. Valores de Hit podem ser fracionários pela expectativa de empates.\n')
rows=[]
for m in R['main_models']:
    s=R['summary'][m]['PT_EN']
    rows.append([R['names'][m],f"{s['ndcg5']:.3f}",f"{100*s['hit1']:.1f}%",f"{s['mrr10']:.3f}",f"{100*s['recall5']:.1f}%",f"{s['ndcg5_ci95'][0]:.3f} a {s['ndcg5_ci95'][1]:.3f}"])
parts.append(table(['Pipeline','nDCG@5','Hit@1','MRR@10','Recall@5','IC95 nDCG'],rows))
parts.append('\n\n### 20 2 Os três cenários\n\nMesmas consultas/intencões em versões linguísticas; não somar como amostras independentes. Todos os valores são nDCG@5.\n')
parts.append(table(['Pipeline','PT para EN','EN para EN','PT para PT'],[[R['names'][m]]+[f"{R['summary'][m][s]['ndcg5']:.3f}" for s in ['PT_EN','EN_EN','PT_PT']] for m in R['main_models']]))
parts.append('\n\n![Qualidade dos rankings por modelo e idioma](../../laboratorio/piloto-animes/relatorios/comparacao-idiomas.png)\n\nFigura 1. A figura foi gerada dos resultados congelados. Barras de erro representam bootstrap por intenção, não validação externa.\n')
parts.append('\n### 20 3 Diagnóstico dos exemplos pequenos Lee\n\nEstes modelos foram mantidos para mostrar a diferença entre tutorial e representação com mais dados. Não foram usados como únicos representantes de Word2Vec.\n')
parts.append(table(['Pipeline Lee','PT para EN','EN para EN','PT para PT'],[[R['names'][m]]+[f"{R['summary'][m][s]['ndcg5']:.3f}" for s in ['PT_EN','EN_EN','PT_PT']] for m in ['w2v-lee-cbow','w2v-lee-sg']]))
parts.append('\n\n### 20 4 Cobertura e recursos no piloto\n\nA cobertura lexical abaixo conta tokens portugueses das consultas no vocabulário treinado. Cobertura utilizável permite subpalavras no fastText. Essas frações não são acurácia. O MiniLM usa outro tokenizer, por isso não recebe uma porcentagem lexical diretamente comparável.\n')
rows=[]
for m in R['main_models']:
    v=R['metadata'][m];s=v['scenarios']['PT_EN'];pct=lambda x:'não comparável' if x is None else f'{100*x:.1f}%'
    rows.append([R['names'][m],pct(s['in_vocabulary_query_token_fraction']),pct(s['usable_query_token_fraction']),f"{v['max_rss_kib']/1024:.1f}",f"{v['load_seconds']:.2f}"])
parts.append(table(['Pipeline','No vocabulário','Vetor utilizável','RSS MiB','Carga s'],rows))
parts.append('\n\nCarga inclui imports/leitura. GloVe lê apenas os vetores necessários ao lote; fastText e outros têm estratégias distintas. Esses números não são uma competição controlada de velocidade. MiniLM codificou 194 textos únicos em cerca de 6,44 s após carregar; não é latência individual de consulta. Os recursos detalhados estão em resultados/v1 e no JSON agregado.\n')

parts.append('\n## 21 Exemplos e todos os erros de primeiro lugar do MiniLM\n\nAnalisar erros ajuda a definir os requisitos do sistema. Não corrigimos relevâncias retrospectivamente para favorecer um modelo. Mesmo um candidato grau 1 continua sendo erro no Hit@1 forte. As formulações abaixo são as portuguesas do cenário principal.\n')
for i,q in enumerate(Q):
    rank=K['minilm']['PT_EN'][i]
    if rank[0]['grade']!=2:
        strong=[x['title'] for x in rank if x['grade']==2];pos=next(j+1 for j,x in enumerate(rank) if x['grade']==2)
        parts.append(f"\n### {q['id']}\n\nConsulta: {q['text_pt']}\n\nPrimeiro resultado: {rank[0]['title']}, grau {rank[0]['grade']}. Primeiro alvo forte na posição {pos}. Alvos fortes definidos antes do ranking: {', '.join(strong)}.\n")
parts.append('\n## 22 Os dados que o leitor pode inspecionar\n\nOs arquivos completos do catálogo, consultas e 2.262 julgamentos estão no pacote. Aqui mostramos a identificação dos 39 itens e todas as consultas portuguesas para tornar visível a cobertura temática. As traduções inglesas e descrições bilingues completas estão nos JSON, não foram ocultadas.\n')
parts.append(table(['ID','Título','Fonte de identificação'],[[x['id'],x['title'],x['source_url']] for x in C]))
parts.append('\n\n### Todas as consultas em português\n')
for q in Q:parts.append(f"\n- {q['id']} / {q['theme']}: {q['text_pt']}\n")
parts.append('\n\n### Um item completo para entender o formato\n\nO campo description_origin explicita que o texto é do piloto, não uma sinopse oficial.\n\n```json\n'+json.dumps(C[0],ensure_ascii=False,indent=2)+'\n```\n')

GUIDE={
'01-preparar-linux.sh':('Preparação Linux','Recebe os diretórios do laboratório e dos downloads. Confere Linux e revisões Git, copia ou obtém os repositórios, cria o ambiente Python e registra versões. prepare_repo organiza a conferência de código. Não é um modelo e não deve ser executado toda vez que se faz uma consulta.'),
'02-executar-oficial.sh':('Execução dos exemplos oficiais','Recebe glove ou fasttext. Confere ambiente, impede sobrescrita de modelos e cria diretório exclusivo de execução. download_zip baixa em arquivo temporário, verifica ZIP e publica a entrada. trap registra encerramento inclusive em erro; GNU time mede recursos. Para GloVe executou o demo oficial. A rota fastText original dependia do RW inacessível e foi complementada por execução por etapas.'),
'03-atualizar-manifesto.ps1':('Inventário preparatório Windows','Recebe caminhos de downloads/repositórios e produz JSON com tamanho, hash, MD5 publicado e revisões. Usa ferramentas PowerShell, não Ubuntu. O arquivo inicial contém estados daquela fase; não é um detector universal de tudo que foi feito posteriormente. Não reexecutar para apagar a história sem preservar a versão anterior.'),
'04-fasttext-etapas.sh':('Treinamento e tutorial fastText separados','Recebe embeddings ou cooking. Seleciona G++ 12, confere commit e fonte sem edição, cria logs e registra hashes. embeddings treina com os parâmetros do script oficial e verifica números; cooking corta a base e chama supervised/test/predict. A mensagem RW pendente registra o estado do treino, encerrado antes da avaliação posterior.'),
'05-consultar-glove.py':('Consulta GloVe','Recebe --vectors, --word e --top-k. Lê a tabela textual, converte para matriz NumPy, normaliza linhas e calcula produtos escalares. Exclui a própria palavra, ordena vizinhos e informa ausência de vocabulário. Não treina e não transforma resultados em probabilidade.'),
'06-exportar-registros.sh':('Exportação de evidências','Copia runs concluídos e manifestos para a pasta Windows, calcula hashes e registra estado Git. Não copia automaticamente todos os pesos grandes. O inventário de Word2Vec text8, criado depois, é preservado também em manifesto próprio.'),
'07-avaliar-rw.sh':('Avaliação Rare Words','Usa o binário fastText e fil9.bin já treinado, prepara a lista de termos e chama eval.py oficial. Cria uma nova pasta de avaliação. A obtenção original Stanford falhou; a rota corroborada fornece o arquivo local antes de invocar este script. Não há retreino.'),
'09-word2vec-lee.py':('Teste didático Word2Vec','Lê Lee pelo datapath do Gensim, simple_preprocess prepara documentos. Treina CBOW e Skip-gram, consulta vetor/vizinhos, verifica KeyError para OOV, salva/carrega e exige igualdade do vetor. Avalia analogias, preserva seções e calcula cobertura. O resultado é didático, não evidência suficiente para recomendação.'),
'10-word2vec-executar.sh':('Runner Word2Vec Lee','Ativa o Python 3.12 apropriado, cria run com identificação e invoca o script Python sob GNU time. Registra início/fim/código e hash do script. Separar runner do algoritmo facilita auditar as mesmas operações sem mudar a biblioteca.'),
'11-preparar-python-word2vec.sh':('Python compatível e Gensim','Baixa CPython 3.12.16 oficial, confere SHA-256, executa configure, make -j4 e altinstall num prefixo do usuário. Cria o venv Gensim, instala a versão fixa e preserva relatórios pip/requisitos. Os módulos ssl/sqlite3/bz2/lzma/ctypes são checados para detectar compilação incompleta.'),
'12-auditar-rw.py':('Auditoria da cópia RW','Recebe os artefatos de origem e cruza notebook AWS, ZIP e cópia acadêmica. Verifica estrutura e 2.034 pares/notas com decimais, incluindo repetições e ordem. Calcula o blob Git da cópia para conferir sua identidade. Produz auditoria.json; falha em inconsistência em vez de avaliar silenciosamente outra base.'),
'13-rw-copia-verificada.sh':('Ponte entre auditoria e avaliação','Encadeia a auditoria, a publicação local do dataset aceito e o avaliador já preparado. Não usa treinamento/endpoint AWS; o espelho é arquivo público. A função do wrapper é impedir avaliação antes da conferência de procedência.'),
'14-rw-resultado-exato.py':('Captura de correlação sem arredondamento','Executa o eval.py oficial por runpy e acessa suas variáveis finais para salvar rho exato, pares avaliados e descartados. Não troca a fórmula de Spearman nem altera o arquivo dos autores. Evita interpretar o inteiro 42 como acurácia.'),
'15-sentencas-minilm.py':('Aquisição e teste do encoder','Obtém revisão fixa com HfApi, baixa snapshot filtrado e carrega com código remoto desabilitado. encode é usado nas frases oficiais; checks verificam matriz finita e recarga local. Salva pesos, exemplo numérico e hashes de todos os arquivos. O teste sintético adicional é explicitamente próprio.'),
'16-sentencas-executar.sh':('Runner MiniLM','Seleciona ambiente de sentenças, cria run, registra código e tempo/memória e chama o teste Python. O tempo inicial engloba download e gravação. Não o interpretar como uma chamada comum de busca.'),
'17-sentencas-instalar.sh':('Receita de reprodução das dependências','Fixa as versões principais observadas de PyTorch CPU e Sentence Transformers e registra pacotes. Foi preparado após a instalação inicial. A existência do script não significa que uma segunda instalação foi feita.'),
'01-treinar-word2vec-text8.py':('Treino adicional em corpus maior','Verifica o SHA do text8, usa Text8Corpus e treina duas variantes com parâmetros prévios e seed. A classe Progress informa épocas, sem servir de métrica de qualidade. Salva .model e registra duração, vocabulário e hash. Não lê animes ou relevâncias.'),
'02-criar-base.py':('Construção e congelamento do piloto','Contém o catálogo/descrições e as intenções preparados com IA. Verifica IDs da fonte AOD, gera duas formulações e traduções, expande os graus para todos os 2.262 pares e salva hashes. Recusa recriar freeze existente. O congelamento não substitui independência dos anotadores.'),
'03-codificar-modelo.py':('Representações e scores sem acessar rótulos','Recebe --model e --output. tokens normaliza texto lexical; normalized faz normalização L2. Carrega o modelo apropriado, lê somente dados textuais e verifica hashes, sem usar relevâncias para score. Usa média IDF nos estáticos, TF-IDF no controle e tokenizer/encode próprios no MiniLM. Salva matrizes/tempos e rejeita dimensões ou números inválidos.'),
'04-rodar-codificadores.sh':('Orquestração das oito configurações','Escolhe o ambiente Python por modelo e executa um encoder por vez com GNU time. Mantém seis principais e dois Lee diagnósticos. Pula saídas existentes para preservá-las; não é comando para repetir uma versão nova de experimento automaticamente.'),
'05-avaliar.py':('Métricas e incerteza','groups identifica empates; metrics calcula nDCG, Hit, MRR, recall e precisão com expectativa dentro dos empates. Lê scores e julgamentos só nesta fase, confere nDCG contra sklearn e faz bootstrap agrupado por família. Salva resumo, CSV e rankings completos. Não altera os pesos.'),
'06-gerar-relatorios.py':('Apresentação do piloto','Lê resultados preservados e gera Markdown, gráfico, CSV agregado, painel HTML e PDF. Não executa inferência. Seu texto registra a recomendação anterior ao esclarecimento do escopo estático; deve ser lido com a atualização do documento 09 e este manual. Não reexecutar esse texto histórico como decisão atual sem revisão.'),
'07-verificar-entrega.py':('Checagem da entrega do piloto','Confere hashes do congelamento, dimensões dos rankings, 47/58 no MiniLM e links locais. Produz manifesto de hashes dos artefatos. Essa verificação confirma integridade e consistência, não legitimidade dos julgamentos nem validade científica universal.'),
'18-fasttext-vocabulario-codigo.py':('Verificação pontual de vocabulário','Percorre o arquivo textual fastText para conferir se o termo didático desconhecido pertence à lista. O resultado False estabelece ausência na tabela; junto do vetor produzido pelo .bin demonstra composição OOV, sem avaliar semântica.'),
'gerar-manual.py':('Consolidação documental','Lê documentos e resultados, monta tabelas automaticamente, incorpora os scripts, gera PDF/HTML/Markdown e cria um pacote de evidências sem pesos volumosos. Não altera dados, pesos ou julgamentos. O código deste gerador também é preservado para mostrar como o documento foi montado.'),
}
SOURCES=sorted((LAB/'scripts').glob('*'))+sorted((PILOT/'codigo').glob('*'))+[LAB/'logs/18-fasttext-vocabulario-codigo.py',pathlib.Path(__file__).resolve()]
SOURCES=[p for p in SOURCES if p.is_file() and p.suffix in ['.py','.sh','.ps1']]
parts.append('\n## 23 Guia dos programas próprios\n\nCada entrada informa a responsabilidade do arquivo e como ele se relaciona às evidências. O código completo está no anexo final. Não copiamos aqui todo o código C/C++ dos projetos externos: ele é identificado por revisão, repositório e licença. Os scripts próprios usam as ferramentas oficiais e registram operações.\n')
for p in SOURCES:
    title,desc=GUIDE[p.name]
    parts.append(f'\n### {title}\n\nArquivo: {p.relative_to(ROOT).as_posix()}.\n\n{desc}\n')
parts.append('\n\n### Construções de código que aparecem repetidamente\n\nset -euo pipefail pede ao Bash para encerrar em falhas relevantes, variáveis ausentes e erros de pipelines. Isso reduz continuação silenciosa; não garante correção científica. mktemp cria pastas exclusivas de execução. trap registra término. tee exibe e grava saída. source ativa variáveis de um ambiente no shell atual. argparse lê opções nomeadas. pathlib organiza caminhos. assert interrompe diante de uma condição inesperada. JSON organiza metadados; CSV permite análise tabular; NPZ armazena matrizes NumPy comprimidas.\n\nsubprocess chama o executável fastText a partir de Python. Um processo persistente evita carregar o mesmo modelo para cada palavra no lote. Cache reutiliza um resultado já calculado. Por isso os tempos com cache não podem ser anunciados como latência individual da primeira consulta.\n')

parts.append('\n## 24 Decisões atuais sobre estáticos LLMs e APIs\n\nO capítulo a seguir incorpora a atualização de escopo registrada após Lucas confirmar a classe do modelo final. Prevalece sobre recomendações anteriores dos materiais do piloto. Os preços são exemplos documentados em 29/10/2026, não orçamento fixo ou teste de acesso de conta.\n')
scope=(LAB/'docs/09-estaticos-llms-e-escopo-tcc.md').read_text(encoding='utf-8')
scope='\n'.join(scope.splitlines()[2:]);scope=re.sub(r'^## ', '### ',scope,flags=re.M)
parts.append(scope)
parts.append('\n## 25 Roteiro de reprodução e critérios de conclusão\n\nPara consultar, basta usar pesos existentes nos ambientes corretos. Para reproduzir desde zero em outra máquina, é preciso preparar Ubuntu/dependências, adquirir as mesmas revisões e bases, verificar integridade, construir o Python compatível, executar treinos e comparar as evidências. Os próximos registros mostram os comandos históricos. Não presumir que instalar a versão mais nova de tudo reproduz o mesmo ambiente.\n\nUma execução funcional exige encerramento documentado e artefatos coerentes. Um resultado científico exige também tarefa e dados apropriados, avaliação independente e hipóteses delimitadas. A instalação correta não implica que os vizinhos lexicais ou rankings serão bons. Acurácia de analogias, correlação RW e nDCG de busca não podem ser comparadas diretamente como uma única pontuação.\n\nPara uma nova coleta anime, versionar o catálogo, fonte, licença e idioma; separar desenvolvimento/teste por intenção; usar julgamentos humanos cegos aos sistemas; definir tratamento de sinopses longas, nomes e OOV; fixar prompts/agregadores antes do teste; medir latência com catálogo já indexado e custo inicial separadamente.\n')

# Registros detalhados mantidos como anexos históricos, não como nova execução.
parts.append('\n## Anexo A Procedimentos históricos de instalação e avaliação\n\nOs registros abaixo foram produzidos durante as etapas. Algumas frases prospectivas refletem o estado daquele momento; o quadro atual deste manual prevalece. Eles detalham comandos e evidências, mas não significam que as operações foram executadas outra vez na consolidação.\n')
for name in ['02-guia-de-execucao.md','05-execucoes-reais.md','06-word2vec.md','07-rare-words-resolucao.md','08-embeddings-sentencas.md']:
    t=(LAB/'docs'/name).read_text(encoding='utf-8')
    t=re.sub(r'^#{1,3} ', '#### ', t,flags=re.M)
    parts.append(f'\n### Registro {name}\n\nOrigem local: laboratorio/docs/{name}. Documento histórico; estados pendentes devem ser lidos com os resultados subsequentes consolidados.\n\n'+t)

parts.append('\n## Anexo B Fontes e referências\n\nAs fontes listadas foram as referências de aquisição/uso ou de propostas discutidas. Uma referência de um modelo não significa que seus pesos foram baixados. Priorizar autores e mantenedores; guardar revisão e data. As citações acadêmicas ainda precisam ser formatadas conforme as normas do TCC.\n')
parts.append((LAB/'docs/04-fontes.md').read_text(encoding='utf-8').replace('# Fontes', '### Fontes',1))
parts.append('\n\n### Fonte do catálogo e avaliação\n\n[Release Anime Offline Database](https://github.com/manami-project/anime-offline-database/releases/tag/2026-27). [JSON da release](https://github.com/manami-project/anime-offline-database/releases/download/2026-27/anime-offline-database-minified.json). [nDCG sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html). [TF-IDF sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).\n')
parts.append('\n## Anexo C Identificação dos artefatos\n\nOs blocos abaixo são cópias dos manifestos selecionados. Manifestos completos, requisitos e logs estão no pacote. O hash de um arquivo comprova igualdade de bytes com a referência aqui registrada; não prova, sozinho, origem legítima ou qualidade.\n')
for name in ['manifests/word2vec-text8-piloto.json','manifests/rw/auditoria.json','piloto-animes/dados/freeze.json']:
    value=json.loads((LAB/name).read_text(encoding='utf-8-sig'))
    parts.append('\n### '+name+'\n\n```json\n'+json.dumps(value,ensure_ascii=False,indent=2)+'\n```\n')
for m in STATE['models']:
    if 'sha256' in m:parts.append(f"\n- {m['name']}: SHA-256 {m['sha256']}.\n")
parts.append('\n## Anexo D Código completo dos programas próprios\n\nO anexo incorpora as versões existentes no momento da geração. Os números à esquerda identificam linhas do arquivo original; uma linha longa pode continuar em outra linha visual. Para executar, use os arquivos originais do pacote, não copie os números impressos. Comentários e textos históricos no código devem ser lidos no contexto descrito no guia. Não há um script 08 na sequência principal: a numeração não implica ausência de uma instalação obrigatória.\n')
for p in SOURCES:
    code=p.read_text(encoding='utf-8-sig');lang='python' if p.suffix=='.py' else 'powershell' if p.suffix=='.ps1' else 'bash'
    parts.append(f'\n### {p.relative_to(ROOT).as_posix()}\n\nSHA-256 {hashlib.sha256(p.read_bytes()).hexdigest()}\n\n```{lang}\n{code.rstrip()}\n```\n')

parts.append('\n## Anexo E Arquivos de evidência disponíveis\n\nO inventário abaixo permite localizar os logs sem imprimir milhares de linhas de progresso do compilador. Todos esses arquivos acompanham o pacote de evidências. Um log de tentativa malsucedida permanece preservado, não é apresentado como sucesso. Arquivos muito grandes de pesos e corpora permanecem nos caminhos explicitados.\n')
logrows=[[str(p.relative_to(LAB)),p.stat().st_size] for p in sorted((LAB/'logs').glob('*')) if p.is_file()]
parts.append(table(['Registro','Bytes'],logrows))
parts.append('\n\n### Limites da consolidação\n\nO pacote é uma fotografia documental dos arquivos locais do laboratório, não imagem completa do sistema operacional. Não inclui credenciais, pesos grandes Linux nem os arquivos integrais de corpora que já estão nos caminhos registrados. A geração não iniciou treino, não mudou julgamentos, não configurou APIs e não publicou documentos externamente.\n')
md='\n\n'.join(parts)
(OUT/'manual-completo-anirec.md').write_text(md,encoding='utf-8')

# Parser mínimo e determinístico para a estrutura Markdown usada nesta entrega.
def parse(text):
    lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            lang=line[3:];i+=1;buf=[]
            while i<len(lines) and not lines[i].startswith('```'):buf.append(lines[i]);i+=1
            yield 'code',lang,'\n'.join(buf);i+=1;continue
        h=re.match(r'^(#{1,4}) (.*)$',line)
        if h:yield 'heading',len(h[1]),h[2];i+=1;continue
        image=re.match(r'^!\[([^]]*)\]\(([^)]+)\)$',line)
        if image:yield 'image',image[1],image[2];i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=[x.strip() for x in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',x) for x in row):rows.append(row)
                i+=1
            yield 'table',None,rows;continue
        buf=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#{1,4} |```|\||!\[)',lines[i]):buf.append(lines[i]);i+=1
        yield 'paragraph',None,' '.join(buf)

blocks=list(parse(md))
def hinline(t):
    t=html.escape(t)
    t=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t)
    t=re.sub(r'`([^`]+)`',r'<code>\1</code>',t)
    return t
ht=[];nav=[];headingid=0
for typ,a,b in blocks:
    if typ=='heading':
        headingid+=1;anchor=f's{headingid}';ht.append(f'<h{min(a,4)} id="{anchor}">{hinline(b)}</h{min(a,4)}>')
        if a==2:nav.append(f'<li><a href="#{anchor}">{html.escape(b)}</a></li>')
    elif typ=='paragraph':ht.append('<p>'+hinline(b)+'</p>')
    elif typ=='code':ht.append('<pre><code>'+html.escape(b)+'</code></pre>')
    elif typ=='table':ht.append('<div class="table"><table>'+''.join('<tr>'+''.join(f'<{"th" if j==0 else "td"}>{hinline(x)}</{"th" if j==0 else "td"}>' for x in row)+'</tr>' for j,row in enumerate(b))+'</table></div>')
    elif typ=='image':
        import base64
        imagepath=ROOT/'laboratorio/piloto-animes/relatorios/comparacao-idiomas.png'
        encoded=base64.b64encode(imagepath.read_bytes()).decode()
        ht.append(f'<img alt="{html.escape(a)}" src="data:image/png;base64,{encoded}">')
htmlpage='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Manual completo AniRec</title><style>body{font:17px/1.7 system-ui;color:#202d39;max-width:1000px;margin:40px auto;padding:0 24px;background:#fff}h1,h2,h3,h4{line-height:1.3;color:#121a22;scroll-margin-top:20px}h2{margin-top:65px;border-top:1px solid #d5dce2;padding-top:24px}h3{margin-top:36px}nav{background:#f0f4f8;padding:20px;border-radius:8px}a{color:#075d96}pre{font:13px/1.5 Consolas,monospace;background:#f4f6f8;padding:18px;overflow:auto;tab-size:4}code{font-family:Consolas,monospace}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #ccd3da;padding:9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e7eef4}tr:nth-child(even){background:#f8fafb}img{max-width:100%}@media print{nav{display:none}h2{break-before:page}pre{white-space:pre-wrap;font-size:9px}body{font-size:11px}}</style><nav><strong>Conteúdo navegável</strong><ol>NAV</ol></nav>BODY</html>'''.replace('NAV',''.join(nav)).replace('BODY',''.join(ht))
(OUT/'manual-completo-anirec.html').write_text(htmlpage,encoding='utf-8')

# PDF com fontes Unicode, sumário paginado e marcadores navegáveis.
fontdir=pathlib.Path('C:/Windows/Fonts')
for name,file in [('Body','arial.ttf'),('BodyBold','arialbd.ttf'),('BodyItalic','ariali.ttf'),('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=10.5,leading=15.3,spaceAfter=8,allowWidows=0,allowOrphans=0,splitLongWords=True),
 'h1':ParagraphStyle('h1',fontName='BodyBold',fontSize=24,leading=30,spaceAfter=22,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=17,leading=22,spaceBefore=6,spaceAfter=14,keepWithNext=True),
 'h3':ParagraphStyle('h3',fontName='BodyBold',fontSize=12.5,leading=17,spaceBefore=14,spaceAfter=8,keepWithNext=True,splitLongWords=True),
 'h4':ParagraphStyle('h4',fontName='BodyBold',fontSize=11,leading=15,spaceBefore=10,spaceAfter=6,keepWithNext=True),
 'code':ParagraphStyle('code',fontName='Mono',fontSize=7.8,leading=10.2,spaceBefore=6,spaceAfter=10),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=8.0,leading=11.2,splitLongWords=True),
}
def ptext(t):
    # URLs permanecem clicáveis e visíveis; o renderer quebra termos longos.
    t=html.escape(t)
    t=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<link href="\2" color="#075d96">\1</link> (\2)',t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t);t=t.replace('`','')
    return t

class ManualDoc(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(path,pagesize=A4,leftMargin=1.9*cm,rightMargin=1.9*cm,topMargin=1.8*cm,bottomMargin=1.8*cm,title='Manual completo do laboratório AniRec',author='Lucas | documentação preparada com assistência do Codex')
        frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='normal',frames=frame,onPage=self.footer))
    def footer(self,c,doc):
        c.saveState();c.setFont('Body',8);c.setFillColor(colors.HexColor('#52616d'));c.drawString(self.leftMargin,1.05*cm,'AniRec | laboratório documentado em 29/10/2026');c.drawRightString(A4[0]-self.rightMargin,1.05*cm,str(doc.page));c.restoreState()
    def afterFlowable(self,f):
        if hasattr(f,'bookmark'):
            key,title=f.bookmark;self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,level=0,closed=False)
            self.notify('TOCEntry',(0,title,self.page,key))

story=[]
story.append(Spacer(1,2.8*cm))
story.append(Paragraph('Manual completo do laboratório de modelos textuais AniRec',styles['h1']))
story.append(Paragraph('Instalações testes resultados códigos e decisões para o TCC',styles['h3']))
story.append(Spacer(1,1*cm))
for line in ['Lucas','Registro consolidado em 29 de outubro de 2026','Preparado com assistência do Codex','Leitura principal em linguagem simples e anexos técnicos completos']:
    story.append(Paragraph(line,styles['body']))
story.append(Spacer(1,1*cm))
story.append(Paragraph('<b>Escopo atual:</b> o sistema final usará modelos estáticos. MiniLM é um comparador contextual. Nenhum gerador LLM foi instalado ou avaliado.',styles['body']))
story.append(Paragraph('<b>Limite do piloto:</b> os títulos são reais, mas descrições, consultas e julgamentos foram preparados com IA e não receberam validação humana independente.',styles['body']))
story.append(PageBreak())
story.append(Paragraph('Sumário',styles['h2']))
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Body',fontSize=10.2,leading=17,spaceBefore=3,leftIndent=0,firstLineIndent=0)]
story.extend([toc,PageBreak()])
headingno=0;seenfirst=False
for typ,a,b in blocks:
    if typ=='heading':
        if a==1:continue
        if a==2:
            if seenfirst:story.append(PageBreak())
            seenfirst=True
        para=Paragraph(ptext(b),styles['h'+str(a)])
        if a==2:
            headingno+=1;para.bookmark=(f'chapter-{headingno}',b)
        story.append(para)
    elif typ=='paragraph':
        if not seenfirst:continue
        story.append(Paragraph(ptext(b),styles['body']))
    elif typ=='code':
        lines=[]
        for no,line in enumerate(b.expandtabs(4).splitlines(),1):
            wrapped=textwrap.wrap(line,width=88,replace_whitespace=False,drop_whitespace=False,break_long_words=True,break_on_hyphens=False) or ['']
            # Numerar apenas código completo do anexo; exemplos também têm numeração
            # de apresentação, e a instrução de copiar o arquivo original é explícita.
            lines.extend([f'{no:4d}  {wrapped[0]}']+['      '+x for x in wrapped[1:]])
        story.append(Preformatted('\n'.join(lines),styles['code']))
    elif typ=='image':
        story.append(Image(str(PILOT/'relatorios/comparacao-idiomas.png'),width=17.2*cm,height=5.73*cm));story.append(Spacer(1,10))
    elif typ=='table':
        n=len(b[0]);width=17.2*cm
        if n==2:widths=[width*.73,width*.27]
        elif n==3:widths=[width*.29,width*.22,width*.49]
        elif n==4:widths=[width*.46]+[width*.18]*3
        else:widths=[width*.29]+[width*.71/(n-1)]*(n-1)
        cells=[[Paragraph(ptext(x),styles['cell']) for x in row] for row in b]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf4')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbd3da')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafb')])]))
        story.extend([t,Spacer(1,10)])
pdfpath=OUT/'manual-completo-anirec.pdf'
ManualDoc(str(pdfpath)).multiBuild(story)

# Checagem e renderização para inspeção visual posterior.
import pymupdf
from PIL import Image as PILImage, ImageDraw
doc=pymupdf.open(pdfpath)
qa=ROOT/'tmp/manual-qa';qa.mkdir(parents=True,exist_ok=True)
pageinfo=[]
for i,page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1,1)).save(qa/f'pagina-{i+1:03d}.png')
    outside=[]
    for w in page.get_text('words'):
        if w[0]<25 or w[2]>A4[0]-25 or w[1]<20 or w[3]>A4[1]-20:outside.append(w[4])
    pageinfo.append({'page':i+1,'characters':len(page.get_text()),'outside_page_guard':outside})
for start in range(0,len(doc),12):
    thumbs=[]
    for i in range(start,min(start+12,len(doc))):
        im=PILImage.open(qa/f'pagina-{i+1:03d}.png').convert('RGB');im.thumbnail((390,552))
        tile=PILImage.new('RGB',(410,582),'#dce3e9');tile.paste(im,((410-im.width)//2,12));ImageDraw.Draw(tile).text((15,565),f'Pagina {i+1}',fill='black');thumbs.append(tile)
    sheet=PILImage.new('RGB',(410*4,582*3),'#dce3e9')
    for j,im in enumerate(thumbs):sheet.paste(im,((j%4)*410,(j//4)*582))
    sheet.save(qa/f'contato-{start//12+1:02d}.png')
quality={'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pages':len(doc),'chapters':headingno,'scripts_in_full':len(SOURCES),'markdown_characters':len(md),'page_checks':pageinfo,'data_qa':R['qa'],'visual_review':'PNG renderizado; inspeção humana assistida pelo agente deve ocorrer antes da entrega.'}
(OUT/'verificacao-manual.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')

# Arquivos pequenos e evidências completas acompanham o manual; não incluir pesos.
zip_path=OUT/'anirec-evidencias-e-codigos.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(LAB.rglob('*')):
        if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.pyc']:
            z.write(p,p.relative_to(ROOT).as_posix())
    for p in [OUT/'manual-completo-anirec.md',OUT/'manual-completo-anirec.html',OUT/'verificacao-manual.json']:
        z.write(p,p.relative_to(ROOT).as_posix())
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [pdfpath,OUT/'manual-completo-anirec.md',OUT/'manual-completo-anirec.html',zip_path]}
(OUT/'manifesto-entrega.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(doc),'scripts':len(SOURCES),'markdown_characters':len(md),'pdf':str(pdfpath),'zip_bytes':zip_path.stat().st_size,'outside_guard':sum(bool(p['outside_page_guard']) for p in pageinfo)},ensure_ascii=False))
