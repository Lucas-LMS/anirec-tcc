"""Export public metadata and frozen embeddings; never trains or reads user profiles."""
import collections,datetime,hashlib,json,subprocess,time
from pathlib import Path
import numpy as np
from gensim.models import Word2Vec,KeyedVectors
from engine import tokenize,unit

def main():
    root=Path(__file__).parent;out=root/'online';lab=out/'lab';lab.mkdir(exist_ok=True)
    catalog=json.loads((out/'catalog.json').read_text());idf=json.loads((out/'idf.json').read_text())
    records=catalog['records'];documents=[tokenize(r['text']) for r in records];vocab=sorted({w for doc in documents for w in doc})
    home=Path.home()/'tcc-lab';models=[]
    specs=[('skipgram','Word2Vec Skip-gram · text8',home/'Word2Vec/models/text8-skipgram-100d.model','gensim','https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html'),('cbow','Word2Vec CBOW · text8',home/'Word2Vec/models/text8-cbow-100d.model','gensim','https://radimrehurek.com/gensim/auto_examples/tutorials/run_word2vec.html'),('glove','GloVe · text8',home/'GloVe/vectors.txt','glove','https://nlp.stanford.edu/projects/glove/'),('fasttext','fastText Skip-gram · fil9 · subpalavras',home/'fastText/result/fil9.bin','fasttext','https://fasttext.cc/docs/en/unsupervised-tutorial.html')]
    for name,label,path,kind,url in specs:
        start=time.perf_counter();print('Exportando',name,flush=True)
        if kind=='gensim':
            trained=Word2Vec.load(str(path));kv=trained.wv
            settings={k:getattr(trained,k,None) for k in ['sg','vector_size','window','min_count','epochs','negative','seed']}
        elif kind=='glove':
            kv=KeyedVectors.load_word2vec_format(str(path),binary=False,no_header=True);settings={'dimensions':kv.vector_size,'training_parameters':'See retained historical GloVe run logs; not inferred from vectors.'}
        else:
            proc=subprocess.run([str(home/'fastText/fasttext'),'print-word-vectors',str(path)],input='\n'.join(vocab)+'\n',text=True,capture_output=True,check=True)
            kv={}
            for line in proc.stdout.splitlines():
                parts=line.split();kv[parts[0]]=np.asarray(parts[1:],dtype=np.float32)
            settings={'dimensions':len(next(iter(kv.values()))),'subwords':'Frozen .bin generates unseen-word vectors; no training.'}
        dimensions=len(next(iter(kv.values()))) if isinstance(kv,dict) else kv.vector_size
        vectors=[];coverage=[]
        for doc in documents:
            known=[w for w in doc if w in kv];coverage.append(len(known)/len(doc) if doc else 0)
            dim=dimensions
            vectors.append(unit(np.average([kv[w] for w in known],axis=0,weights=[idf['idf'].get(w,idf['unseen']) for w in known])) if known else np.zeros(dim))
        matrix=np.asarray(vectors,dtype='<f4');blob=matrix.tobytes();(lab/(name+'.bin')).write_bytes(blob)
        spec={'id':name,'label':label,'file':'lab/'+name+'.bin','dimensions':matrix.shape[1],'rows':len(records),'sha256':hashlib.sha256(blob).hexdigest(),'artifact_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':url,'settings':settings,'mean_token_coverage':float(np.mean(coverage)),'zero_documents':int(sum(not np.any(v) for v in matrix)),'export_seconds':time.perf_counter()-start}
        models.append(spec);print(json.dumps(spec),flush=True)
        del kv
    manifest={'built_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'corpus_sha256':hashlib.sha256((out/'catalog.json').read_bytes()).hexdigest(),'row_keys':[r['key'] for r in records],'models':models,'policy':'Frozen identical public AniList corpus; full synopsis; same IDF and rank parameters. No training. fastText corpus differs (fil9 vs text8), so this is artifact comparison, not controlled algorithm-only comparison.'}
    (lab/'models.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    raw=json.loads((Path.home()/'tcc-lab/recomendador-private/catalog-snapshot.json').read_text());byid={r['id']:r for r in raw}
    enriched=[]
    for r in records:
        src=byid[r['anilist_id']];enriched.append({k:r.get(k) for k in ['key','title','anilist_id','source','metadata_fetched_at','average_score','mean_score','popularity','community_favourites','rating_count','statistics_fetched_at']}|{'format':src.get('format'),'year':src.get('seasonYear'),'status':src.get('status'),'genres':r['genres'],'tags':len(r['tags']),'words':len(tokenize(r['text'])),'synopsis':r['text'],'vector_nonzero':any(r['vector'])})
    (lab/'dataset.json').write_text(json.dumps({'snapshot_total':len(raw),'public_total':len(records),'excluded_adult':sum(bool(r.get('isAdult')) for r in raw),'rows':enriched,'selection':'Application usage, popularity sample and queries; user/popularity bias. Not a complete or representative catalogue.','built_at':manifest['built_at'],'sha256':manifest['corpus_sha256']},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

if __name__=='__main__':main()
