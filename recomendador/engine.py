"""Deterministic information retrieval with frozen Word2Vec Skip-gram vectors.

No fitting, gradients, classifiers, LLMs, or learned ranking weights.
"""
import collections,hashlib,html,json,math,os,re,threading,time,unicodedata,datetime,shutil
from pathlib import Path
import numpy as np
from anilist_client import AniListClient
from repository import Repository
from affinity import theme_affinity

WORK=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('ANIREC_DATA_DIR',str(Path.home()/'tcc-lab/recomendador-private')))
PARAMS=dict(version='ir-v7-guided-profile',model='Word2Vec Skip-gram text8 100d',document_words=None,synopsis_policy='entire_available_source',idf_policy='anilist_catalog_smooth',base_semantic=.5,base_topics=.5,topic_metric='idf_weighted_tag_cosine_85_genres_15',affinity_metric='positive_coverage_times_one_minus_negative_coverage',profile_semantic=.7,profile_topics=.3,personal_min_topics=.25,profile_text_policy='positive_negative_centroid_contrast',default_personalization=.35,max_personalization=.6,explicit_topic_weight=1.,max_history_topics=12,rating_neutral='user_observed_midrange',rating_policy='signed_user_midrange',import_limit=None,profile_metadata_limit=None,api_cache_seconds=3600)

def norm(text):return unicodedata.normalize('NFKC',str(text)).casefold().strip()
def clean(text):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',text or ''))).strip()
def tokenize(text):return re.findall(r'[^\W\d_]+',unicodedata.normalize('NFKC',text).casefold())
def unit(vector):
    length=np.linalg.norm(vector)
    return vector/length if length else vector
def topics(media,include_spoilers=False):
    result={norm(g):dict(name=g,weight=1.) for g in media.get('genres',[])}
    for tag in media.get('tags',[]):
        if not include_spoilers and (tag.get('isGeneralSpoiler') or tag.get('isMediaSpoiler')):continue
        result[norm(tag['name'])]=dict(name=tag['name'],weight=max(0,min(1,float(tag.get('rank',0))/100)))
    return result
def jaccard(a,b):return len(set(a)&set(b))/len(set(a)|set(b)) if a and b else 0.
def public(media):
    return {k:media.get(k) for k in ['key','title','romaji','text','genres','tags','cover','url','source','anilist_id','mal_id','status','synopsis_source','synopsis_complete']}

class Engine:
    def __init__(self,client=None,data_dir=None):
        from gensim.models import Word2Vec
        self.client=client or AniListClient();self.lock=threading.RLock();self.import_lock=threading.Lock();self.import_status=dict(active=False,stage='Aguardando importação')
        self.dir=Path(data_dir or DATA);self.dir.mkdir(parents=True,exist_ok=True)
        self.repository=Repository(self.dir/'anirec.sqlite3')
        self.profile_path=self.dir/'profile.json'
        self.profile=json.loads(self.profile_path.read_text(encoding='utf-8')) if self.profile_path.exists() else dict(username=None,entries=[],user=None,manual_favorites=[],preferred=[],avoided=[],rejected=[],updated_at=None,truncated=False)
        seed=json.loads((Path(__file__).parent/'data/anilist-seed.json').read_text(encoding='utf-8'))
        self.base_media={}
        self.repository.put_many('AniList',[(r['id'],r.get('idMal'),self.materialize(r)['title'],r,self.materialize(r)['text']) for r in seed])
        # Only AniList records enter the current application dataset.
        snapshot=self.dir/'catalog-snapshot.json'
        if snapshot.exists():
            records={r['id']:r for r in json.loads(snapshot.read_text(encoding='utf-8'))}
        else:
            records=self.repository.recent_anilist(days=36500)
            snapshot.write_text(json.dumps(list(records.values()),ensure_ascii=False),encoding='utf-8')
        mal_counts=collections.Counter(r.get('idMal') for r in records.values() if r.get('idMal'))
        self.key_by_anilist={r['id']:('anilist:'+str(r['id']) if not r.get('idMal') or mal_counts[r['idMal']]>1 else 'mal:'+str(r['idMal'])) for r in records.values()}
        catalog=[self.materialize(r) for _,r in sorted(records.items()) if r.get('type','ANIME')=='ANIME' and not r.get('isAdult')]
        frequencies=collections.Counter(word for item in catalog for word in set(tokenize(item['text'])))
        self.idf={word:math.log((1+len(catalog))/(1+count))+1 for word,count in frequencies.items()}
        self.unseen=math.log(1+len(catalog))+1
        topic_df=collections.Counter(t for item in catalog for t in topics(item,True))
        self.topic_idf={t:math.log((len(catalog)+1)/(count+1))+1 for t,count in topic_df.items()}
        model_path=Path(os.environ.get('ANIREC_WORD2VEC_PATH',str(Path.home()/'tcc-lab/Word2Vec/models/text8-skipgram-100d.model')))
        if model_path.exists():self.words=Word2Vec.load(str(model_path)).wv
        else:
            from gensim.models import KeyedVectors
            exported=Path(__file__).parent/'online'
            manifest=json.loads((exported/'model-manifest.json').read_text(encoding='utf-8'))
            vocabulary=json.loads((exported/'vocabulary.json').read_text(encoding='utf-8'))
            matrix=np.concatenate([np.frombuffer((exported/s['file']).read_bytes(),dtype='<f4').reshape(s['count'],manifest['dimensions']) for s in manifest['shards']])
            self.words=KeyedVectors(vector_size=manifest['dimensions']);self.words.add_vectors(vocabulary,matrix)
        self.media={};self.base_vectors={};self.vector_cache={};self.expansion={};self.live_media=collections.OrderedDict();self.profile_media={}
        for item in catalog:
            self.media[item['key']]=item;self.base_vectors[(item['key'],item['text'])]=self.vector(item)
        self.discovery_extra={}
        self.base_keys=set(self.media)
        self.base_media={key:item.copy() for key,item in self.media.items()}
        self.restore_profile_media()

    def prune(self):
        for key,(_,deadline) in list(self.live_media.items()):
            if time.monotonic()>deadline:self.live_media.pop(key,None)
        self.media={**self.base_media,**self.profile_media,**{key:item for key,(item,_) in self.live_media.items()}}

    def restore_profile_media(self):
        self.profile_media={}
        for entry in self.profile.get('entries',[]):
            if (entry.get('media') or {}).get('title'):
                item=self.materialize(entry['media']);self.profile_media[item['key']]=item
        for row in self.profile.get('favorite_media',[]):
            item=self.materialize(row);self.profile_media[item['key']]=item
        for item in self.profile.get('manual_favorites',[]):self.profile_media[item['key']]=item
        self.prune()

    def key_for(self,row):
        return getattr(self,'key_by_anilist',{}).get(row.get('id'),'mal:'+str(row['idMal']) if row.get('idMal') else 'anilist:'+str(row['id']))

    def materialize(self,row):
        title=row.get('title') or {};text=clean(row.get('description'))
        key=self.key_for(row)
        previous=self.base_media.get(key,{})
        item=dict(key=key,mal_id=row.get('idMal'),anilist_id=row['id'],title=title.get('english') or title.get('romaji') or str(row['id']),romaji=title.get('romaji') or '',text=text or previous.get('text',''),synopsis_source='AniList description' if text else previous.get('synopsis_source'),synopsis_complete=True if text else previous.get('synopsis_complete',False),genres=row.get('genres') or [],tags=row.get('tags') or [],cover=(row.get('coverImage') or {}).get('large'),url=row.get('siteUrl'),source='AniList (consulta sob demanda)',status=row.get('status'),media_type=row.get('type','ANIME'))
        return item

    def add_anilist(self,row):
        item=self.materialize(row);key=item['key']
        self.repository.put_many('AniList',[(row['id'],row.get('idMal'),item['title'],row,item['text'])])
        self.live_media[key]=(item,time.monotonic()+3600);self.live_media.move_to_end(key)
        while len(self.live_media)>200:self.live_media.popitem(last=False)
        self.prune();return item

    def vector(self,item):
        text=item.get('text','');cache_key=(item['key'],text)
        if cache_key in self.base_vectors:return self.base_vectors[cache_key]
        if cache_key in self.vector_cache:return self.vector_cache[cache_key]
        values=[];weights=[]
        for word in tokenize(text):
            if word in self.words:values.append(self.words[word]);weights.append(self.idf.get(word,self.unseen))
        value=unit(np.average(values,axis=0,weights=weights)) if values else np.zeros(100)
        if len(self.vector_cache)>2500:self.vector_cache.clear()
        self.vector_cache[cache_key]=np.asarray(value,dtype=np.float32)
        return self.vector_cache[cache_key]

    def thematic_similarity(self,a,b):
        def features(item):
            return {norm(t['name']):max(0,min(1,float(t.get('rank') or 0)/100))*self.topic_idf.get(norm(t['name']),1.) for t in item.get('tags',[]) if float(t.get('rank') or 0)>=50}
        av=features(a);bv=features(b)
        denominator=math.sqrt(sum(v*v for v in av.values())*sum(v*v for v in bv.values()))
        tag_cos=sum(v*bv.get(t,0) for t,v in av.items())/denominator if denominator else 0.
        genre=jaccard(a.get('genres',[]),b.get('genres',[]))
        return .85*tag_cos+.15*genre,tag_cos,genre

    def text_quality(self,item):
        words=tokenize(item.get('text',''))
        known=sum(word in self.words for word in words)
        return dict(word_count=len(words),known_words=known,unknown_words=len(words)-known,
                    vocabulary_coverage=known/len(words) if words else 0.,
                    has_tags=bool(item.get('tags')),has_genres=bool(item.get('genres')),
                    has_status=bool(item.get('status')),synopsis_source=item.get('synopsis_source'),synopsis_complete=item.get('synopsis_complete',False))

    def save(self):
        self.profile['updated_at']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
        if self.profile_path.exists():shutil.copy2(self.profile_path,self.dir/'profile.previous.json')
        temp=self.profile_path.with_suffix('.tmp');temp.write_text(json.dumps(self.profile,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(self.profile_path)

    def search(self,text,online=True):
        text=text.strip()
        if not 2<=len(text)<=100:raise ValueError('Digite entre 2 e 100 caracteres.')
        with self.lock:
            self.prune()
            local=[m for m in self.media.values() if norm(text) in norm(m['title']) or norm(text) in norm(m.get('romaji',''))]
        warning=None;remote=[]
        if online:
            try:
                rows=self.client.search(text)
                with self.lock:remote=[self.add_anilist(row) for row in rows]
            except (RuntimeError,OSError,ValueError) as error:warning=str(error)
        unique={m['key']:m for m in remote+local}
        return dict(items=[public(m) for m in list(unique.values())[:12]],warning=warning)

    def import_profile(self,username):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,50}',username):raise ValueError('Nome de usuário inválido.')
        if not self.import_lock.acquire(blocking=False):raise ValueError('Já existe uma importação em andamento.')
        def progress(**values):self.import_status=dict(active=True,**values)
        try:
            known=self.repository.recent_anilist()
            with self.lock:
                try:recent=time.time()-datetime.datetime.fromisoformat(self.profile.get('updated_at') or '').timestamp()<3600
                except ValueError:recent=False
                if recent and norm(username)==norm(self.profile.get('username') or ''):
                    known.update({e['mediaId']:e['media'] for e in self.profile.get('entries',[]) if (e.get('media') or {}).get('title')})
            imported=self.client.public_list(username,max_chunks=None,metadata_limit=None,known_media=known,progress=progress)
            if not imported['entries']:raise ValueError('Nenhum item público visível. O perfil anterior foi mantido.')
            rich={r['media']['id']:r['media'] for r in imported['entries'] if (r.get('media') or {}).get('title')}
            rich.update({r['id']:r for r in imported['favorite_media']})
            self.repository.put_many('AniList',[(r['id'],r.get('idMal'),self.materialize(r)['title'],r,self.materialize(r)['text']) for r in rich.values()])
            with self.lock:
                self.profile.update(username=imported['user']['name'],user=imported['user'],entries=imported['entries'],favorite_media=imported['favorite_media'],metadata_count=imported['metadata_count'],truncated=imported['truncated'])
                self.restore_profile_media();self.save();result=self.summary()
            self.import_status=dict(active=False,stage='Importação concluída',count=len(imported['entries']));return result
        except Exception:
            self.import_status=dict(active=False,stage='Importação não concluída; perfil anterior preservado');raise
        finally:self.import_lock.release()

    def profile_signals(self):
        favorite_ids={x['id'] for x in (((self.profile.get('user') or {}).get('favourites') or {}).get('anime') or {}).get('nodes',[])}
        observed=[min(float(e.get('score') or 0),100) for e in self.profile.get('entries',[]) if float(e.get('score') or 0)>0]
        minimum=min(observed) if observed else None;maximum=max(observed) if observed else None
        neutral=(minimum+maximum)/2 if observed else None
        half_range=(maximum-minimum)/2 if observed else 0.
        rated_keys={self.key_for(e['media']) for e in self.profile.get('entries',[]) if float(e.get('score') or 0)>0 and e.get('media')}
        weighted={};seen=set();rated_count=0;neutral_count=0;missing_rated=0
        for entry in self.profile.get('entries',[]):
            row=entry.get('media')
            if not row:continue
            key=self.key_for(row)
            if entry.get('status') in ['COMPLETED','CURRENT','REPEATING','DROPPED','PAUSED']:seen.add(key)
            score=float(entry.get('score') or 0)
            if score>0:rated_count+=1;neutral_count+=int(score==neutral)
            weight=(min(score,100)-neutral)/half_range if score>0 and half_range>0 else 0. if score>0 else 2. if row['id'] in favorite_ids else 0.
            if weight!=0:weighted[key]=weight
            if score>0 and key not in self.profile_media and key not in self.base_media:missing_rated+=1
        for row in self.profile.get('favorite_media',[]):
            key=self.key_for(row)
            if key not in rated_keys:weighted[key]=2.
            seen.add(key)
        for media in self.profile.get('manual_favorites',[]):
            if media['key'] not in rated_keys:weighted[media['key']]=2.
            seen.add(media['key'])
        positives=[];weights=[];theme_weights=collections.Counter();theme_names={}
        for key,weight in weighted.items():
            # The profile depends on its saved snapshot, never on browsing/cache history.
            item=self.profile_media.get(key) or self.base_media.get(key)
            if item is None:continue
            v=self.vector(item)
            if np.linalg.norm(v):positives.append(v);weights.append(weight)
            for topic,meta in topics(item).items():theme_weights[topic]+=weight*meta['weight'];theme_names[topic]=meta['name']
        total=sum(abs(weight) for key,weight in weighted.items() if key in self.profile_media or key in self.base_media) or 1
        inferred={t:dict(name=theme_names[t],weight=float(w/total),source='histórico: aproximação' if w>0 else 'histórico: afastamento') for t,w in sorted(theme_weights.items(),key=lambda x:(-abs(x[1]),x[0]))[:12]}
        combined={t:meta.copy() for t,meta in inferred.items()}
        for t in self.profile.get('preferred',[]):combined[norm(t)]=dict(name=t,weight=1.,source='preferência explícita')
        self.profile_centroids=dict(positive=unit(sum((v*w for v,w in zip(positives,weights) if w>0),np.zeros(100))) if any(w>0 for w in weights) else None,negative=unit(sum((v*abs(w) for v,w in zip(positives,weights) if w<0),np.zeros(100))) if any(w<0 for w in weights) else None)
        profile_vector=unit(np.sum(np.asarray(positives)*np.asarray(weights)[:,None],axis=0)) if positives else None
        if profile_vector is not None and not np.linalg.norm(profile_vector):profile_vector=None
        return profile_vector,combined,seen,dict(rating_min=minimum,rating_max=maximum,rating_neutral=neutral,rating_scale_informative=bool(half_range),positive_count=sum(w>0 for w in weighted.values()),negative_count=sum(w<0 for w in weighted.values()),rated_count=rated_count,neutral_count=neutral_count,missing_rated_metadata=missing_rated,vector_count=len(positives),inferred=list(inferred.values()))

    def summary(self):
        with self.lock:
            _,_,seen,info=self.profile_signals()
            return dict(username=self.profile.get('username'),import_count=len(self.profile.get('entries',[])),truncated=self.profile.get('truncated',False),updated_at=self.profile.get('updated_at'),preferred=self.profile.get('preferred',[]),avoided=self.profile.get('avoided',[]),manual_favorites=[public(m) for m in self.profile.get('manual_favorites',[])],rejected_count=len(self.profile.get('rejected',[])),rejected=[public(self.media[k]) for k in self.profile.get('rejected',[]) if k in self.media],seen_count=len(seen),metadata_count=self.profile.get('metadata_count'),**info)

    def preferences(self,preferred,avoided):
        def valid(values):
            if not isinstance(values,list) or len(values)>30:raise ValueError('Use até 30 temas.')
            return list(dict.fromkeys(clean(str(v))[:80] for v in values if clean(str(v))))
        with self.lock:
            self.profile['preferred']=valid(preferred);self.profile['avoided']=valid(avoided);self.save();return self.summary()

    def onboarding(self,preferred,avoided,favorite_keys):
        if not isinstance(favorite_keys,list) or len(favorite_keys)>30:raise ValueError('Use até 30 favoritos.')
        with self.lock:
            if any(key not in self.media for key in favorite_keys):raise ValueError('Pesquise novamente o favorito que expirou do cache.')
            for values in (preferred,avoided):
                if not isinstance(values,list) or len(values)>30:raise ValueError('Use até 30 preferências.')
            self.profile['preferred']=list(dict.fromkeys(clean(str(t))[:80] for t in preferred if clean(str(t))))
            self.profile['avoided']=list(dict.fromkeys(clean(str(t))[:80] for t in avoided if clean(str(t))))
            self.profile['manual_favorites']=[self.media[key].copy() for key in dict.fromkeys(favorite_keys)]
            self.restore_profile_media();self.save();return self.summary()

    def favorite(self,key,add=True):
        with self.lock:
            if key not in self.media:raise ValueError('Anime não encontrado; pesquise novamente.')
            favorites=[m for m in self.profile.get('manual_favorites',[]) if m['key']!=key]
            if add:
                if len(favorites)>=30:raise ValueError('Limite de 30 favoritos manuais nesta versão.')
                favorites.append(self.media[key])
            self.profile['manual_favorites']=favorites;self.restore_profile_media();self.save();return self.summary()

    def reject(self,key,add=True):
        with self.lock:
            if key not in self.media:raise ValueError('Anime não encontrado.')
            current=set(self.profile.get('rejected',[]))
            if add:current.add(key)
            else:current.discard(key)
            self.profile['rejected']=sorted(current);self.save();return self.summary()

    def clear_import(self):
        with self.lock:
            self.profile.update(username=None,user=None,entries=[],favorite_media=[],metadata_count=0,truncated=False);self.restore_profile_media();self.save();return self.summary()

    def recommend(self,key,personalization=.35,exclude_seen=False,online=True,require_genre=False,exclude_upcoming=True,require_tag_metadata=False,personal_min_topics=.25,pure=False):
        if pure:personalization=0.;exclude_seen=False
        if not math.isfinite(float(personalization)):raise ValueError('Peso de personalização inválido.')
        if not math.isfinite(float(personal_min_topics)) or not 0<=float(personal_min_topics)<=1:raise ValueError('Proximidade temática deve estar entre 0 e 1.')
        start=time.perf_counter();warning=None
        with self.lock:
            self.prune()
            if key not in self.media:raise ValueError('Selecione um anime da busca.')
            anchor=self.media[key].copy()
            if key in self.live_media:self.live_media.move_to_end(key)
        related=[];discovered=[]
        if online and anchor.get('anilist_id'):
            try:related=self.client.candidates(anchor['anilist_id'])
            except (RuntimeError,OSError,ValueError) as error:warning=str(error)
        if online and anchor.get('genres') and hasattr(self.client,'discover'):
            excluded=[anchor['anilist_id']] if anchor.get('anilist_id') else []
            if exclude_seen:
                excluded.extend(e['mediaId'] for e in self.profile.get('entries',[]) if e.get('status') in ['COMPLETED','CURRENT','REPEATING','DROPPED','PAUSED'])
                excluded.extend(m['anilist_id'] for m in self.profile.get('manual_favorites',[]) if m.get('anilist_id'))
            try:discovered=self.client.discover(anchor['genres'][0],excluded)
            except (RuntimeError,OSError,ValueError) as error:warning=str(error)
        # A dedicated discovery query does not discard seen works from the general list.
        if online and not pure and hasattr(self.client,'discover'):
            known_ids=[e['mediaId'] for e in self.profile.get('entries',[]) if e.get('status') in ['COMPLETED','CURRENT','REPEATING','DROPPED','PAUSED']]
            known_ids.extend(m['anilist_id'] for m in self.profile.get('manual_favorites',[]) if m.get('anilist_id'))
            if known_ids and not exclude_seen:
                known_genres={norm(g) for item in self.base_media.values() for g in item.get('genres',[])}
                desired_tag=next((t for t in self.profile.get('preferred',[]) if norm(t) not in known_genres),None)
                try:discovered.extend(self.client.discover(None if desired_tag else (anchor.get('genres') or [None])[0],known_ids+([anchor['anilist_id']] if anchor.get('anilist_id') else []),tag=desired_tag))
                except (RuntimeError,OSError,ValueError) as error:warning=str(error)
        local_start=time.perf_counter()
        with self.lock:
            related_items=[self.add_anilist(row) for row in related]
            discovery_items=[self.add_anilist(row) for row in discovered]
            cached=self.expansion.get(key)
            if related_items:self.expansion[key]=(time.monotonic(),[m['key'] for m in related_items])
            elif cached and time.monotonic()-cached[0]<3600:related_items=[self.media[k] for k in cached[1] if k in self.media]
            # A common candidate pool for both modes; the imported history does not silently expand it.
            candidate_keys=self.base_keys|{m['key'] for m in related_items+discovery_items}|(set(self.discovery_extra.get(key,[]))&set(self.media) if not pure else set())
            anchor_vector=self.vector(anchor)
            if not np.linalg.norm(anchor_vector):raise ValueError('A sinopse não forneceu termos com vetores utilizáveis. Escolha outro anime.')
            if pure:profile=None;preference={};seen=set();info={};active=False
            else:
                profile,preference,seen,info=self.profile_signals();active=any(v is not None for v in self.profile_centroids.values()) or bool(preference)
            lam=max(0,min(.6,float(personalization))) if active else 0.
            forbidden=set() if pure else {norm(t) for t in self.profile.get('avoided',[])}
            excluded={key}|(set(self.profile.get('rejected',[])) if not pure else set())|(seen if exclude_seen else set())
            audit=collections.Counter();diagnostics=[]
            def reject(item,reason,detail=None):
                audit[reason]+=1;diagnostics.append(dict(key=item['key'],title=item['title'],reason=reason,detail=detail))
            anchor_topics=topics(anchor);rows=[];skipped=0;excluded_by_topic=0;excluded_unknown=0;semantic_start=time.perf_counter()
            denominator=sum(abs(x['weight']) for x in preference.values()) or 1
            for candidate_key in sorted(candidate_keys):
                item=self.media[candidate_key];item_topics=topics(item,True);explain_topics=topics(item)
                if candidate_key in excluded:
                    reject(item,'anchor' if candidate_key==key else 'hidden' if candidate_key in self.profile.get('rejected',[]) else 'seen');continue
                if item.get('media_type','ANIME')!='ANIME':reject(item,'not_anime');continue
                if exclude_upcoming and item.get('status')=='NOT_YET_RELEASED':reject(item,'upcoming');continue
                if require_genre and anchor.get('genres') and not set(anchor['genres'])&set(item['genres']):reject(item,'genre');continue
                # Explicit exclusions must also match spoiler-marked metadata;
                # hiding a tag in explanations must not bypass a requested filter.
                exclusion_topics=set(item_topics)|{norm(t['name']) for t in item.get('tags',[])}
                if forbidden&exclusion_topics:
                    excluded_by_topic+=1;reject(item,'avoided_topic',sorted(forbidden&exclusion_topics));continue
                if forbidden and require_tag_metadata and not item.get('tags'):
                    excluded_unknown+=1;reject(item,'missing_tags');continue
                vector=self.vector(item)
                if not np.linalg.norm(vector):skipped+=1;reject(item,'missing_vector');continue
                cosine=float(np.clip(np.dot(anchor_vector,vector),-1,1));topic,tag_cos,genre_overlap=self.thematic_similarity(anchor,item)
                base=.5*((cosine+1)/2)+.5*topic
                affinity_details=theme_affinity(preference,item_topics);affinity=affinity_details['score']
                profile_cos=float(np.clip(np.dot(profile,vector),-1,1)) if profile is not None else None
                pos=None if pure else self.profile_centroids['positive'];neg=None if pure else self.profile_centroids['negative']
                pos_cos=float(np.clip(np.dot(pos,vector),-1,1)) if pos is not None else None
                neg_cos=float(np.clip(np.dot(neg,vector),-1,1)) if neg is not None else None
                profile_text=float(np.clip(.5+.5*(pos_cos-neg_cos),0,1)) if pos_cos is not None and neg_cos is not None else (pos_cos+1)/2 if pos_cos is not None else (1-neg_cos)/2 if neg_cos is not None else None
                personalized=.7*profile_text+.3*affinity if profile_text is not None else affinity
                score=(1-lam)*base+lam*personalized
                common=[v['name'] for t,v in explain_topics.items() if t in anchor_topics]
                matched=[dict(name=p['name'],source=p['source']) for t,p in preference.items() if t in item_topics]
                contributions=dict(anchor_text=(1-lam)*.5*((cosine+1)/2),anchor_topics=(1-lam)*.5*topic,profile_text=lam*.7*profile_text if profile_text is not None else 0.,profile_topics=lam*.3*affinity if profile_text is not None else lam*affinity)
                rows.append(dict(**public(item),quality=self.text_quality(item),contributions=contributions,base_score=base,personalized_score=score,anchor_cosine=cosine,anchor_topic_overlap=topic,anchor_tag_cosine=tag_cos,anchor_genre_overlap=genre_overlap,profile_cosine=profile_cos,positive_profile_cosine=pos_cos,negative_profile_cosine=neg_cos,profile_text_score=profile_text,preference_affinity=affinity,affinity_details=affinity_details,is_seen=candidate_key in seen,common_topics=common[:8],matched_preferences=matched[:8]))
            general=sorted(rows,key=lambda r:(-r['base_score'],r['key']))
            personal_candidates=[r for r in rows if not active or lam==0 or r['anchor_topic_overlap']>=personal_min_topics]
            personal=sorted(personal_candidates,key=lambda r:(-r['personalized_score'],r['key']))
            recommendation_sets=dict(general_all=general[:10],general_unseen=[r for r in general if not r['is_seen']][:10],personal_all=personal[:10],personal_unseen=[r for r in personal if not r['is_seen']][:10])
            general_rank={r['key']:i+1 for i,r in enumerate(general)};personal_rank={r['key']:i+1 for i,r in enumerate(personal)}
            diagnostics.extend(dict(key=r['key'],title=r['title'],reason='eligible',general_rank=general_rank[r['key']],personal_rank=personal_rank.get(r['key']),personal_exclusion=None if r['key'] in personal_rank else 'below_personal_anchor_theme_threshold') for r in rows)
            audit['eligible']=len(rows)
            coverage=dict(total=len(candidate_keys),with_text=sum(bool(self.media[k].get('text')) for k in candidate_keys),with_tags=sum(bool(self.media[k].get('tags')) for k in candidate_keys),with_genres=sum(bool(self.media[k].get('genres')) for k in candidate_keys),with_status=sum(bool(self.media[k].get('status')) for k in candidate_keys))
            return dict(recommendation_sets=recommendation_sets,unseen_count=sum(not r['is_seen'] for r in general),personal_unseen_count=sum(not r['is_seen'] for r in personal),filter_audit=dict(audit),diagnostics=diagnostics,anchor=public(anchor),anchor_quality=self.text_quality(anchor),metadata_coverage=coverage,general=general,personalized=personal,profile_active=active,personalization=lam,candidate_count=len(candidate_keys),eligible_count=len(rows),personal_eligible_count=len(personal_candidates),related_count=len(related_items),discovery_count=len(discovery_items),base_count=len(self.base_keys),skipped_no_vector=skipped,ranking_ms=(time.perf_counter()-local_start)*1000,scoring_ms=(time.perf_counter()-semantic_start)*1000,total_ms=(time.perf_counter()-start)*1000,warning=warning,profile_info=info,params=PARAMS,filters=dict(pure=pure,exclude_seen=exclude_seen,require_genre=require_genre,exclude_upcoming=exclude_upcoming,require_tag_metadata=require_tag_metadata,personal_min_topics=personal_min_topics),excluded_by_topic=excluded_by_topic,excluded_unknown_tags=excluded_unknown,limitations=['Metadados ausentes não comprovam ausência de um tema ou lançamento.','AniList amplia o pool com até 20 sugestões comunitárias e 50 itens do primeiro gênero da âncora; nosso motor calcula a ordem.','Score é relativo, não probabilidade de gostar.'])
