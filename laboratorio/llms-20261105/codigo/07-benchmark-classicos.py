"""Pipelines fixos de SMS: embeddings congelados + regressão logística.

Executar no WSL. Não ajusta parâmetros no teste. Medição individual inclui
tokenização/encode + predict_proba; embeddings do teste não são reutilizados
no loop que mede latência. IDF/vocabulário/classificador aprendem só no treino.
"""
import time
ENTRY=time.perf_counter()
import argparse
import collections
import hashlib
import math
import os
import pathlib
import resource
import subprocess
import sys

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from benchmark_suporte import OUT,ROOT,SEED,read_data,tokens,write_json

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True,
        choices=['dummy','tfidf','glove','fasttext','w2v-cbow','w2v-sg','minilm','w2v-lee-cbow','w2v-lee-sg'])
    args=parser.parse_args();target=OUT/args.model;target.mkdir(parents=True,exist_ok=True)
    if (target/'resultado.json').exists():print('Preservado:',args.model);return
    threadpool_limits(4)
    train,validation,test,common,freeze=read_data()
    texts=[x['text'] for x in train];y=np.array([x['label']=='spam' for x in train],dtype=int)
    lab=pathlib.Path.home()/'tcc-lab'
    process=None;source=None;notes=[];truncation=None;vocab=None;dimension=None;load_start=time.perf_counter()
    if args.model=='dummy':
        def encode(items):return np.zeros((len(items),1))
    elif args.model=='tfidf':
        vectorizer=TfidfVectorizer(tokenizer=tokens,token_pattern=None,lowercase=False,
                                  ngram_range=(1,2),sublinear_tf=True,norm='l2')
        # fit é medido na etapa de treinamento abaixo.
        def encode(items):return vectorizer.transform(items)
    elif args.model=='minilm':
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(4)
        source=lab/'SentenceTransformers/models/paraphrase-multilingual-MiniLM-L12-v2'
        model=SentenceTransformer(str(source),device='cpu',local_files_only=True,trust_remote_code=False)
        dimension=model.get_sentence_embedding_dimension()
        def encode(items):return model.encode(items,batch_size=32,normalize_embeddings=True,show_progress_bar=False)
        truncation={}
        for name,rows in [('train',train),('validation',validation),('test',test),('common',common)]:
            lengths=[len(row) for row in model.tokenizer([x['text'] for x in rows],truncation=False)['input_ids']]
            truncation[name]={'max_tokens':max(lengths),'over_limit':sum(n>model.max_seq_length for n in lengths),'limit':model.max_seq_length}
        notes.append('Truncamento no limite original de 128 tokens é registrado; o limite não foi aumentado após observar resultados.')
    else:
        if args.model=='glove':
            source=lab/'GloVe/vectors.txt';lookup={}
            with source.open() as f:
                for line in f:
                    word,_,values=line.partition(' ');lookup[word]=np.fromstring(values,sep=' ',dtype=np.float32)
            vocab=set(lookup);dimension=50;get=lambda word:lookup.get(word)
        elif args.model.startswith('w2v-'):
            from gensim.models import Word2Vec
            files={'w2v-cbow':'text8-cbow-100d.model','w2v-sg':'text8-skipgram-100d.model',
                   'w2v-lee-cbow':'lee-cbow.model','w2v-lee-sg':'lee-skipgram.model'}
            source=lab/'Word2Vec/models'/files[args.model];model=Word2Vec.load(str(source))
            vocab=set(model.wv.index_to_key);dimension=model.vector_size
            get=lambda word:model.wv[word] if word in model.wv else None
        else:
            source=lab/'fastText/result/fil9.bin';dimension=100
            with (lab/'fastText/result/fil9.vec').open() as f:
                next(f);vocab={line.partition(' ')[0] for line in f}
            err=(target/'fasttext-stderr.log').open('w')
            process=subprocess.Popen([str(lab/'fastText/fasttext'),'print-word-vectors',str(source)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
            def get(word):
                process.stdin.write(word+'\n');process.stdin.flush();fields=process.stdout.readline().split()
                assert len(fields)==dimension+1 and fields[0]==word
                return np.asarray(fields[1:],dtype=np.float32)
            get('the')
            notes.append('Consulta lexical fastText pela CLI persistente. Latência inclui IPC por palavra e não mede só o algoritmo interno.')
        df=collections.Counter(word for text in texts for word in set(tokens(text)))
        idf={word:math.log((1+len(texts))/(1+n))+1 for word,n in df.items()};unseen=math.log(1+len(texts))+1
        train_cache={}
        if args.model=='fasttext':
            for word in sorted(df):train_cache[word]=get(word)
        def encode(items,training=False):
            rows=[]
            for text in items:
                values=[];weights=[];local={}
                for word in tokens(text):
                    if word not in local:local[word]=train_cache.get(word) if training else get(word)
                    value=local[word]
                    if value is not None and np.linalg.norm(value)>0:values.append(value);weights.append(idf.get(word,unseen))
                vector=np.average(np.stack(values),axis=0,weights=weights) if values else np.zeros(dimension)
                norm=np.linalg.norm(vector);rows.append(vector/norm if norm else vector)
            return np.asarray(rows,dtype=np.float32)
    loaded=time.perf_counter()-load_start
    try:
        start=time.perf_counter()
        if args.model=='tfidf':x=vectorizer.fit_transform(texts)
        elif args.model=='fasttext':x=encode(texts,training=True)
        else:x=encode(texts)
        encode_train=time.perf_counter()-start
        classifier=DummyClassifier(strategy='most_frequent') if args.model=='dummy' else LogisticRegression(C=1,max_iter=1000,class_weight='balanced',random_state=SEED)
        start=time.perf_counter();classifier.fit(x,y);fit=time.perf_counter()-start
        # Aquecimento com exemplos do treino, não com predições do teste.
        for row in train[:3]:classifier.predict_proba(encode([row['text']]))
        predictions=[]
        for i,row in enumerate(common):
            start=time.perf_counter();v=encode([row['text']]);probs=classifier.predict_proba(v)[0];elapsed=time.perf_counter()-start
            probability=float(probs[list(classifier.classes_).index(1)])
            predictions.append({'id':row['id'],'prediction':'spam' if probability>=.5 else 'ham',
                                'spam_probability':probability,'wall_seconds':elapsed})
        # Teste completo adicional; não confundir com o denominador comum.
        start=time.perf_counter();full_x=encode([row['text'] for row in test]);full=classifier.predict_proba(full_x)[:,list(classifier.classes_).index(1)];full_seconds=time.perf_counter()-start
        full_predictions=[{'id':row['id'],'prediction':'spam' if probability>=.5 else 'ham','spam_probability':float(probability)} for row,probability in zip(test,full)]
        coverage=None
        if vocab is not None:
            words=[w for row in common for w in tokens(row['text'])]
            coverage={'in_vocabulary_token_fraction':sum(w in vocab for w in words)/len(words)}
        metadata={'model':args.model,'environment':'Ubuntu/WSL2 CPU','threads':4,'seed':SEED,
                  'load_seconds':loaded,'imports_and_setup_seconds':time.perf_counter()-ENTRY-loaded-encode_train-fit-full_seconds-sum(p['wall_seconds'] for p in predictions),
                  'encode_train_seconds':encode_train,'classifier_fit_seconds':fit,'full_test_batch_seconds':full_seconds,
                  'peak_rss_kib_self':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'peak_rss_kib_child':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  'truncation':truncation,'coverage':coverage,'notes':notes,'source_path':str(source),
                  'classifier':classifier.get_params(),'files_sha256':freeze['files_sha256'],'common_count':len(predictions),
                  'inference_timing':'Uma mensagem por vez, tokenização/encode + predict_proba, após três aquecimentos; sem reutilizar embeddings de teste.'}
        write_json(target/'predictions.json',predictions);write_json(target/'full-test-predictions.json',full_predictions)
        write_json(target/'resultado.json',metadata)
        print(args.model,'concluído; média s/mensagem=',sum(x['wall_seconds'] for x in predictions)/len(predictions),flush=True)
    finally:
        if process:
            process.stdin.close();process.stdout.close();process.wait(timeout=30);err.close()

if __name__=='__main__':main()
