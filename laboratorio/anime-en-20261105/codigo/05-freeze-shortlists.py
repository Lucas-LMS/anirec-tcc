"""Freeze TF-IDF shortlists using scores only, without consulting qrels."""
import hashlib,random
from support import DATA,OUT,SEED,read,load,save,prompt
catalog,queries,freeze=read();byid={r['id']:r for r in catalog}
target=DATA/'shortlists.json';assert not target.exists(),'Preserve frozen shortlists.'
scores=load(OUT/'retrieval/tfidf/scores.json');assert [x['id'] for x in scores]==[q['id'] for q in queries]
shortlists=[]
for i,(q,record) in enumerate(zip(queries,scores)):
    indices=sorted(range(len(catalog)),key=lambda j:(-record['scores'][j],int(catalog[j]['id'])))[:5]
    original=[catalog[j]['id'] for j in indices];permuted=original.copy();random.Random(SEED+i).shuffle(permuted)
    candidates=[dict(id=chr(65+k),synopsis=byid[item]['text']) for k,item in enumerate(permuted)]
    shortlists.append(dict(id=q['id'],tfidf_order=original,candidate_map={chr(65+k):item for k,item in enumerate(permuted)},prompt=prompt(q['text'],candidates)))
save(target,shortlists)
save(DATA/'shortlists-freeze.json',dict(seed=SEED,selection='TF-IDF top five; no qrels consulted; score ties by MAL_ID',sha256=hashlib.sha256(target.read_bytes()).hexdigest(),prompt_template_sha256=hashlib.sha256(__import__('support').INSTRUCTION.encode()).hexdigest()))
print('Frozen:',len(shortlists),'shortlists, five candidates each.')
