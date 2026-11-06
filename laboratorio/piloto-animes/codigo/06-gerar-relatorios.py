"""Gera relatório, gráfico, painel offline e PDF a partir dos resultados preservados.

Executar com Python que contenha matplotlib e reportlab. Não executa modelos,
não altera dados nem julgamentos e não depende de conexão à internet.
"""
import base64
import csv
import html
import json
import pathlib
import re
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'relatorios'
OUT.mkdir(exist_ok=True)
R = json.loads((ROOT/'resultados/resumo.json').read_text(encoding='utf-8'))
Q = json.loads((ROOT/'dados/consultas.json').read_text(encoding='utf-8'))
C = json.loads((ROOT/'dados/catalogo.json').read_text(encoding='utf-8'))
K = json.loads((ROOT/'resultados/rankings.json').read_text(encoding='utf-8'))
MODELS = R['main_models']
N = R['names']
SCENARIOS = {'PT_EN':'Português → inglês (principal)', 'EN_EN':'Inglês → inglês', 'PT_PT':'Português → português'}

def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |'] + ['| '+' | '.join(map(str,r))+' |' for r in rows])

rows = []
for m in MODELS:
    s = R['summary'][m]['PT_EN']
    rows.append([N[m], f"{s['ndcg5']:.3f}", f"{s['hit1']*100:.1f}%", f"{s['mrr10']:.3f}", f"{s['recall5']*100:.1f}%", f"[{s['ndcg5_ci95'][0]:.3f}; {s['ndcg5_ci95'][1]:.3f}]"])
primary = table(['Pipeline','nDCG@5','Hit@1','MRR@10','Recall@5','IC exploratório nDCG'],rows)
alllangs = table(['Pipeline','PT → EN','EN → EN','PT → PT'], [[N[m]]+[f"{R['summary'][m][s]['ndcg5']:.3f}" for s in SCENARIOS] for m in MODELS])
resources = table(['Pipeline','Pico RSS (MiB)','Carregamento (s)','Cache de textos/termos (s)'], [[N[m],f"{R['metadata'][m]['max_rss_kib']/1024:.1f}",f"{R['metadata'][m]['load_seconds']:.2f}",f"{R['metadata'][m]['lexical_or_text_cache_seconds']:.3f}"] for m in MODELS])

with (ROOT/'resultados/metricas-agregadas.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['model','scenario','ndcg5','hit1','mrr10','recall5','ci95_low','ci95_high'])
    for m in MODELS:
        for s in SCENARIOS:
            v=R['summary'][m][s];w.writerow([m,s,v['ndcg5'],v['hit1'],v['mrr10'],v['recall5'],*v['ndcg5_ci95']])

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,3,figsize=(15,5),sharex=True)
for ax,(s,label) in zip(axs,SCENARIOS.items()):
    for i,m in enumerate(MODELS):
        v=R['summary'][m][s]; value=v['ndcg5'];lo,hi=v['ndcg5_ci95']
        ax.barh(i,value,color='#0072B2' if m=='minilm' else '#8497A5',height=.63)
        ax.errorbar(value,i,xerr=[[value-lo],[hi-value]],fmt='none',ecolor='#222222',capsize=3)
        ax.text(min(hi+.02,.93),i,f'{value:.3f}',va='center',fontsize=9)
    ax.set(yticks=range(len(MODELS)),yticklabels=[N[m] for m in MODELS] if s=='PT_EN' else [],xlim=(0,1),xlabel='nDCG@5 (maior é melhor)',title=label)
    ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.suptitle('Piloto de busca de animes: 39 itens, 58 consultas, 29 intenções',fontsize=15,fontweight='bold')
fig.text(.5,.015,'Textos e julgamentos preparados com IA, sem validação humana independente. IC95%: bootstrap por intenção (5.000).',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.05,1,.93));fig.savefig(OUT/'comparacao-idiomas.png',dpi=170);fig.savefig(OUT/'comparacao-idiomas.svg');plt.close(fig)

errors=[]
for i,q in enumerate(Q):
    rank=K['minilm']['PT_EN'][i]
    if rank[0]['grade']!=2:
        strong=[x['title'] for x in rank if x['grade']==2]
        pos=next(j+1 for j,x in enumerate(rank) if x['grade']==2)
        errors.append((q,rank[0],strong,pos))
error_text='\n\n'.join(f"- **{q['id']}** — {q['text_pt']}\n  Primeiro resultado: **{top['title']}**, grau {top['grade']}. Alvo(s) forte(s): {', '.join(strong)}; primeiro grau 2 na posição {pos}." for q,top,strong,pos in errors)
examples=[]
for idx in [1,7,19]:
    q=Q[idx]
    examples.append('### '+q['id']+'\n\n'+q['text_pt']+'\n\n'+table(['Pipeline','Primeiro resultado','Grau'],[[N[m],K[m]['PT_EN'][idx][0]['title'],K[m]['PT_EN'][idx][0]['grade']] for m in MODELS])+'\n\nScores empatados podem tornar o primeiro item exibido arbitrário; as métricas usam a expectativa do empate.')

report=f'''# AniRec: comparação piloto e escolha provisória para o TCC

29/10/2026 • Lucas • cenário prioritário confirmado: consultas em português e descrições em inglês.

## 1. Decisão que os dados permitem tomar

Recomendo **paraphrase-multilingual-MiniLM-L12-v2 como encoder principal do protótipo do TCC**. Neste catálogo e nestas consultas, teve nDCG@5 de **0,805**, Hit@1 de **47/58 = 81,0%**, MRR@10 de 0,878 e Recall@5 de 72,7%. Opera localmente em CPU, já foi carregado com os arquivos locais e dispensa treinar um modelo de linguagem para iniciar o sistema.

Essa é uma decisão de engenharia apoiada por um piloto controlado. Não demonstra que MiniLM seja universalmente melhor, nem que a arquitetura dos modelos estáticos seja incapaz de servir ao projeto. Escolhemos o melhor dos pipelines disponíveis para o requisito PT → EN. O uso de descrições e julgamentos preparados com IA exige confirmação humana antes de uma conclusão científica.

## 2. O que já está funcional

- GloVe oficial compilado e treinado no demo text8: 50 dimensões, 71.290 palavras. Analogia oficial: 23,50% nas questões cobertas, com 91,21% de cobertura. Esse teste verifica aprendizado lexical; não mede recomendação de animes.
- fastText oficial v0.9.2 compilado com G++ 12 e treinado em fil9/enwik9: Skip-gram, 100 dimensões, 218.316 entradas, uma época. O tutorial de classificação cooking também foi executado, mas seu classificador não participa desta busca.
- Rare Words do fastText resolvido: avaliador oficial aplicado a 2.034 pares, zero pares descartados, Spearman rho = **0,4177019**. A origem Stanford estava inacessível; usamos cópia histórica AWS e corroboramos todos os pares/notas com cópia acadêmica. Não há checksum publicado da origem para afirmar identidade binária. Detalhes em `../../docs/07-rare-words-resolucao.md`, e no registro de fontes do laboratório.
- Word2Vec Gensim 4.4: CBOW e Skip-gram nos exemplos Lee, mais novos treinos em text8 para este piloto. Text8: 100 dimensões, cinco épocas, janela 5, min_count 5, quatro workers, seed 20261029, 71.290 palavras. Lee é apenas demonstração e não decide a exclusão do Word2Vec.
- Sentence Transformers MiniLM multilíngue: pesos salvos localmente, 384 dimensões, inferência CPU e carregamento offline verificados. Revisão fixada: e8f8c211226b894fcb81acc59f3b34ba3efd5f42.
- TF-IDF é a referência lexical adicional; não necessita pesos pré-treinados.

Nenhum GPT, Llama ou DeepSeek gerador foi instalado ou comparado. O MiniLM usado é um encoder de embeddings, não um chatbot gerador. “Funcional” significa que os testes documentados passaram; não significa que um produto final de recomendação esteja pronto ou validado.

## 3. Base: o que veio de uma fonte e o que foi criado

Selecionamos **39 animes reais**, identificados no Anime Offline Database, release 2026-27, metadados de 04/07/2026. O download do JSON completo ficou em C:/tcc-lab/Pilot, com 62.331.136 bytes; o subconjunto de metadados está preservado em `dados/brutos/aod-subconjunto.json`. A consulta à API Jikan não forneceu a base deste experimento.

**As descrições bilingues são textos curtos originais preparados com IA, não sinopses oficiais obtidas dessa base.** Consultas e relevâncias também foram preparadas com assistência de IA, sem anotadores humanos independentes. O catálogo foi escolhido por conveniência e diversidade temática. Isso facilita demonstrar o mecanismo, mas cria viés de autoria, vocabulário e cobertura intencional de enredos. Não apresentar estes textos como um benchmark público validado.

São 58 consultas, duas versões por 29 intenções: uma direta e uma paráfrase. As traduções PT/EN compartilham o mesmo julgamento. Os **2.262 pares** consulta/anime têm grau 2 (fortemente pertinente), 1 (parcialmente pertinente) ou 0 (não selecionado como pertinente). Grau 0 reflete o julgamento operacional do piloto, não uma verdade universal sobre a obra.

O protocolo, os textos e os julgamentos foram congelados antes de observar rankings. Hashes estão em `dados/freeze.json`. Títulos, IDs, gêneros e notas públicas não entram nos vetores. Nenhum modelo foi treinado com os julgamentos de anime; nenhum hiperparâmetro foi escolhido depois dos resultados. Para o TCC, substituir/complementar estas descrições por sinopses reais com fonte e condições de uso registradas.

Fonte: [Anime Offline Database](https://github.com/manami-project/anime-offline-database). Preservar atribuição e as licenças ODbL 1.0 / DbCL 1.0 dos metadados derivados; cópia da licença em dados/brutos.

## 4. Como cada busca funciona

TF-IDF: tokenização Unicode, unigramas/bigramas, frequência sublinear e IDF aprendido somente nas descrições do catálogo de cada cenário. Não utiliza tradução.

GloVe, fastText e Word2Vec: tokenização NFKC/casefold e letras Unicode; média dos vetores das palavras ponderada pelo IDF do catálogo, seguida de normalização L2. Palavras ausentes são descartadas em GloVe/Word2Vec. O fastText usa o executável oficial e subpalavras para gerar vetores também fora do vocabulário.

MiniLM: encode do texto completo com o tokenizer próprio, normalização L2 e similaridade por produto escalar, equivalente ao cosseno para vetores unitários. Não aplica a tokenização lexical comum antes do encoder. O maior texto teve **60 tokens**, abaixo do limite de 128; **nenhuma entrada foi truncada**. Sinopses reais longas exigirão definir e avaliar segmentação/agregação; este piloto não testa isso.

Todos ranqueiam os mesmos 39 candidatos. A documentação oficial do Sentence Transformers descreve embeddings e similaridade; a escolha do catálogo, média IDF e protocolo de comparação é nossa implementação experimental, não um benchmark oficial dos fabricantes.

Fontes: [similaridade no Sentence Transformers](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html), [cartão do modelo MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2), [tutorial fastText](https://fasttext.cc/docs/en/unsupervised-tutorial.html), [GloVe oficial](https://github.com/stanfordnlp/GloVe), [Word2Vec Gensim](https://radimrehurek.com/gensim/models/word2vec.html), [TF-IDF sklearn](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).

## 5. Métricas e confiabilidade do cálculo

**nDCG@5** é a métrica principal: avalia ordem e graus de relevância dos cinco primeiros, com ganho 2^grau - 1, normalizado pelo ranking ideal. Varia de 0 a 1. **0,805 não significa 80,5% de acurácia**.

Hit@1 conta consultas cujo primeiro item é grau 2. MRR@10 considera o inverso da posição do primeiro grau 2 nos dez primeiros. Recall@5 conta a proporção dos itens grau 1 ou 2 recuperados entre os cinco primeiros; seu denominador pode ser maior que cinco.

Empates usam o valor esperado sob permutações uniformes, inclusive quando não há vetor. Assim, IDs não produzem acertos artificiais. O painel exibe uma ordem fixa por ID nos empates; ela não deve ser confundida com evidência de preferência do modelo. Scores de diferentes modelos não são probabilidades nem são diretamente comparáveis.

A implementação de nDCG foi conferida em **1.392 casos** contra sklearn, diferença máxima 3,33e-16; um exemplo pequeno de empate foi verificado separadamente. Os intervalos de 95% usam 5.000 reamostragens bootstrap por **29 famílias de intenção**, mantendo as duas formulações juntas. Não consideramos 174 consultas independentes ao juntar idiomas. Os intervalos quantificam variação nesta amostra, não corrigem viés de autoria ou ausência de anotadores humanos.

## 6. Resultado principal: português → inglês

{primary}

MiniLM supera fastText, o segundo maior nDCG neste cenário, por 0,658; intervalo bootstrap pareado exploratório [0,562; 0,748]. Essa diferença é consistente dentro do piloto. Não apresentamos isso como prova de superioridade universal ou estudo causal de arquitetura.

Separação por formulação: MiniLM teve nDCG 0,904 e Hit@1 29/29 nas consultas diretas; nas paráfrases, nDCG 0,707 e Hit@1 **18/29**. Portanto, a média total esconde erros importantes quando o usuário se afasta das palavras mais diretas do enredo.

## 7. Idioma muda a interpretação

Valores abaixo são nDCG@5; os três cenários reutilizam intenções e julgamentos.

{alllangs}

Em inglês, Word2Vec Skip-gram text8 alcança 0,739 e fastText 0,723; TF-IDF chega a 0,680 e GloVe a 0,606. Isso mostra que os pipelines estáticos estão produzindo informação útil no idioma em que foram treinados. Sua queda em PT → EN não permite concluir que o algoritmo é ruim: falta um espaço semanticamente alinhado entre os idiomas nessa configuração.

O fastText gera vetor utilizável para **100%** dos tokens portugueses destas consultas, mas apenas 53,3% pertencem ao vocabulário treinado; GloVe/Word2Vec cobrem 45,1%. Cobertura mede disponibilidade lexical, não entendimento ou tradução. Subpalavras ajudam com formas desconhecidas, mas não criam por si sós alinhamento português/inglês. Para TF-IDF EN, apenas 3,5% dos tokens das consultas PT pertencem ao vocabulário do catálogo.

## 8. Por que continuar com MiniLM e não priorizar os outros no TCC

### MiniLM multilíngue: escolha principal

O requisito decisivo é atravessar português e inglês sem exigir que o usuário traduza a consulta. O modelo representa frases completas e foi disponibilizado para similaridade/busca semântica multilíngue. A evidência deste piloto favorece a configuração já instalada, sem treino adicional. Arquitetura proposta: descrição inglesa → embedding persistido; consulta portuguesa → embedding; cosseno → top-k de animes. É uma base adequada para construir o protótipo e avaliar o fluxo de recuperação.

Custos e limitações: mais dependências e custo de codificação que TF-IDF/GloVe; limite de entrada curto; erros em nuances de enredo; cosseno não é confiança calibrada. Não há ainda latência de API medida nem validação com usuários. É busca por conteúdo, não recomendação personalizada por histórico ou preferência individual. Essas etapas precisam ser definidas no escopo do TCC.

### fastText: manter como comparador estático

Tem valor por subpalavras, tratamento de formas raras e desempenho monolíngue útil. A instalação e Rare Words estão funcionando. Porém, o modelo inglês local não atende bem ao requisito PT → EN: nDCG 0,148 e Hit@1 3/58, apesar de gerar vetores para todos os termos. Além disso, a média de vetores perde relações entre palavras. Não escolher como núcleo agora reduz o trabalho de alinhar idiomas ou adicionar tradução antes de construir o produto.

Alternativas para a IC: vetores fastText português/inglês alinhados oficialmente, ou uma etapa fixa de tradução PT → EN seguida do mesmo buscador inglês. Treinar dois espaços separados, um por idioma, não basta: seus eixos precisam estar alinhados. A variante com tradução deve ser avaliada como pipeline próprio, contabilizando qualidade, tempo, dependências e erro do tradutor. Não foi instalada nem testada neste piloto.

### GloVe: referência clássica, sem prioridade de integração

Seu demo prova que o algoritmo e a ferramenta funcionam. No pipeline atual, palavras fora do vocabulário são descartadas e uma palavra conserva o mesmo vetor independentemente da frase; a média IDF também ignora ordem. A configuração inglesa 50d teve nDCG 0,115 em PT → EN. Para atender ao produto, seria preciso outro corpus/modelo, alinhamento ou tradução e nova avaliação. Manter como referência científica; não gastar o escopo inicial do TCC nessas adaptações.

### Word2Vec CBOW e Skip-gram: distinguir exemplo pequeno de candidato real

Não rejeitamos Word2Vec por causa do corpus didático Lee. Treinamos também CBOW e Skip-gram em text8, sem usar animes, e o Skip-gram mostrou resultado competitivo em inglês (0,739). Contudo, ambos ficam perto de 0,084 em PT → EN. O obstáculo combina idioma, vocabulário e agregação lexical; CBOW e Skip-gram não resolvem alinhamento automaticamente. Treinar um corpus pequeno de animes também não garante vetores melhores. Novas bases, múltiplas sementes e outros agregadores pertencem à investigação da IC.

### TF-IDF: conservar como controle barato

É simples, auditável e útil quando as mesmas palavras aparecem na consulta e descrição. Neste piloto em inglês teve 0,680, mas em PT → EN caiu para 0,127. Não atende sozinho à busca semântica entre idiomas. Deve permanecer como baseline para medir se a complexidade do encoder compensa. Não há razão para apagar os outros modelos ou encerrar sua investigação.

### GPT, Llama e DeepSeek

Não participaram do teste e não há pesos de geradores instalados. Portanto, não há evidência experimental para dizer que perdem para MiniLM. Um gerador pode futuramente explicar resultados ou reordenar candidatos, mas introduz outro problema de custo, avaliação e possíveis respostas inventadas. Para a entrega inicial, o encoder local já resolve a operação central de produzir vetores e ordenar candidatos. Não é necessário instalar um gerador agora para implementar essa arquitetura.

## 9. Exemplos concretos e erros preservados

{(chr(10)*2).join(examples)}

### Todos os 11 casos em que MiniLM não colocou grau 2 em primeiro

{error_text}

Há casos de proximidade temática e casos de perda do detalhe decisivo da consulta. Um grau 1 pode ser uma sugestão aceitável, mas continua sendo falha no Hit@1 forte definido previamente. Não alteramos os julgamentos depois de ver esses erros. A próxima análise humana deve revisar os pares sem mostrar qual modelo os produziu; discordâncias precisam ser registradas, não corrigidas silenciosamente para favorecer o vencedor.

## 10. Recursos observados nesta máquina

Ryzen 5 2400G, CPU, WSL2 com aproximadamente 6,7 GiB disponíveis e 2 GiB swap. Um processo de encoder por vez; quatro threads no MiniLM. Tabela registra o processo observado, incluindo imports e bibliotecas.

{resources}

**Esses números não são latência online por consulta nem um benchmark justo de velocidade.** Os modelos lexicais possuem estratégias de carregamento/cache diferentes; GloVe pode ler apenas vetores necessários. MiniLM codificou o lote completo de 194 textos únicos em cerca de 6,44 s após carregamento, não uma chamada de API individual. Pico RSS não é tamanho do arquivo e não equivale a toda a memória do sistema. Ainda faltam repetições, aquecimento, concorrência e medição separada da consulta com catálogo pré-indexado.

## 11. O que relatar na reunião

“Instalei e executei os exemplos e avaliações documentados de GloVe, fastText, Word2Vec e um encoder MiniLM multilíngue. Resolvi a obtenção da base Rare Words e documentei a origem alternativa. Construí um piloto reproduzível de busca de animes com 39 títulos e 58 consultas, com dados congelados antes das predições. Para consultas em português e descrições inglesas, MiniLM teve nDCG@5 0,805 e um resultado fortemente relevante em primeiro em 47 de 58 consultas. Proponho usar esse encoder no protótipo do TCC. A comparação ampla, controlada e com anotação humana fica para a IC. Os números atuais são exploratórios, porque textos e julgamentos foram preparados com IA.”

Pedir orientação sobre a formulação do objetivo: busca semântica de animes por descrição ou recomendação personalizada? Confirmar a separação TCC/IC, a fonte das sinopses reais, critérios de avaliação humana e requisitos mínimos do protótipo. Não afirmar que o sistema final já está pronto.

## 12. Próximas entregas e desenho da IC

No TCC: fixar MiniLM como candidato inicial; coletar catálogo com sinopses inglesas reais e fonte registrada; definir tratamento de sinopses maiores que 128 tokens; criar índice persistido e função/API de busca; interface com consulta PT e resultados; documentar versão dos dados e encoder; avaliar utilidade com consultas reais e julgamento humano. Se a avaliação independente contradisser o piloto, reabrir a escolha explicitamente.

Na IC: hipótese prévia sobre busca multilíngue e formulação; catálogo maior e com casos difíceis; consultas escritas por pessoas sem acesso às descrições-alvo; pelo menos dois avaliadores cegos e protocolo de adjudicação; separação por intenção entre desenvolvimento e teste; teste final não usado para ajustar hiperparâmetros; corpora e orçamento controlados quando a pergunta for causal; estáticos alinhados e tradução como alternativas distintas; várias sementes no treino; comparação pareada por intenção e análise de erros/custo. Não escolher arquitetura e publicar desempenho final usando o mesmo pequeno conjunto de ajuste.

## 13. Reprodução e trilha de auditoria

Ler `../PROTOCOLO.md`, `../dados/freeze.json` e `../README.md`. Código completo em `../codigo/`: 01 treina Word2Vec text8; 02 cria e congela a base; 03 codifica cada pipeline sem ler relevâncias; 04 orquestra; 05 avalia; 06 gera estes relatórios. Os scripts de instalação e demos oficiais continuam em `../../scripts/`, com documentação em `../../docs/`.

Preservados: JSON agregado, CSV por consulta, CSV agregado, rankings completos, matrizes NumPy e metadados/recursos de cada execução. O painel HTML é offline e usa resultados prontos; não consulta um modelo ao selecionar opções. Não reexecutar o gerador de base sobre o congelamento. Novas avaliações devem usar uma nova versão, mantendo v1.

Reprodutibilidade não significa identidade bit a bit: os treinos multithread podem variar apesar da seed. Pesos treinados e seus hashes são a referência desta execução. As comparações usam corpora, dimensões e pré-treinamentos diferentes; avaliam a escolha de pipelines disponíveis, não o efeito isolado de um algoritmo.
'''
(OUT/'RELATORIO_COMPARACAO.md').write_text(report,encoding='utf-8')

brief='''# Roteiro para a reunião das 15h - 29/10/2026

**Proposta:** usar MiniLM multilíngue como encoder principal do protótipo de busca do TCC; comparação ampla como IC.

## Relato em um minuto

Instalações verificadas: GloVe, fastText, Word2Vec CBOW/Skip-gram e MiniLM multilíngue. Rare Words resolvido: 2.034 pares, Spearman 0,4177, com origem alternativa documentada. Nenhum GPT/Llama/DeepSeek gerador instalado.

Piloto concluído: 39 animes reais, 58 consultas em 29 intenções e julgamentos congelados antes dos rankings. Cenário principal: consultas em português e descrições inglesas. MiniLM obteve nDCG@5 0,805 e Hit@1 47/58 (81,0%). Nas paráfrases, Hit@1 cai para 18/29: ainda há erros relevantes.

**Limitação indispensável:** descrições, consultas e relevâncias preparados com IA, sem validação humana independente. É evidência exploratória para uma decisão técnica, não resultado científico final nem benchmark oficial.

## Justificativa da escolha

MiniLM atende ao requisito entre idiomas e já roda localmente em CPU. Modelos estáticos ingleses não foram alinhados ao português; fastText gera vetores fora do vocabulário, mas isso não equivale a tradução. Em inglês, Skip-gram text8 teve nDCG 0,739 e fastText 0,723, portanto não devem ser declarados ruins ou descartados da IC.

## Decisões para discutir

- O TCC é busca semântica por descrição ou inclui personalização por usuário?
- Aprovar o encoder como candidato inicial e delimitar o protótipo.
- Definir fonte de sinopses reais, consultas humanas e avaliação cega.
- Tratar textos acima de 128 tokens e medir latência com catálogo pré-indexado.
- Separar implementação/avaliação do sistema (TCC) da comparação controlada de modelos (IC).

## Não afirmar

“MiniLM tem 80,5% de acurácia”; “o sistema final está pronto”; “fastText é sempre pior”; “LLMs perderam o teste”. nDCG é uma métrica de ranking e geradores não foram comparados.
'''
(OUT/'ROTEIRO_REUNIAO_15H.md').write_text(brief,encoding='utf-8')

payload=json.dumps({'queries':Q,'catalog':C,'ranks':K,'summary':R['summary'],'names':N,'models':MODELS},ensure_ascii=False).replace('</','<\\/')
chart=base64.b64encode((OUT/'comparacao-idiomas.png').read_bytes()).decode()
page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AniRec | piloto de busca</title>
<style>body{font:16px/1.6 system-ui;background:#f3f6fa;color:#192b3b;max-width:1150px;margin:30px auto;padding:0 22px}h1,h2{line-height:1.2}section{background:white;border-radius:14px;padding:25px;margin:20px 0}.note{border-left:5px solid #ce8714;background:#fff6e5;padding:16px}select{font:inherit;padding:10px;max-width:100%;margin:5px}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #ddd;padding:9px}.g2{background:#e4f2eb}.g1{background:#fff5d6}img{width:100%}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:15px}.card{border:1px solid #dae1e8;padding:15px;border-radius:9px}.sub{color:#56697a}button{padding:8px}details{margin:12px 0}a{color:#00669c}</style>
<h1>AniRec: qual pipeline continuar usando?</h1><p>29/10/2026 • Resultados preservados • consulta portuguesa / descrição inglesa como cenário principal</p>
<section><h2>MiniLM multilíngue é o candidato inicial</h2><div class="grid"><div class="card"><b>0,805 nDCG@5</b><br>Qualidade da ordem dos cinco primeiros.</div><div class="card"><b>47/58 consultas</b><br>Anime fortemente relevante em primeiro.</div><div class="card"><b>39 animes · 29 intenções</b><br>58 consultas; duas formulações por intenção.</div></div><p class="note"><b>Piloto exploratório:</b> títulos reais, descrições curtas e julgamentos preparados com IA. Sem anotação humana independente. Não são sinopses oficiais nem evidência de superioridade universal. nDCG não é acurácia.</p></section>
<section><h2>O idioma altera o resultado</h2><img alt="nDCG por modelo em três cenários, com intervalos bootstrap" src="data:image/png;base64,CHART"><p>Os modelos estáticos locais foram treinados em inglês. Subpalavras do fastText não alinham automaticamente os idiomas. Em inglês, Word2Vec Skip-gram e fastText recuperam boa parte do desempenho.</p></section>
<section><h2>Inspecionar as consultas</h2><p>Este painel lê rankings salvos; não executa inferência. Graus: 2 forte, 1 parcial, 0 não selecionado como pertinente. Empates exibidos por ID; métricas usam valor esperado do empate.</p><label>Cenário <select id="scenario"><option value="PT_EN">Português → inglês</option><option value="EN_EN">Inglês → inglês</option><option value="PT_PT">Português → português</option></select></label><label>Consulta <select id="query"></select></label><p id="text"></p><div class="grid" id="rankings"></div></section>
<section><h2>Catálogo e origem dos textos</h2><p>Metadados de identificação: Anime Offline Database, release 2026-27. Descrições abaixo são originais preparadas com IA para o piloto.</p><div id="catalog"></div></section><section><h2>Materiais completos</h2><p><a href="RELATORIO_COMPARACAO.md">Relatório detalhado</a> · <a href="../../../output/pdf/relatorio-comparacao-anirec.pdf">PDF</a> · <a href="ROTEIRO_REUNIAO_15H.md">Roteiro da reunião</a> · <a href="../PROTOCOLO.md">Protocolo</a> · <a href="../resultados/metricas-agregadas.csv">CSV agregado</a></p><p>Próximo passo: sinopses reais e validação humana, mantendo o teste final separado de ajustes. Para o TCC, construir o sistema com o encoder escolhido; para a IC, ampliar e controlar a comparação.</p></section>
<script>const D=PAYLOAD;const $=id=>document.getElementById(id);function el(tag,text){const e=document.createElement(tag);e.textContent=text;return e}D.queries.forEach((q,i)=>{const o=el('option',q.id+' · '+q.theme);o.value=i;$('query').append(o)});function render(){const i=Number($('query').value),s=$('scenario').value,q=D.queries[i];$('text').textContent=(s==='EN_EN'?q.text_en:q.text_pt);$('rankings').replaceChildren();D.models.forEach(m=>{const card=el('div','');card.className='card';card.append(el('h3',D.names[m]));const v=D.summary[m][s];card.append(el('p','Média nDCG@5: '+v.ndcg5.toFixed(3)));const t=el('table','');D.ranks[m][s][i].slice(0,5).forEach((r,j)=>{const tr=el('tr','');tr.className='g'+r.grade;[j+1,r.title,'grau '+r.grade,r.score.toFixed(4)].forEach(x=>tr.append(el('td',x)));t.append(tr)});card.append(t);$('rankings').append(card)})}$('query').onchange=render;$('scenario').onchange=render;D.catalog.forEach(c=>{const d=el('details','');d.append(el('summary',c.title));d.append(el('p',c.description_en));d.append(el('p',c.description_pt));$('catalog').append(d)});render();</script></html>'''.replace('CHART',chart).replace('PAYLOAD',payload)
(OUT/'painel-comparacao.html').write_text(page,encoding='utf-8')

# PDF: texto derivado do mesmo relatório, sem tabelas cortadas ou dependência web.
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
PDF=ROOT.parents[1]/'output/pdf/relatorio-comparacao-anirec.pdf'
PDF.parent.mkdir(parents=True,exist_ok=True)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyPT',fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=8))
styles['Heading1'].fontSize=17;styles['Heading1'].leading=21
styles['Heading2'].fontSize=14;styles['Heading2'].leading=18
styles['Heading3'].fontSize=11;styles['Heading3'].leading=15
def inline(t):
    t=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'\1 (\2)',t)
    t=html.escape(t.replace('→',' para ').replace('•',' | ').replace('—','-').replace('–','-'))
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t);t=t.replace('`','')
    return t
story=[]
blocks=report.split('\n\n')
for block in blocks:
    if not block.strip():continue
    if block.startswith('# '):
        story.append(Paragraph(inline(block[2:]),styles['Title']));continue
    if block.startswith('## '):
        story.append(Paragraph(inline(block[3:]),styles['Heading2']))
        if block.startswith('## 7.'):
            story.append(Image(str(OUT/'comparacao-idiomas.png'),width=17*cm,height=5.67*cm))
        continue
    if block.startswith('### '):story.append(Paragraph(inline(block[4:]),styles['Heading3']));continue
    if block.startswith('|'):
        lines=block.splitlines();cells=[]
        for line in lines:
            parts=[x.strip() for x in line.strip('|').split('|')]
            if all(re.fullmatch(r'[-: ]+',p) for p in parts):continue
            cells.append([Paragraph(inline(x),ParagraphStyle('cell',fontSize=7.1,leading=10)) for x in parts])
        n=len(cells[0]);widths=([4.4*cm]+[(17-4.4)*cm/(n-1)]*(n-1))
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=0)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1edf5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#7892a6')),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7fa')])]))
        story.extend([t,Spacer(1,10)]);continue
    for line in block.split('\n') if block.startswith('- ') else [block]:
        story.append(Paragraph(inline(line).replace('\n',' '),styles['BodyPT']))
def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526474'));canvas.drawString(1.9*cm,1.1*cm,'AniRec | piloto exploratório | 29/10/2026');canvas.drawRightString(19*cm,1.1*cm,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=1.9*cm,leftMargin=1.9*cm,topMargin=1.8*cm,bottomMargin=1.8*cm,title='AniRec - Comparação piloto de modelos',author='Lucas - laboratório TCC').build(story,onFirstPage=footer,onLaterPages=footer)
print(json.dumps({'pdf':str(PDF),'errors_top1':len(errors),'report_chars':len(report),'html_bytes':(OUT/'painel-comparacao.html').stat().st_size},ensure_ascii=False))
