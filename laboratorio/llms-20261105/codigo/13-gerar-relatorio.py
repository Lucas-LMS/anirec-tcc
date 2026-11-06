"""Gera relatório legível e gráficos a partir de resultados já congelados."""
import datetime,html,json,textwrap,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

BASE=Path(__file__).resolve().parents[1];WORK=BASE.parents[1]
SOURCE=BASE/'resultados/comparacao/comparacao.json'
OUT=WORK/'output/comparacao-sms';OUT.mkdir(parents=True,exist_ok=True)
data=json.loads(SOURCE.read_text(encoding='utf-8'))
preliminary='--preliminary' in sys.argv
assert data['complete'] or preliminary,'Não publicar relatório final com modelos faltando.'
suffix='preliminar' if preliminary else 'comparacao'
pending=[x for x in ['deepseek','qwen'] if x not in {m['model'] for m in data['models']}]
status=f"PRELIMINAR: {len(data['models'])}/13 pipelines concluídos. Pendentes: {', '.join(pending) or 'nenhum'}." if preliminary else 'COMPLETO: 13/13 pipelines concluídos.'
models=sorted(data['models'],key=lambda x:-x['f1_spam'])
by={x['model']:x for x in models}
if by.get('qwen',{}).get('metadata',{}).get('interruption'):
    status+=' Qwen: retomado após um timeout; latências de respostas concluídas excluem a tentativa anterior que expirou. Tempo total original indisponível.'
static=['glove','fasttext','w2v-cbow','w2v-sg']
winner=max((by[x] for x in static),key=lambda x:x['f1_spam'])
candidate=max((by[x] for x in static),key=lambda x:x['full_test_775']['f1_spam'])
def percent(x):return f'{100*x:.1f}%'
def val(x):return f'{x:.3f}'
def family(x):return '#247c66' if x['model'] in static else '#3357a8' if x['model']=='minilm' else '#aa6633' if x['model'] in ['llama','deepseek','qwen','gptoss'] else '#7b8493'

# Intervalos por bootstrap são exploratórios e compartilham amostras entre modelos.
fig,ax=plt.subplots(figsize=(10,7.5));ordered=models[::-1]
for i,x in enumerate(ordered):
    lo,hi=x['f1_ci95'];ax.plot([lo,hi],[i,i],color=family(x),lw=2);ax.scatter([x['f1_spam']],[i],color=family(x),s=45,zorder=3)
ax.set(yticks=range(len(ordered)),yticklabels=[x['name'] for x in ordered],xlim=(-.02,1.02),xlabel='F1 spam; intervalo exploratório de 95% (bootstrap estratificado)',title='Mesmas 200 mensagens: 175 ham e 25 spam')
ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(OUT/f'qualidade-f1-{suffix}.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,7.5))
for i,x in enumerate(ordered):ax.scatter(x['median_ms'],i,color=family(x),s=40);ax.plot([x['median_ms'],x['p95_ms']],[i,i],color=family(x),lw=2)
ax.set_xscale('log');ax.set(yticks=range(len(ordered)),yticklabels=[x['name'] for x in ordered],xlabel='Milissegundos por SMS (escala log); ponto = mediana, ponta = p95',title='Resposta completa, após aquecimento; Groq inclui rede e serviço')
ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(OUT/f'tempo-resposta-{suffix}.png',dpi=180);plt.close(fig)

sections=[]
def add(title,body):sections.append((title,body))
add('1. O que foi feito e o que esta comparação significa',f'''{status} Em 05/11/2026 concluímos {len(data['models'])} pipelines sobre as mesmas 200 mensagens rotuladas do SMS Spam Collection baixado do Kaggle. Instalamos os geradores locais, recuperamos o ambiente WSL após ativação da virtualização e incluímos GPT-OSS 20B pela Groq, conforme a opção gratuita escolhida pelo usuário. A comparação mede classificação binária, recursos e tempo de resposta. O arquivo comparacao.json é a fonte numérica; cada modelo conserva predições, metadados e logs. Modelos pendentes não entram nas tabelas; não tratamos predições de um prefixo incompleto como se cobrissem as 200 mensagens.

O maior F1 observado pode ser consultado na tabela. Entre os quatro embeddings estáticos de interesse principal, o maior valor pontual nos 200 exemplos comuns foi de {winner['name']}: F1 {val(winner['f1_spam'])}. No complemento de 775, o melhor estático foi {candidate['name']}, F1 {val(candidate['full_test_775']['f1_spam'])}. A troca de ordem limita a alegação de um vencedor estável. Recomendamos CBOW como candidato provisório para desenvolvimento estático, mantendo GloVe como concorrente próximo, sem decidir ainda o modelo final de anime. O objetivo de usar modelos estáticos no TCC foi preservado. MiniLM e os geradores são comparadores.

Não planejamos provar que estáticos vencem LLMs. Testamos uma hipótese de utilidade e eficiência de pipelines acessíveis. Se o resultado contradiz a preferência inicial, ele deve aparecer. Não usamos o teste para escolher novos parâmetros nesta rodada.''')
add('2. Por que escolhemos esse dataset', '''SMS Spam Collection é uma coleção pequena de textos curtos em inglês, com dois rótulos existentes: ham (mensagem legítima) e spam (publicidade não solicitada, golpe ou promoção). O Kaggle permite aquisição simples e uma execução local viável. Cada mensagem tem uma resposta esperada, de modo que precisão, recall, F1 e erros podem ser calculados sem inventar avaliações humanas. O tamanho permite comparar latência por mensagem em CPU e numa API limitada.

Escolher essa base reduz a complexidade do teste técnico inicial. Ela não mede busca semântica, recomendação, qualidade de sinopses ou tradução português-inglês. No futuro projeto de anime, será necessário outro protocolo: consultas em português, sinopses em inglês, relevância revisada por humanos, separação de consultas de desenvolvimento/teste e métricas de ranking como nDCG, MRR e Recall@k. Não transportar o ranking deste experimento diretamente para esse cenário.

A cópia Kaggle tem 5.572 linhas: 4.825 ham e 747 spam. A descrição anuncia 5.574; usamos a contagem real. Depois de normalização para detectar duplicatas (NFKC, casefold e espaços), restaram 5.157 exemplos sem grupos de rótulos conflitantes. Os textos originais foram mantidos como entrada. As duplicatas foram agrupadas antes da divisão para evitar a mesma mensagem em treino e teste.

Divisão estratificada com seed 20261105: treino 3.609 (3.160 ham, 449 spam), validação 773 (677 ham, 96 spam), teste 775 (678 ham, 97 spam). Antes de prever, congelamos 200 IDs do teste: 175 ham e 25 spam. Esses 200 são a comparação principal de TODOS os modelos. O teste completo de 775 só aparece como complemento dos classificadores. Não houve ajuste por validação nesta rodada; a partição está reservada para desenvolvimento futuro.

O dataset é público e antigo: não sabemos se os LLMs o encontraram no pré-treinamento. A licença indicada no metadado Kaggle é Unknown; a página original UCI informa CC BY 4.0. Registramos essa diferença. Atribuição: Almeida e Hidalgo, SMS Spam Collection, DOI 10.24432/C5CC84; artigo Almeida, Hidalgo e Yamakami, DOCENG 2011.''')
add('3. Quais modelos são esses e de onde vieram', '''GloVe (Stanford, Pennington, Socher e Manning): aprende vetores de palavras usando estatísticas globais de coocorrência. Aqui usamos o vectors.txt já treinado com o demo oficial text8: 50 dimensões, 71.290 palavras, 15 iterações. Cada palavra conhecida recebe um vetor fixo. Palavras fora do vocabulário não têm vetor nessa implementação.

fastText (Facebook/Meta, projeto de Bojanowski e colaboradores): representa palavras com informação de subpalavras, permitindo compor vetores para palavras novas. Usamos o binário oficial v0.9.2 e o fil9.bin existente, 100 dimensões, 218.316 entradas, uma época. O modelo ocupa aproximadamente 978 MB no disco. A composição por subpalavras funciona mesmo quando não há entrada exata. O acesso ocorre pelo CLI em um processo persistente; a comunicação por pipes entra no tempo medido. Não é um teste da velocidade intrínseca de todas as integrações possíveis de fastText.

Word2Vec (Mikolov e colaboradores): CBOW prevê uma palavra usando seu contexto; Skip-gram prevê palavras vizinhas a partir da palavra central. Usamos Gensim 4.4, modelos text8 de 100 dimensões, janela 5, min_count 5, cinco épocas, quatro workers, seed 20261029 e 71.290 palavras. CBOW e Skip-gram são avaliados separadamente. Os dois modelos Lee, treinados em corpus diminuto (1.750 palavras), são controles diagnósticos e não candidatos equivalentes aos text8.

MiniLM é uma família de Transformers compactos proposta pela Microsoft Research por Wang e colaboradores, com destilação de relações de autoatenção. O modelo concreto utilizado aqui não é só o artigo MiniLM: é sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2, publicado pela organização sentence-transformers, associado ao trabalho de Reimers e Gurevych/UKPLab em representações de sentenças e destilação multilíngue. São 12 camadas, saída de 384 dimensões e limite operacional de 128 tokens nesta configuração. Ele usa contexto e pooling para produzir um vetor da sentença. Não é embedding estático e não é um gerador de texto. Revisão fixada: e8f8c211226b894fcb81acc59f3b34ba3efd5f42. Sete mensagens de treino e uma do teste completo ultrapassaram 128 tokens; nenhuma das 200 comuns ultrapassou.

Llama 3.2 1B Instruct é um gerador da Meta. Instalamos GGUF Q4_K_M de Bartowski (conversão comunitária), 807.694.464 bytes, revisão 067b946cf014b7c697f3654f621d577a3e3afd1c. Usa licença própria Llama 3.2. Não equivale aos Llamas grandes hospedados.

DeepSeek-R1-Distill-Qwen-1.5B é um modelo destilado pela DeepSeek a partir de Qwen, não o DeepSeek completo. Instalamos GGUF Q4_K_M de Bartowski, 1.117.320.800 bytes, revisão 9cc28b17e86fa2415fcb070f8ee5ec27c965aa61, licença MIT indicada no cartão. O raciocínio gera tokens antes da resposta final e consome tempo/orçamento.

Qwen3 0.6B é um gerador pequeno da equipe Qwen/Alibaba. Usamos o GGUF oficial Q8_0, 639.446.688 bytes, revisão 23749fefcc72300e3a2ad315e1317431b06b590a, Apache 2.0. É alternativa local; não deve ser chamado de GPT.

GPT-OSS 20B é um modelo OpenAI de pesos abertos. Não baixamos seus pesos nem usamos um GPT proprietário do ChatGPT. Chamamos openai/gpt-oss-20b no provedor Groq. O usuário configurou chave para a opção Free; não houve upgrade ou contratação por esta execução. O hardware remoto é desconhecido e o modelo não é uma instalação local. Catálogo/cotas podem mudar e um GET autenticado não comprova modalidade de cobrança.

Os GGUF têm seus hashes verificados contra os arquivos dos publicadores. O runtime llama.cpp é oficial, mas isso não torna oficiais as conversões comunitárias Meta/DeepSeek. Modelos foram baixados, não treinados novamente neste benchmark. O diário anterior e instalacao.json registram origens e hashes completos.''')
add('4. Como os textos viram decisões', '''Um embedding é um vetor numérico: palavras ou sentenças semelhantes tendem a ter representações próximas, dependendo de treinamento e corpus. O embedding sozinho não devolve o rótulo spam. Nesta comparação, adicionamos regressão logística supervisionada para transformar o vetor em probabilidade de spam.

Nos estáticos, tokenizamos usando NFKC, casefold e sequências de letras, sem stopwords ou stemming. Calculamos uma média dos vetores ponderada por IDF: log((1+N)/(1+df))+1, com N e df extraídos somente do treino. Termo não visto recebe log(1+N)+1. GloVe/Word2Vec ignoram palavras sem vetor; fastText usa subpalavras. Normalizamos a representação por norma L2. O classificador tem C=1, max_iter=1000, class_weight=balanced, solver lbfgs e seed 20261105. A probabilidade >=0,5 define spam. Não otimizamos esse limiar no teste.

O baseline TF-IDF usa unigramas e bigramas, TF sublinear, L2 e vocabulário/IDF ajustados somente no treino. Não é embedding pré-treinado nem LLM; é uma referência lexical indispensável. O baseline de maioria sempre responde ham. O MiniLM gera um vetor normalizado por mensagem e recebe a mesma cabeça logística, sem fine-tuning do Transformer.

Os geradores recebem o mesmo prompt inglês que define ham/spam, manda tratar o SMS como dado e pede uma palavra. O texto é inserido como string JSON. É zero-shot: eles não recebem os 3.609 pares rotulados do treino. Portanto estamos comparando pipelines práticos com regimes de supervisão diferentes. Não é um experimento que isola o efeito causal da arquitetura.

Todos os geradores usam até 512 tokens de saída e temperatura 0,6; top_p 0,95. Llama: raciocínio desligado. DeepSeek: ligado. Qwen: ligado, top_k 20, min_p 0 e presence_penalty 1,5. GPT-OSS: reasoning_effort low. Seed varia deterministicamente por índice a partir de 20261105. Os locais usam contexto 2.048, quatro threads CPU e uma requisição por vez. O orçamento curto é uma restrição deste experimento, não reprodução do orçamento recomendado para benchmarks extensos de raciocínio.

O parser aceita somente ham ou spam após limpeza simples de pontuação/formatação externa. Explicação em vez de rótulo, vazio ou resposta truncada sem rótulo contam como inválida e como erro. Não extraímos uma palavra conveniente do raciocínio depois de olhar o teste. Não mudamos o orçamento para melhorar os resultados desta rodada.''')
add('5. O que as métricas dizem', '''Precisão spam é a fração de mensagens realmente spam entre as classificadas como spam. Recall spam é a fração dos spams existentes que foram encontrados. F1 combina as duas: 2TP/(2TP+FP+FN). TP é spam identificado; FP é ham acusado de spam; FN é spam perdido, incluindo uma resposta inválida para spam. Macro-F1 dá o mesmo peso às duas classes. Balanced accuracy é a média do recall de ham e spam. Acurácia é a proporção total de rótulos corretos.

Como só 25/200 são spam, dizer sempre ham produz 87,5% de acurácia e F1 spam zero. Acurácia sozinha é enganosa aqui. Uma única mensagem spam corresponde a quatro pontos percentuais de recall: a amostra positiva é pequena.

Usamos bootstrap estratificado pareado com 5.000 reamostragens, seed 20261105, preservando 175 ham e 25 spam e compartilhando os mesmos índices entre modelos. Intervalos são exploratórios, condicionais a esta amostra e aos modelos treinados; não incluem variação entre corpora, treinos, sementes ou hardware. Intervalos de diferenças entre GloVe e demais pipelines constam no JSON. Cruzar zero não comprova equivalência. O modelo com maior valor pontual não é automaticamente significativamente superior.

ROC-AUC e average precision (AP, que não é idêntica à área trapezoidal sob a curva PR) aparecem apenas para os classificadores com probabilidade. Não fabricamos probabilidades de LLMs a partir de rótulos ou confiança verbal. nDCG/MRR pertencem ao futuro ranking de animes, não a esta classificação.

As métricas foram calculadas por uma implementação explícita de matriz 2x3 (verdade ham/spam; predição ham/spam/inválida) e conferidas contra scikit-learn. IDs, ordem e hashes dos dados são validados antes de agregar resultados.''')
add('6. Como medimos velocidade e memória', '''Após aquecimento, cada SMS recebe uma chamada individual. Para encoders o cronômetro cobre tokenização/codificação e predict_proba, sem reutilizar vetores já calculados do teste. Três exemplos de treino aquecem os classificadores. Para geradores, uma mensagem sintética externa ao teste aquece o serviço. A latência cobre a resposta completa, incluindo raciocínio. Não usamos streaming: TTFT (tempo até primeiro token) não foi medido.

Média, mediana e p95 expressam aspectos diferentes: média inclui respostas demoradas; mediana é a observação central; p95 é um percentil amostral e não um limite garantido. Throughput serial é 1/latência média, não benchmark de servidor concorrente. Preparação/carga, codificação do treino e ajuste logístico aparecem separados. O tempo total de etapa dos geradores inclui aquecimento e, na Groq, pausas preventivas de cota; a soma das latências individuais não inclui essas pausas.

Groq tem intervalo mínimo local de 2,2 segundos, controle conservador da janela de tokens de 60 segundos, máximo de 205 chamadas e 150.000 tokens. Há espera limitada em 429; sem fallback pago. Não interpretar o tempo total com pausas como velocidade intrínseca do modelo. A latência remota inclui rede/serviço em hardware diferente, enquanto os locais usam CPU Ryzen 5 2400G no WSL2. Uma comparação causal de arquitetura exigiria condições de hardware e implantação controladas.

Pico RSS é memória residente observada de processo, não tamanho no disco nem soma de toda a máquina. GNU time captura o maior processo dos classificadores, inclusive o CLI fastText; geradores usam VmHWM do servidor, com cliente separado. O pico do serviço remoto Groq é desconhecido. O aquecimento/cache de prompt e a montagem de disco Windows também afetam tempos. Registramos apenas uma execução por configuração, sem repetição entre sementes.''')
add('7. Leitura dos resultados e recomendação',f'''Entre os estáticos de corpus text8/fil9, {winner['name']} teve o maior F1 pontual nos 200 comuns: {val(winner['f1_spam'])}. Entretanto, o complemento de 775 favoreceu {candidate['name']}: {val(candidate['full_test_775']['f1_spam'])}. Portanto não declaramos um vencedor estático estável. Se precisarmos priorizar um para desenvolver agora, recomendamos provisoriamente Word2Vec CBOW, pela evidência no conjunto maior, mantendo GloVe como concorrente e fastText para investigar palavras raras/subpalavras. Não comparamos o F1 de 775 a LLMs avaliados em 200 como se fossem o mesmo teste. O conjunto maior contém os 200 comuns: não é uma replicação independente. A escolha orientada por esses testes é exploratória e precisará de validação independente.

Não encerrar a decisão com SMS em inglês: falta testar o alinhamento português-inglês exigido pelo projeto de anime. GloVe/Word2Vec monolíngues não colocam automaticamente português e inglês no mesmo espaço. Poderá ser necessário alinhamento, tradução controlada ou embeddings estáticos multilíngues, com custo e efeitos medidos.

O fastText não deve ser descartado por um único resultado menor: o corpus, uma época de treinamento e a representação por média influenciam a qualidade. Ele resolve vetorização de OOV, mas isso não garante compreensão semântica perfeita de termos raros. CBOW/Skip-gram são comparadores válidos e o CBOW liderou o complemento de 775 entre os estáticos. Lee deve permanecer diagnóstico: o corpus minúsculo não representa treinamento competitivo. Dimensões, corpora e orçamentos de treinamento diferem entre estáticos; estes resultados não isolam o efeito causal do algoritmo.

TF-IDF é barato e forte para esta tarefa lexical. Não o apresentar como um modelo estático neural; manter como baseline para evitar atribuir ao embedding um benefício que um método simples já oferece. MiniLM é contextual e gera embeddings de sentenças; se for melhor, isso deve ser registrado, ainda que a restrição do TCC mantenha o foco estático.

A ordem entre esses dois também depende do subconjunto: nos 200 comuns, MiniLM liderou; no complemento de 775, TF-IDF teve F1 {val(by['tfidf']['full_test_775']['f1_spam'])} e MiniLM {val(by['minilm']['full_test_775']['f1_spam'])}. O complemento contém os 200 comuns, portanto não é uma replicação independente. Não transformar o melhor valor de uma amostra pequena em uma vitória universal.

Os LLMs locais operam gratuitamente nesta máquina, mas os modelos pequenos quantizados não representam todas as capacidades das famílias GPT/Llama/DeepSeek. Seu custo de resposta e eventuais falhas de formato/orçamento afetam esta tarefa simples. Não recomendamos torná-los o motor principal do TCC definido pelo usuário: são comparadores e possíveis ferramentas auxiliares. Uma nova rodada com outra supervisão, orçamento ou prompt precisa usar validação, ser identificada separadamente e manter estes resultados originais.

GPT-OSS foi incluído gratuitamente pelo provedor escolhido, sem carregar pesos 20B na máquina. Isso permite comparar um gerador maior com menos exigência local, mas introduz cota, dependência de rede e hardware desconhecido. Ele não demonstra o desempenho de GPT proprietário nem garante gratuidade futura de qualquer API. Não comparar consumo de RAM local do cliente com RAM do serviço remoto.

Para a iniciação científica, a conclusão defensável é quais pipelines funcionaram melhor sob as condições registradas, quanto custaram em tempo/recursos e quais limitações foram observadas. Uma afirmação universal como 'estáticos são melhores que LLMs' não decorre deste teste.''')
add('8. Erros, dificuldades e o que preservamos', (BASE/'DIARIO_BENCHMARK.md').read_text(encoding='utf-8'))
explanations={
 'dummy':'Serve somente de referência do desbalanceamento; não identifica nenhum spam.',
 'tfidf':'É uma referência lexical simples. Seu resultado ajuda a verificar se a complexidade dos demais pipelines trouxe ganho nesta tarefa.',
 'glove':'Manter como concorrente estático: vetores compactos, inferência barata e melhor F1 pontual entre os estáticos nos 200 comuns. O CBOW liderou o complemento maior; não declarar superioridade estável. Ainda falta avaliar português-inglês e relevância de anime.',
 'fasttext':'Manter como concorrente por sua composição de subpalavras. O resultado atual depende de fil9, uma época e média IDF; não generalizar para qualquer fastText. O tempo inclui pipes por palavra.',
 'w2v-cbow':'Candidato provisório para priorizar desenvolvimento estático: liderou os estáticos no complemento de 775, apesar de ficar atrás de GloVe nos 200 comuns. A troca de ordem e a tarefa inglesa impedem decisão definitiva para anime. Corpus e treinamento distintos impedem atribuir tudo ao algoritmo.',
 'w2v-sg':'Manter para comparação de arquitetura/custo. Não descartar Skip-gram em geral por esta configuração; uma rodada futura de ajuste deve usar validação.',
 'minilm':'Embedding contextual de sentenças, útil como referência de qualidade. Não é elegível como estático no recorte final estabelecido pelo usuário; isso é uma restrição de escopo, não uma refutação de sua qualidade.',
 'w2v-lee-cbow':'Controle diagnóstico com vocabulário/corpus muito pequenos. Não recomendar para produção nem usar seu fracasso como prova contra Word2Vec em geral.',
 'w2v-lee-sg':'Controle diagnóstico, não candidato equivalente ao modelo treinado em text8.',
 'llama':'A versão 1B quantizada funciona localmente, mas a qualidade observada e o tempo devem orientar o uso. Não representa os Llamas grandes. Não escolher como motor do TCC que foi definido para estáticos.',
 'deepseek':'Modelo destilado 1,5B, não o DeepSeek completo. Raciocínio e limite de 512 tokens são parte da configuração e podem provocar custo/saída incompleta. Qualidade sob esse limite não é qualidade máxima da família.',
 'qwen':'Alternativa gratuita pequena local, com Q8 e raciocínio. Não é GPT nem modelo estático. Ler erros de formato/orçamento junto ao F1 antes de recomendar uso auxiliar.',
 'gptoss':'Modelo maior servido pela Groq; não instalado nesta máquina e não GPT proprietário. Próximo de um estático em um teste não comprova equivalência. Hardware remoto/cotas/rede limitam a comparação de recursos.'}
details=[]
for x in models:
    c=x['confusion'];details.append(f"{x['name']}: F1 spam {val(x['f1_spam'])}; precisão {val(x['precision_spam'])}; recall {val(x['recall_spam'])}; acurácia {percent(x['accuracy'])}. Detectou {c[1][1]}/25 spams e acusou {c[0][1]} mensagens legítimas como spam. Respostas inválidas: {x['invalid']}; encerramentos por limite de tokens: {x.get('length_finishes','não se aplica')}. Tempo médio {x['mean_ms']:.3f} ms, mediana {x['median_ms']:.3f} ms, p95 {x['p95_ms']:.3f} ms. "+explanations[x['model']])
sections.insert(7,('7a. Evidência e decisão para cada pipeline','\n\n'.join(details)))
add('9. Como reproduzir e entender o código', '''Os códigos estão em laboratorio/llms-20261105/codigo. Primeiro 02-preparar-dataset.py adquire/processa o dataset; depois os hashes congelados protegem as divisões. Não executar novamente a aquisição para modificar silenciosamente esta avaliação. 07-benchmark-classicos.py carrega pesos existentes, ajusta IDF e regressão apenas com treino e salva decisões/tempos. 08-rodar-classicos.sh executa os nove workers em série. 09-benchmark-geradores.py inicia o llama-server ou faz chamada HTTP à Groq, grava cada requisição em JSONL e conserva respostas brutas. 11-rodar-geradores-locais.sh ordena os três modelos. 12-avaliar-comparacao.py agrega, valida e calcula intervalos. Este script 13 apenas apresenta os resultados e não muda predições.

Uma leitura didática: carregar um modelo significa trazer os pesos do disco para memória; encode transforma texto em vetor; fit aprende a cabeça logística com exemplos conhecidos; predict_proba calcula a chance estimada de spam; comparar com 0,5 gera o rótulo. Em geradores, chamar chat/completions envia um prompt e recebe texto. O parser transforma a resposta em ham/spam/inválida. Métricas comparam essas decisões aos rótulos guardados, nunca fornecidos no prompt de teste.

Exemplo MiniLM: SentenceTransformer(caminho_local).encode(['No pic. Please re-send.'], normalize_embeddings=True) produz um vetor de 384 números. Sem uma cabeça treinada isso não é uma classificação de spam. Exemplo Word2Vec: KeyedVectors.load ou Word2Vec.load recupera os vetores e model.wv['message'] acessa uma palavra; a função de média/IDF constrói o vetor do SMS. GloVe usa o arquivo texto com palavra e coordenadas; fastText print-word-vectors recebe palavras pelo stdin e devolve coordenadas, inclusive para OOV. Os exemplos executáveis anteriores permanecem no manual de instalação e EXEMPLOS_COMENTADOS.md.

Exemplo API local: iniciar 04-iniciar-servidor.ps1 com o modelo desejado e executar 05-consultar-api-local.py ou .ps1. O endpoint fica restrito a 127.0.0.1. O servidor precisa estar ativo para gerar respostas. Não é necessário manter modelos carregados quando não usados. Para Groq, a credencial fica fora do projeto e é lida localmente; nunca copiar para relatório, notebook, comando ou repositório. As requisições registram parâmetros/modelo/tempo, sem Authorization.

Para repetir exatamente, preservar ambientes, hashes, modelos, prompt e dados; usar os scripts originais e uma NOVA pasta de rodada antes de sobrescrever qualquer evidência. Os scripts atuais podem pular saídas concluídas e retomar JSONL; uma retomada pode ter tempos de etapa diferentes e deve ser identificada. Reexecutar o avaliador ou o relatório não faz novas chamadas de API e não treina novamente.''')
add('10. Fontes e documentação oficial', '''Dataset Kaggle: https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset
Origem UCI e licença: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
GloVe: https://nlp.stanford.edu/projects/glove/ e https://github.com/stanfordnlp/GloVe
fastText vetores: https://fasttext.cc/docs/en/unsupervised-tutorial.html
Word2Vec original: https://arxiv.org/abs/1301.3781 ; implementação Gensim: https://radimrehurek.com/gensim/models/word2vec.html
MiniLM (Microsoft Research): https://arxiv.org/abs/2002.10957 ; modelo concreto: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Sentence Transformers: https://www.sbert.net/
Meta Llama 3.2: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct ; GGUF comunitário: https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF
DeepSeek: https://github.com/deepseek-ai/DeepSeek-R1 ; GGUF: https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF
Qwen: https://huggingface.co/Qwen/Qwen3-0.6B e https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
llama.cpp: https://github.com/ggml-org/llama.cpp/releases/tag/b12110
GPT-OSS: https://openai.com/open-models/ ; Groq: https://console.groq.com/docs/model/openai/gpt-oss-20b
Groq configuração e limites: https://console.groq.com/docs/quickstart e https://console.groq.com/docs/rate-limits
Parâmetros scikit-learn: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html

As fontes originais descrevem modelos e bibliotecas; os resultados numéricos deste documento vêm da execução local/remota registrada, não dos benchmarks dos fabricantes. Nenhum treinamento novo dos grandes modelos foi realizado. Mais documentos/cards e licenças estão na pasta fontes e no manual histórico de instalação.''')

# Tabelas em Markdown e HTML acessíveis, com unidades explícitas.
quality_headers=['Pipeline','F1 spam','IC 95%','Precisão','Recall','Acurácia','Inválidas']
quality=[[x['name'],val(x['f1_spam']),f"{x['f1_ci95'][0]:.3f}-{x['f1_ci95'][1]:.3f}",val(x['precision_spam']),val(x['recall_spam']),percent(x['accuracy']),str(x['invalid'])] for x in models]
time_headers=['Pipeline','Média ms','Mediana ms','p95 ms','Soma respostas s','RSS MiB']
timings=[[x['name'],f"{x['mean_ms']:.3f}",f"{x['median_ms']:.3f}",f"{x['p95_ms']:.3f}",f"{x['sum_response_seconds']:.2f}",f"{x['peak_rss_mib']:.1f}" if x['peak_rss_mib'] else 'desconhecido'] for x in models]
conf_headers=['Pipeline','ham→ham','ham→spam','ham→inv.','spam→ham','spam→spam','spam→inv.']
confusions=[[x['name']]+[str(v) for row in x['confusion'] for v in row] for x in models]
full_headers=['Pipeline','N','F1 spam','Precisão','Recall','Acurácia']
full=[[x['name'],'775',val(x['full_test_775']['f1_spam']),val(x['full_test_775']['precision_spam']),val(x['full_test_775']['recall_spam']),percent(x['full_test_775']['accuracy'])] for x in models if 'full_test_775' in x]
setup_headers=['Pipeline','Preparo s','Encode treino s','Ajuste LR s','Etapa gerador s']
setup=[[x['name'],f"{x['metadata']['load_seconds']:.2f}" if x['metadata'].get('load_seconds') is not None else '-',f"{x['metadata']['encode_train_seconds']:.2f}" if 'encode_train_seconds' in x['metadata'] else '-',f"{x['metadata']['classifier_fit_seconds']:.3f}" if 'classifier_fit_seconds' in x['metadata'] else '-',f"{x['metadata']['total_stage_wall_seconds']:.2f}" if x['metadata'].get('total_stage_wall_seconds') is not None else '-'] for x in models]
def mdtable(headers,body):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(row)+' |' for row in body])
paired_headers=['Diferença F1','Limite inferior 95%','Limite superior 95%']
paired=[[f"GloVe menos {by[x['second']]['name']}",f"{x['delta_ci95'][0]:.3f}",f"{x['delta_ci95'][1]:.3f}"] for x in data['paired_glove']]
tables=[('Resultados principais - 200 mensagens',quality_headers,quality),('Resposta completa por SMS - tempos em milissegundos',time_headers,timings),('Matriz de confusão - contagens',conf_headers,confusions),('Preparação e etapa - segundos',setup_headers,setup),('Intervalos exploratórios de diferenças pareadas',paired_headers,paired),('Complemento - 775 mensagens (não comparar com LLMs nesta tabela)',full_headers,full)]
recovered=[x for x in models if 'first_attempt_quality_sensitivity' in x]
if recovered:
    tables.append(('Sensibilidade à interrupção operacional',['Pipeline','F1 após recuperação','F1 com timeout inválido','Inválidas conservadoras'],[[x['name'],val(x['f1_spam']),val(x['first_attempt_quality_sensitivity']['f1_spam']),str(x['first_attempt_quality_sensitivity']['invalid'])] for x in recovered]))
extra_path=BASE/'resultados/comparacao/cenarios-sms.json'
if extra_path.exists():
    extra=json.loads(extra_path.read_text(encoding='utf-8'));ex={m['model']:m for m in extra['models']}
    assert set(by)==set(ex),'Recalcular cenários para corresponder aos modelos concluídos.'
    costs=[[m['name']]+[str(ex[m['model']]['costs'][k]['total_units']) for k in ['equal','protect_legitimate_messages','prioritize_spam_detection']] for m in models]
    tables.append(('Cenários exploratórios - menor custo é melhor',['Pipeline','FP=FN=1','FP=5, FN=1','FP=1, FN=5'],costs))
    cohorts=[]
    for m in models:
        for c in ex[m['model']]['cohorts']:cohorts.append([m['name'],c['cohort'],str(c['n']),str(c['spam']),val(c['f1_spam']),val(c['recall_spam'])])
    tables.append(('Análise exploratória por comprimento',['Pipeline','Faixa','N','Spam','F1 spam','Recall spam'],cohorts))
    probabilities=[[m['name'],val(m['roc_auc']),val(m['average_precision']),val(ex[m['model']]['brier_score'])] for m in models if 'roc_auc' in m]
    tables.append(('Scores probabilísticos - somente classificadores',['Pipeline','ROC-AUC ↑','AP ↑','Brier ↓'],probabilities))
    sections.append(('11. Cenários adicionais e métricas probabilísticas','''Estas análises são pós-hoc: foram acrescentadas por utilidade operacional depois de observar o comparativo inicial. Não houve ajuste de limiar ou nova predição. Cenário de custo igual: FP+FN+inválidas. Proteção de mensagens legítimas: 5*FP+FN+5*inválidas. Prioridade a detectar spam: FP+5*FN+5*inválidas. São unidades hipotéticas; não dinheiro nem custo medido com usuários. A inválida recebe conservadoramente o maior custo de erro. Isso permite discutir prioridades sem inventar uma probabilidade para os LLMs. Não selecionamos o vencedor apenas por um custo escolhido depois do teste.

Dividimos as mensagens por comprimento original: 1-80, 81-160 e acima de 160 caracteres. Cada faixa mostra N e quantidade de spam, porque prevalências e tamanhos diferentes afetam o F1. O resultado de uma faixa pequena não sustenta conclusão geral nem equivale a repetir o experimento. Esta análise identifica fragilidades a investigar com mais dados.

ROC-AUC é a probabilidade de um spam receber score maior que um ham escolhido aleatoriamente (empates contam meio), agregando todos os pares. Mede ordenação dos scores, não acerto no limiar 0,5; pode parecer favorável mesmo com problemas na classe rara. Average precision (AP) soma os valores de precisão ponderados pelo incremento de recall à medida que descemos o limiar. É útil para avaliar a recuperação de positivos raros sem fixar limiar. AP não é a área trapezoidal sob PR. Em ambas, maior é melhor.

Brier é a média de (probabilidade_spam - rótulo_0_ou_1)^2; menor é melhor. Penaliza erros probabilísticos confiantes e reflete discriminação e calibração, não apenas calibração. A regressão usa class_weight=balanced, portanto suas probabilidades não devem ser tratadas automaticamente como frequências reais calibradas. Scores de similaridade de uma busca de anime também não são probabilidades de gostar. Não calculamos essas métricas probabilísticas para LLMs que devolveram somente rótulos.'''))
sections.append(('Escopo final confirmado pelo usuário','''O programa final seguirá recuperação da informação com embeddings estáticos pré-treinados, indexação, similaridade e combinação determinística de pesos. Lucas confirmou que os vetores aprendidos previamente podem ser usados, mas não haverá treinamento ou ajuste de modelos no programa. Não usar a regressão logística deste benchmark de SMS no recomendador final. MiniLM, LLMs e classificadores ficam como comparadores experimentais.

O produto tem duas modalidades: recomendação a partir de um anime sem perfil e recomendação a partir do mesmo anime com pesos explícitos de preferência/histórico. Assistir não significa gostar. O teste de SMS é uma verificação comparativa de pipelines de classificação; não seleciona sozinho o modelo de recuperação nem valida personalização. Mesmo o diagnóstico de consultas por gêneros em anime precisará ser complementado por avaliação anime-para-anime e de perfis. A origem aprendida dos embeddings deve ser descrita corretamente no TCC, sem afirmar que eles nunca envolveram aprendizado de máquina.'''))
glossary=BASE.parent/'anime-en-20261105/METRICAS_EXPLICADAS.md'
if glossary.exists():sections.append(('12. Guia detalhado de métricas e interpretação',glossary.read_text(encoding='utf-8')))
md='# Comparação documentada de modelos - SMS Spam Collection\n\n'+status+'\n\nExecução de 05/11/2026. Documento gerado de evidências preservadas.\n\n'
for title,h,body in tables:md+='## '+title+'\n\n'+mdtable(h,body)+'\n\n'
md+=f'![F1 e intervalos](qualidade-f1-{suffix}.png)\n\n![Tempo até resposta completa](tempo-resposta-{suffix}.png)\n\n'
for title,body in sections:md+='## '+title+'\n\n'+body+'\n\n'
md+='## Anexo de códigos completos\n\nOs códigos executados seguem abaixo para permitir leitura e revisão; os arquivos .py/.sh originais estão na pasta codigo.\n\n'
codefiles=[BASE/'codigo'/x for x in ['benchmark_suporte.py','07-benchmark-classicos.py','08-rodar-classicos.sh','09-benchmark-geradores.py','11-rodar-geradores-locais.sh','12-avaliar-comparacao.py','15-cenarios-sms.py']]
for f in codefiles:md+='### '+f.name+'\n\n```'+('bash' if f.suffix=='.sh' else 'python')+'\n'+f.read_text(encoding='utf-8')+'\n```\n\n'
(OUT/f'relatorio-{suffix}-sms.md').write_text(md,encoding='utf-8')
ht='<html lang="pt-BR"><meta charset="utf-8"><title>Comparação SMS</title><style>body{font:17px/1.6 system-ui;max-width:1150px;margin:40px auto;padding:20px;color:#182238}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:8px;border-bottom:1px solid #ccd}th{background:#e8eff9;text-align:left}img{max-width:100%}pre{overflow:auto;background:#f1f4f8;padding:16px;font-size:12px}h1,h2{color:#204b77}</style><h1>Comparação documentada de modelos</h1><p>SMS Spam Collection | 05/11/2026 | 200 mensagens comuns</p>'
for title,h,body in tables:ht+='<h2>'+html.escape(title)+'</h2><table><tr>'+''.join('<th>'+html.escape(v)+'</th>' for v in h)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in body)+'</table>'
ht+=f'<p><strong>{html.escape(status)}</strong></p><img src="qualidade-f1-{suffix}.png"><img src="tempo-resposta-{suffix}.png">'
for title,body in sections:ht+='<h2>'+html.escape(title)+'</h2>'+''.join('<p>'+html.escape(p).replace('\n','<br>')+'</p>' for p in body.split('\n\n'))
for f in codefiles:ht+='<h2>'+html.escape(f.name)+'</h2><pre>'+html.escape(f.read_text(encoding='utf-8'))+'</pre>'
(OUT/f'relatorio-{suffix}-sms.html').write_text(ht+'</html>',encoding='utf-8')

# PDF: fonte Unicode, tabelas com quebra de texto, paginação e anexo de código.
for name,file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf'),('Mono','consola.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
styles=getSampleStyleSheet();styles['Normal'].fontName='Arial';styles['Normal'].fontSize=10;styles['Normal'].leading=14
styles['Title'].fontName='Arial-Bold';styles['Heading1'].fontName='Arial-Bold';styles['Heading1'].fontSize=16;styles['Heading1'].leading=20
styles.add(ParagraphStyle(name='SmallCell',fontName='Arial',fontSize=7.5,leading=10))
styles.add(ParagraphStyle(name='CodeSmall',fontName='Mono',fontSize=6.7,leading=8.2))
story=[]
def para(s,style='Normal'):return Paragraph(html.escape(s).replace('\n','<br/>'),styles[style])
story.extend([para('Comparação de modelos','Title'),Spacer(1,16),para('SMS Spam Collection | Execução de 05/11/2026'),Spacer(1,12),para('Evidências, parâmetros, métricas, tempos, limitações e código comentado para o TCC.'),Spacer(1,18)])
story.extend([para(status),Spacer(1,12)])
story.append(para('Como ler: comece pelas tabelas; as seções seguintes explicam os conceitos, o que foi medido e os limites da conclusão. O manual histórico de instalação continua separado. Este documento registra o novo benchmark.'))
for title,h,body in tables:
    story.append(PageBreak());story.append(para(title,'Heading1'));story.append(Spacer(1,10))
    widths=[160]+[(507-160)/(len(h)-1)]*(len(h)-1)
    table=Table([[para(v,'SmallCell') for v in row] for row in [h]+body],colWidths=widths,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1eaf5')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7fa')]),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7)]));story.append(table)
    if h==time_headers:story.extend([Spacer(1,12),para('RSS remoto desconhecido; RSS local é pico de processo. Tempos de resposta excluem pausas preventivas da Groq. Nenhum valor desta tabela é TTFT.')])
for image in [f'qualidade-f1-{suffix}.png',f'tempo-resposta-{suffix}.png']:story.extend([PageBreak(),Image(str(OUT/image),width=507,height=380)])
for title,body in sections:
    story.extend([PageBreak(),para(title,'Heading1'),Spacer(1,12)])
    for p in body.split('\n\n'):story.extend([para(p),Spacer(1,9)])
story.extend([PageBreak(),para('Anexo - códigos executados','Heading1'),para('Texto completo para revisão. Cada arquivo original permanece disponível na pasta codigo. As linhas longas são quebradas visualmente apenas neste PDF.')])
for f in codefiles:
    story.extend([PageBreak(),para(f.name,'Heading1'),Spacer(1,10)])
    for line in f.read_text(encoding='utf-8').expandtabs(4).splitlines():
        wrapped=textwrap.wrap(line,width=114,replace_whitespace=False,drop_whitespace=False) or [' ']
        for part in wrapped:story.append(Preformatted(part,styles['CodeSmall']))
def footer(canvas,doc):
    canvas.setFont('Arial',8);canvas.setFillColor(colors.HexColor('#64748b'));canvas.drawString(44,24,'TCC | Benchmark SMS | Resultados condicionais ao protocolo');canvas.drawRightString(552,24,str(doc.page))
pdf=OUT/f'relatorio-{suffix}-sms.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),rightMargin=44,leftMargin=44,topMargin=44,bottomMargin=44,title='Comparação documentada de modelos - SMS',author='Laboratório TCC').build(story,onFirstPage=footer,onLaterPages=footer)
print(pdf)
