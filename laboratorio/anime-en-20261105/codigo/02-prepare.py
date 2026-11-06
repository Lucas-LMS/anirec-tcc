"""Freeze an English recommendation proxy before any model predictions.

Ground truth is derived from publisher genres, not a judge LLM. It is a
controlled genre-adherence benchmark, not human preference assessment.
"""
import collections,csv,hashlib,json,random,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';SEED=20261105
def norm(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
def save(name,obj):
    p=DATA/name;p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (DATA/'freeze.json').exists(),'Preserve the existing frozen benchmark.'
    with (DATA/'raw/anime_with_synopsis.csv').open(encoding='utf-8-sig',newline='') as f:raw=list(csv.DictReader(f))
    seen=set();eligible=[];excluded=collections.Counter()
    for row in sorted(raw,key=lambda r:int(r['MAL_ID'])):
        text=re.sub(r'\[Written by.*?\]','',row['sypnopsis'],flags=re.S)
        text=re.sub(r'\(Source:.*','',text,flags=re.S);text=re.sub(r'\s+',' ',text).strip()
        genres=sorted(g.strip() for g in row['Genres'].split(',') if g.strip() and g.strip()!='Unknown')
        if not genres or len(text.split())<40:excluded['missing_or_short']+=1;continue
        words=set(re.findall('[a-z]+',text.casefold()))
        english=len(words&set('the and of to in with a is his her their for on as'.split()))>=3
        letters=[c for c in text if c.isalpha()]
        if not english or sum(c.isascii() for c in letters)/max(1,len(letters))<.9:excluded['language_heuristic']+=1;continue
        snippet=' '.join(text.split()[:80]);key=norm(snippet)
        if key in seen:excluded['duplicate_snippet']+=1;continue
        seen.add(key);eligible.append(dict(id=row['MAL_ID'],title=row['Name'],text=snippet,genres=genres,original_words=len(text.split()),source_score=row['Score']))
    rng=random.Random(SEED);catalog=sorted(rng.sample(eligible,1000),key=lambda x:int(x['id']))
    # The literal and paraphrase express the same metadata-defined intent.
    intents=[
      ('sports',['Sports'],[], 'Recommend a sports anime about competition and practice.', 'I want athletes working hard to improve and compete.'),
      ('mecha',['Mecha'],[], 'Recommend a mecha anime featuring giant robots.', 'I want a story where people pilot large machines.'),
      ('mystery',['Mystery'],[], 'Recommend a mystery anime with secrets to investigate.', 'I want to follow clues and uncover hidden explanations.'),
      ('romance',['Romance'],[], 'Recommend an anime centered on romance.', 'I want characters falling in love and developing a relationship.'),
      ('comedy',['Comedy'],[], 'Recommend a funny comedy anime.', 'I want an entertaining story that makes me laugh.'),
      ('science-fiction',['Sci-Fi'],[], 'Recommend a science fiction anime.', 'I want a story involving futuristic technology or scientific possibilities.'),
      ('action-adventure',['Action','Adventure'],[], 'Recommend an action and adventure anime.', 'I want an exciting journey with danger, fights, and exploration.'),
      ('fantasy-romance',['Fantasy','Romance'],[], 'Recommend an anime combining fantasy and romance.', 'I want a love story in an imaginative world with fantastic elements.'),
      ('school-comedy',['School','Comedy'],[], 'Recommend a comedy anime set at school.', 'I want funny situations involving students and school life.'),
      ('supernatural-mystery',['Supernatural','Mystery'],[], 'Recommend an anime combining supernatural events and mystery.', 'I want strange otherworldly events investigated through clues and secrets.'),
      ('action-no-mecha',['Action'],['Mecha'], 'Recommend an action anime, but exclude mecha and giant robots.', 'I want exciting fights without anyone piloting large robotic machines.'),
      ('romance-no-school',['Romance'],['School'], 'Recommend a romance anime, but exclude school settings.', 'I want a love story that is not about students at school.'),
    ]
    queries=[];qrels={}
    for family,required,forbidden,literal,paraphrase in intents:
        for variant,text in [('literal',literal),('paraphrase',paraphrase)]:
            query=dict(id=family+'-'+variant,family=family,variant=variant,text=text,required=required,forbidden=forbidden)
            grades={}
            for row in catalog:
                genres=set(row['genres']);hits=len(genres&set(required))
                grade=0 if genres&set(forbidden) else 2 if hits==len(required) else 1 if hits else 0
                grades[row['id']]=grade
            assert sum(v==2 for v in grades.values())>=5,family
            queries.append(query);qrels[query['id']]=grades
    hashes={name:save(name,obj) for name,obj in [('catalog.json',catalog),('queries.json',queries),('qrels.json',qrels)]}
    manifest=dict(seed=SEED,raw_rows=len(raw),eligible=len(eligible),excluded=dict(excluded),catalog_size=len(catalog),queries=len(queries),intent_families=len(intents),language='English (source text; heuristic filtering, not independently certified)',document_word_limit=80,qrels_source='Publisher genre metadata; proxy relevance, no human preference labels',files_sha256=hashes)
    save('freeze.json',manifest);print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
