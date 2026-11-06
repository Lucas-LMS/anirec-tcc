"""Valida CSV Kaggle, deduplica antes do split e congela avaliações futuras.

Não treina nem consulta modelos. Somente biblioteca padrão Python.
"""
import collections
import csv
import hashlib
import json
import pathlib
import random
import re
import unicodedata

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'dados'
SEED=20261105

def normalize(text):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',text).casefold()).strip()

def main():
    if (DATA/'freeze.json').exists():raise FileExistsError('Dataset já congelado; preservar e usar outra versão.')
    source=DATA/'brutos/spam.csv'
    with source.open(encoding='latin-1',newline='') as f:raw=list(csv.DictReader(f))
    assert all(x['v1'] in ['ham','spam'] and x['v2'].strip() for x in raw)
    groups=collections.defaultdict(list)
    for index,row in enumerate(raw):groups[normalize(row['v2'])].append((index,row))
    conflicts=[k for k,v in groups.items() if len({x[1]['v1'] for x in v})!=1]
    clean=[]
    for norm,entries in groups.items():
        if norm in conflicts:continue
        index,row=entries[0]
        clean.append({'id':hashlib.sha256(norm.encode()).hexdigest()[:20],
                      'label':row['v1'],'text':row['v2'],'source_row':index+2,
                      'copies_in_source':len(entries)})
    assert len({x['id'] for x in clean})==len(clean)
    rng=random.Random(SEED);splits={'train':[],'validation':[],'test':[]}
    for label in ['ham','spam']:
        rows=sorted([x for x in clean if x['label']==label],key=lambda x:x['id']);rng.shuffle(rows)
        n=len(rows);ntrain=int(.7*n);nval=int(.15*n)
        splits['train']+=rows[:ntrain];splits['validation']+=rows[ntrain:ntrain+nval];splits['test']+=rows[ntrain+nval:]
    for rows in splits.values():rng.shuffle(rows)
    common=[];nsmall=min(200,len(splits['test']))
    ham_n=round(nsmall*sum(x['label']=='ham' for x in splits['test'])/len(splits['test']))
    for label,n in [('ham',ham_n),('spam',nsmall-ham_n)]:common += [x for x in splits['test'] if x['label']==label][:n]
    rng.shuffle(common)
    splits['test-common-200']=common
    hashes={}
    for name,rows in splits.items():
        target=DATA/f'{name}.jsonl'
        target.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
        hashes[target.name]=hashlib.sha256(target.read_bytes()).hexdigest()
    ids={k:{x['id'] for x in v} for k,v in splits.items()}
    assert not ids['train']&ids['test'] and not ids['validation']&ids['test'] and not ids['train']&ids['validation']
    assert ids['test-common-200']<=ids['test']
    report={'date':'2026-11-05','source':'Kaggle uciml/sms-spam-collection-dataset',
            'source_rows':len(raw),'source_counts':dict(collections.Counter(x['v1'] for x in raw)),
            'normalization_for_dedup':'Unicode NFKC + casefold + colapso de whitespace; entrada do modelo preserva texto original.',
            'unique_normalized_groups':len(groups),'conflicting_groups_excluded':len(conflicts),
            'clean_rows':len(clean),'seed':SEED,
            'splits':{k:{'rows':len(v),'counts':dict(collections.Counter(x['label'] for x in v))} for k,v in splits.items()},
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'files_sha256':hashes,
            'purpose':'Classificação de SMS; não mede recomendação/busca de animes.',
            'note':'Rótulos existentes no dataset; não preparados por nós com IA. Dataset público antigo pode constar do pré-treino de LLMs.'}
    (DATA/'freeze.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
