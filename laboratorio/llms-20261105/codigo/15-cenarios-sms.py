"""Análises pós-hoc úteis, sem mudar os parâmetros ou refazer predições.

Não seleciona limiar no teste. Custos são hipotéticos, não valores em dinheiro.
"""
import importlib.util,json
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('evaluation',BASE/'codigo/12-avaliar-comparacao.py')
ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
data=ev.rows(BASE/'dados/test-common-200.jsonl');ids=[x['id'] for x in data]
truth=np.array([int(x['label']=='spam') for x in data])
result=[]
for model in ev.MODELS:
    source=ev.ROOT/model/'predictions.json'
    if not source.exists():continue
    records=ev.load(source);assert [x['id'] for x in records]==ids
    predictions=np.array([{'ham':0,'spam':1}.get(x['prediction'],2) for x in records])
    cm=np.asarray(ev.metrics(truth,predictions)['confusion'])
    cohorts=[]
    for label,low,high in [('short: 1-80 characters',1,80),('medium: 81-160 characters',81,160),('long: >160 characters',161,10**9)]:
        ix=[i for i,row in enumerate(data) if low<=len(row['text'])<=high]
        cohorts.append(dict(cohort=label,n=len(ix),spam=int(truth[ix].sum()),**ev.metrics(truth[ix],predictions[ix])))
    item=dict(model=model,cohorts=cohorts,costs={})
    for label,fp,fn in [('equal',1,1),('protect_legitimate_messages',5,1),('prioritize_spam_detection',1,5)]:
        item['costs'][label]=dict(false_positive_weight=fp,false_negative_weight=fn,invalid_weight=max(fp,fn),total_units=int(fp*cm[0,1]+fn*cm[1,0]+max(fp,fn)*cm[:,2].sum()),units_per_message=float((fp*cm[0,1]+fn*cm[1,0]+max(fp,fn)*cm[:,2].sum())/len(data)))
    if all('spam_probability' in row for row in records):
        probability=np.array([row['spam_probability'] for row in records])
        item['brier_score']=float(np.mean((probability-truth)**2))
    result.append(item)
target=BASE/'resultados/comparacao/cenarios-sms.json'
target.write_text(json.dumps(dict(post_hoc=True,thresholds_changed=False,note='Exploratory operational costs and length cohorts; not independent test replications. Invalid response receives the larger error cost. Cohorts have different label prevalences.',models=result),ensure_ascii=False,indent=2),encoding='utf-8')
print('Cenários adicionais:',len(result),'pipelines; nenhuma nova inferência.')
