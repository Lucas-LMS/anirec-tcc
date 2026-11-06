"""Avaliação reproduzível: nunca treina nem modifica predições do benchmark."""
import csv, hashlib, json, re
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/'resultados'/'benchmark-v1'
MODELS=['dummy','tfidf','glove','fasttext','w2v-cbow','w2v-sg','minilm','w2v-lee-cbow','w2v-lee-sg','llama','deepseek','qwen','gptoss']
NAMES=['Maioria ham','TF-IDF + LR','GloVe + LR','fastText + LR','Word2Vec CBOW + LR','Word2Vec Skip-gram + LR','MiniLM + LR','Lee CBOW (diagnóstico)','Lee Skip-gram (diagnóstico)','Llama 3.2 1B Q4','DeepSeek distill 1.5B Q4','Qwen3 0.6B Q8','GPT-OSS 20B / Groq']
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def metrics(y,p):
    # Colunas: ham, spam, inválida. Uma inválida sempre conta como erro.
    cm=np.zeros((2,3),dtype=int)
    for a,b in zip(y,p):cm[a,b]+=1
    recalls=[];f=[]
    for k in [0,1]:
        tp=cm[k,k];fp=cm[1-k,k];fn=cm[k].sum()-tp
        precision=tp/(tp+fp) if tp+fp else 0
        recall=tp/(tp+fn) if tp+fn else 0
        f.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0);recalls.append(recall)
        if k==1:sp, sr=precision,recall
    return dict(accuracy=float((cm[0,0]+cm[1,1])/len(y)),precision_spam=float(sp),recall_spam=float(sr),f1_spam=float(f[1]),macro_f1=float(np.mean(f)),balanced_accuracy=float(np.mean(recalls)),invalid=int(cm[:,2].sum()),confusion=cm.tolist())
def evaluate():
    freeze=load(BASE/'dados/freeze.json')
    for filename,expected in freeze['files_sha256'].items():
        assert hashlib.sha256((BASE/'dados'/filename).read_bytes()).hexdigest()==expected,filename
    data=rows(BASE/'dados/test-common-200.jsonl');ids=[x['id'] for x in data]
    y=np.array([int(x['label']=='spam') for x in data]);assert len(y)==200 and sum(y)==25
    rng=np.random.default_rng(20261105)
    # Mesmos índices de bootstrap em todos os modelos: comparação pareada.
    boot=np.array([np.concatenate([rng.choice(np.where(y==0)[0],175),rng.choice(np.where(y==1)[0],25)]) for _ in range(5000)])
    out=[];preds={}
    for model,name in zip(MODELS,NAMES):
        path=ROOT/model
        if not (path/'resultado.json').exists():print('Pendente:',model);continue
        meta=load(path/'resultado.json');records=load(path/'predictions.json')
        assert [x['id'] for x in records]==ids,model
        p=np.array([{'ham':0,'spam':1}.get(x['prediction'],2) for x in records]);preds[model]=p
        m=metrics(y,p)
        # Conferência independente com implementação oficial sklearn.
        from sklearn.metrics import precision_recall_fscore_support,accuracy_score
        ps,rs,fs,_=precision_recall_fscore_support(y,p,labels=[0,1],zero_division=0)
        assert np.allclose([m['f1_spam'],m['macro_f1'],m['accuracy']],[fs[1],fs.mean(),accuracy_score(y,p)])
        times=np.array([x['wall_seconds'] for x in records]);bs=[metrics(y[ix],p[ix])['f1_spam'] for ix in boot]
        peak=meta.get('peak_rss_kib_server')
        if (path/'recursos-runner.txt').exists():
            match=re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',(path/'recursos-runner.txt').read_text())
            if match:peak=max(peak or 0,int(match.group(1)))
        entry=dict(model=model,name=name,**m,f1_ci95=np.quantile(bs,[.025,.975]).tolist(),mean_ms=float(times.mean()*1000),median_ms=float(np.median(times)*1000),p95_ms=float(np.quantile(times,.95)*1000),sum_response_seconds=float(times.sum()),throughput_serial_per_second=float(1/times.mean()),throttle_seconds=sum(x.get('throttle_seconds',0) for x in records),peak_rss_mib=peak/1024 if peak else None,metadata=meta)
        interruption=meta.get('interruption')
        if interruption:
            conservative=p.copy();conservative[ids.index(interruption['affected_id'])]=2
            entry['first_attempt_quality_sensitivity']=metrics(y,conservative)
            entry['operational_interruption_count']=1
            entry['timing_exception']='Completed-response latencies exclude the prior failed attempt; first response after recovery has no fresh warmup. Original total stage duration unavailable.'
        if all('spam_probability' in x for x in records):
            from sklearn.metrics import roc_auc_score,average_precision_score
            probs=[x['spam_probability'] for x in records]
            entry.update(roc_auc=roc_auc_score(y,probs),average_precision=average_precision_score(y,probs))
        if (path/'requests.jsonl').exists():entry['length_finishes']=sum(x.get('finish_reason')=='length' for x in records)
        if (path/'full-test-predictions.json').exists():
            full=load(path/'full-test-predictions.json');truth=rows(BASE/'dados/test.jsonl')
            assert [x['id'] for x in full]==[x['id'] for x in truth]
            entry['full_test_775']=metrics([int(x['label']=='spam') for x in truth],[{'ham':0,'spam':1}.get(x['prediction'],2) for x in full])
        out.append(entry)
    pairs=[]
    for other in ['fasttext','w2v-cbow','w2v-sg','minilm','tfidf','llama','deepseek','qwen','gptoss']:
        if 'glove' in preds and other in preds:
            differences=[metrics(y[ix],preds['glove'][ix])['f1_spam']-metrics(y[ix],preds[other][ix])['f1_spam'] for ix in boot]
            pairs.append(dict(first='glove',second=other,delta_ci95=np.quantile(differences,[.025,.975]).tolist()))
    target=BASE/'resultados'/'comparacao';target.mkdir(exist_ok=True)
    result=dict(n=200,spam=25,bootstrap_replicates=5000,models=out,paired_glove=pairs,complete=len(out)==len(MODELS))
    (target/'comparacao.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    fields=['model','name','f1_spam','precision_spam','recall_spam','macro_f1','balanced_accuracy','accuracy','invalid','mean_ms','median_ms','p95_ms','sum_response_seconds','throttle_seconds','peak_rss_mib']
    with (target/'comparacao.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(out)
    for item in sorted(out,key=lambda x:-x['f1_spam']):print(f"{item['model']:15} F1={item['f1_spam']:.4f} média={item['mean_ms']:.3f}ms inválidas={item['invalid']}")
    return result
if __name__=='__main__':
    evaluate()
    import subprocess,sys
    extra=BASE/'codigo/15-cenarios-sms.py'
    if extra.exists():subprocess.run([sys.executable,str(extra)],check=True)
