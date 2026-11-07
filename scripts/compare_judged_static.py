"""Private one-query artifact comparison using explicit human relevance judgments.

The frozen candidate synopses are never replaced with newer text. Current common
IDF and anchor metadata are declared; results are a pilot, not a final test set.
"""
import argparse,json,math,subprocess,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'recomendador'))
from engine import tokenize,unit
from gensim.models import Word2Vec,KeyedVectors

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--judgments',required=True);ap.add_argument('--output',required=True);args=ap.parse_args();p=json.loads(Path(args.judgments).read_text());study=p['study'];base=Path(__file__).resolve().parents[1]/'recomendador/online';catalog=json.loads((base/'catalog.json').read_text());idf=json.loads((base/'idf.json').read_text());models=json.loads((base/'lab/models.json').read_text());bykey={r['key']:r for r in catalog['records']};anchor=bykey[study['anchor']['key']];pool=[r for r in study['pool'] if r['key'] in study['similarity_pool_keys']];docs=[study['anchor']]+pool;words=sorted({w for r in docs for w in tokenize(r['text'])});home=Path.home()/'tcc-lab';grades={k:v['similarity'] for k,v in p['judgments'].items() if 'similarity' in v};results=[]
    gain=lambda values:sum((2**v-1)/math.log2(i+2) for i,v in enumerate(values));ideal=gain(sorted([grades[r['key']] for r in pool],reverse=True)[:10])
    def theme(a,b):
        features=lambda r:{t['name'].lower():t['rank']/100*catalog['topic_idf'].get(t['name'].lower(),1) for t in r['tags'] if t['rank']>=50};av,bv=features(a),features(b);den=math.sqrt(sum(v*v for v in av.values())*sum(v*v for v in bv.values()));tag=sum(v*bv.get(k,0) for k,v in av.items())/den if den else 0;ga,gb=set(a['genres']),set(b['genres']);genre=len(ga&gb)/len(ga|gb) if ga|gb else 0;return .85*tag+.15*genre
    for spec in models['models']:
        start=time.perf_counter();name=spec['id']
        if name in ['skipgram','cbow']:kv=Word2Vec.load(str(home/'Word2Vec/models'/('text8-'+name+'-100d.model'))).wv
        elif name=='glove':kv=KeyedVectors.load_word2vec_format(str(home/'GloVe/vectors.txt'),binary=False,no_header=True)
        else:
            response=subprocess.run([str(home/'fastText/fasttext'),'print-word-vectors',str(home/'fastText/result/fil9.bin')],input='\n'.join(words)+'\n',capture_output=True,text=True,check=True);kv={line.split()[0]:np.asarray(line.split()[1:],dtype=np.float32) for line in response.stdout.splitlines()}
        vectors=[]
        for r in docs:
            known=[w for w in tokenize(r['text']) if w in kv];vectors.append(unit(np.average([kv[w] for w in known],axis=0,weights=[idf['idf'].get(w,idf['unseen']) for w in known])))
        encoding=time.perf_counter()-start;matrix=np.fromfile(base/spec['file'],dtype='<f4').reshape(spec['rows'],spec['dimensions']);mean=matrix[np.linalg.norm(matrix,axis=1)>0].mean(axis=0)
        for centered in [False,True]:
            transformed=[unit(v-mean) for v in vectors] if centered else vectors;ranked=sorted([{'key':r['key'],'title':r['title'],'grade':grades[r['key']],'score':.25*(float(np.clip(np.dot(transformed[0],transformed[i+1]),-1,1))+1)+.5*theme(anchor,r)} for i,r in enumerate(pool)],key=lambda r:(-r['score'],r['key']))[:10];results.append({'model':name,'variant':'mean_centered_diagnostic' if centered else 'original','precision_at_10':sum(r['grade']>=2 for r in ranked)/10,'ndcg_at_10':gain([r['grade'] for r in ranked])/ideal,'encoding_load_seconds':encoding,'ranking':ranked})
        del kv
    report={'protocol':'one-query-four-static-artifacts-v11','anchor':study['anchor']['title'],'pool_count':len(pool),'human_similarity_complete':True,'source_policy':'Frozen full candidate/anchor synopsis texts from supplied study; common current corpus IDF; current shared anchor tags; candidate tags from study. No training.','corpus_count':len(catalog['records']),'results':results,'limitations':['One query and one evaluator; preselected pool; not a final model-selection benchmark.','Centering subtracts the arithmetic corpus mean and renormalizes; experimental only, no fitted classifier.','Corpora/dimensions differ between model artifacts.']};Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps([{k:r[k] for k in ['model','variant','precision_at_10','ndcg_at_10']} for r in results]))

if __name__=='__main__':main()
