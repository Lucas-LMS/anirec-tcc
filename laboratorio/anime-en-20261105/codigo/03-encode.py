"""Index frozen English synopses and measure individual query retrieval.

No qrels or genre labels are used in scoring. One model per process.
"""
import argparse,collections,math,resource,subprocess,time,hashlib,shutil
import numpy as np
from threadpoolctl import threadpool_limits
from support import OUT,ROOT,SEED,read,save,tokens
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True);args=parser.parse_args()
    target=OUT/'retrieval'/args.model
    if (target/'result.json').exists():print('Preserved:',args.model);return
    snapshot=ROOT/'data/frozen-code'
    if not snapshot.exists():
        snapshot.mkdir()
        for src in list((ROOT/'codigo').glob('*.py'))+list((ROOT/'codigo').glob('*.sh'))+[ROOT/'PROTOCOL.md']:shutil.copy2(src,snapshot/src.name)
        save(ROOT/'data/implementation-freeze.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()})
    threadpool_limits(4);catalog,queries,freeze=read();texts=[x['text'] for x in catalog]
    from pathlib import Path
    lab=Path.home()/'tcc-lab';process=None;source=None;vocab=None;trunc=None;started=time.perf_counter()
    df=collections.Counter(w for text in texts for w in set(tokens(text)));idf={w:math.log((1+len(texts))/(1+n))+1 for w,n in df.items()};unseen=math.log(1+len(texts))+1
    if args.model=='tfidf':
        from sklearn.feature_extraction.text import TfidfVectorizer
        encoder=TfidfVectorizer(tokenizer=tokens,token_pattern=None,lowercase=False,ngram_range=(1,2),sublinear_tf=True,norm='l2')
        matrix=encoder.fit_transform(texts)
        def score(text):return (encoder.transform([text])@matrix.T).toarray()[0]
    elif args.model=='bm25':
        counts=[collections.Counter(tokens(text)) for text in texts];lengths=np.array([sum(c.values()) for c in counts]);average=lengths.mean()
        terms={w:np.array([c.get(w,0) for c in counts]) for w in df}
        def score(text):
            result=np.zeros(len(catalog))
            for w in set(tokens(text)):
                if w in terms:
                    tf=terms[w];weight=math.log(1+(len(catalog)-df[w]+.5)/(df[w]+.5))
                    result+=weight*tf*2.2/(tf+1.2*(.25+.75*lengths/average))
            return result
    elif args.model=='random':
        def score(text):return np.zeros(len(catalog))
    else:
        if args.model=='minilm':
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(4);source=lab/'SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2'
            encoder=SentenceTransformer(str(source),device='cpu',local_files_only=True,trust_remote_code=False)
            lengths=[len(x) for x in encoder.tokenizer(texts,truncation=False)['input_ids']]
            trunc=dict(limit=encoder.max_seq_length,documents_over_limit=sum(n>encoder.max_seq_length for n in lengths),max_document_tokens=max(lengths))
            def encode(items):return encoder.encode(items,batch_size=32,normalize_embeddings=True,show_progress_bar=False)
        else:
            if args.model=='glove':
                source=lab/'GloVe/vectors.txt';lookup={}
                with source.open() as f:
                    for line in f:
                        word,_,values=line.partition(' ');lookup[word]=np.fromstring(values,sep=' ',dtype=np.float32)
                vocab=set(lookup);dim=50;get=lambda w:lookup.get(w)
            elif args.model.startswith('w2v-'):
                from gensim.models import Word2Vec
                files={'w2v-cbow':'text8-cbow-100d.model','w2v-sg':'text8-skipgram-100d.model','w2v-lee-cbow':'lee-cbow.model','w2v-lee-sg':'lee-skipgram.model'}
                source=lab/'Word2Vec/models'/files[args.model];encoder=Word2Vec.load(str(source));dim=encoder.vector_size;vocab=set(encoder.wv.index_to_key)
                get=lambda w:encoder.wv[w] if w in vocab else None
            elif args.model=='fasttext':
                source=lab/'fastText/result/fil9.bin';dim=100
                stderr=(target/'fasttext.log');target.mkdir(parents=True,exist_ok=True);err=stderr.open('w')
                process=subprocess.Popen([str(lab/'fastText/fasttext'),'print-word-vectors',str(source)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
                def get(w):
                    process.stdin.write(w+'\n');process.stdin.flush();fields=process.stdout.readline().split();assert len(fields)==101 and fields[0]==w
                    return np.asarray(fields[1:],dtype=np.float32)
            else:raise ValueError(args.model)
            # Cache catalog terms for indexing only; query calls are fresh.
            cache={w:get(w) for w in df}
            def encode(items,indexing=False):
                vectors=[]
                for text in items:
                    local={};values=[];weights=[]
                    for w in tokens(text):
                        if w not in local:local[w]=cache[w] if indexing else get(w)
                        value=local[w]
                        if value is not None and np.linalg.norm(value)>0:values.append(value);weights.append(idf.get(w,unseen))
                    vector=np.average(np.stack(values),axis=0,weights=weights) if values else np.zeros(dim)
                    norm=np.linalg.norm(vector);vectors.append(vector/norm if norm else vector)
                return np.asarray(vectors,dtype=np.float32)
        matrix=encode(texts) if args.model=='minilm' else encode(texts,indexing=True)
        def score(text):return (encode([text])@matrix.T)[0]
    prep=time.perf_counter()-started
    try:
        for text in ['A story about a journey.','A funny romance.','A mystery in space.']:score(text)
        records=[]
        for query in queries:
            start=time.perf_counter();scores=score(query['text']);elapsed=time.perf_counter()-start
            assert len(scores)==len(catalog) and np.isfinite(scores).all()
            records.append(dict(id=query['id'],scores=scores.tolist(),wall_seconds=elapsed))
        coverage=None
        if vocab:
            words=[w for q in queries for w in tokens(q['text'])];coverage=sum(w in vocab for w in words)/len(words)
        # Persist the unsupervised index for future reuse, outside query timing.
        target.mkdir(parents=True,exist_ok=True)
        if args.model=='tfidf':
            import joblib
            from scipy.sparse import save_npz
            save_npz(target/'document-index.npz',matrix);joblib.dump(encoder,target/'vectorizer.joblib')
        elif args.model=='bm25':save(target/'bm25-index.json',dict(counts=[dict(c) for c in counts],k1=1.2,b=.75))
        elif args.model!='random':np.save(target/'document-index.npy',matrix)
        save(target/'index-config.json',dict(document_ids=[r['id'] for r in catalog],idf=idf,unseen_idf=unseen,source=str(source),dataset_sha256=freeze['files_sha256']))
        save(target/'scores.json',records)
        save(target/'result.json',dict(model=args.model,catalog_size=len(catalog),queries=len(queries),preparation_seconds=prep,peak_rss_kib_self=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source=str(source),query_vocabulary_coverage=coverage,truncation=trunc,files_sha256=freeze['files_sha256'],timing='Fresh individual query encoding plus full catalog scoring after three synthetic warmups; index preparation separate.'))
        print(args.model,'complete; mean query seconds:',np.mean([r['wall_seconds'] for r in records]),flush=True)
    finally:
        if process:process.stdin.close();process.stdout.close();process.wait(timeout=30);err.close()
if __name__=='__main__':main()
