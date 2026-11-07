"""Small read-only AniList client: public data, bounded queries, no OAuth needed.

No mutations, no database mirroring. Cache is for a small recommendation
session; it is not an archival copy of the AniList catalog.
"""
import json,time,threading,urllib.request,urllib.error
URL='https://graphql.anilist.co'
MEDIA_FIELDS='''id idMal type status format seasonYear countryOfOrigin episodes duration startDate { year month day } title { romaji english } description(asHtml:false)
 genres tags { name rank isGeneralSpoiler isMediaSpoiler }
 coverImage { large } siteUrl averageScore meanScore popularity favourites stats { scoreDistribution { score amount } } isAdult'''
class AniListClient:
    def __init__(self):self.lock=threading.Lock();self.last=0.;self.cache={}
    def query(self,query,variables):
        if not query.lstrip().startswith('query'):raise ValueError('Only predefined read queries are supported.')
        cache_key=json.dumps([query,variables],sort_keys=True)
        if cache_key in self.cache:
            when,result=self.cache[cache_key]
            if time.monotonic()-when<3600:return result
        with self.lock:
            delay=max(0,2.2-(time.monotonic()-self.last))
            if delay:time.sleep(delay)
            payload=json.dumps(dict(query=query,variables=variables)).encode()
            for attempt in range(2):
                req=urllib.request.Request(URL,data=payload,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'TCC content recommender research/1.0'})
                try:
                    with urllib.request.urlopen(req,timeout=30) as response:result=json.load(response)
                    self.last=time.monotonic();break
                except urllib.error.HTTPError as error:
                    self.last=time.monotonic()
                    if error.code==429 and attempt==0:
                        wait=float(error.headers.get('Retry-After','30'))
                        if wait<=60:time.sleep(wait);continue
                    raise RuntimeError(f'AniList returned HTTP {error.code}. No repeated retry or paid fallback.') from None
            else:raise RuntimeError('AniList quota retry exhausted.')
        if result.get('errors'):raise RuntimeError('AniList GraphQL: '+'; '.join(str(e.get('message','Unknown error')) for e in result['errors']))
        if len(self.cache)>=200:self.cache.clear()
        self.cache[cache_key]=(time.monotonic(),result['data']);return result['data']
    def user(self,username):
        return self.query('''query($name:String!){ User(name:$name){ id name siteUrl statistics{anime{count meanScore minutesWatched tags(limit:1000,sort:COUNT_DESC){count meanScore minutesWatched tag{id name}} genres(limit:100,sort:COUNT_DESC){genre count meanScore minutesWatched}}} favourites { anime(page:1,perPage:50){ nodes { id } } } } }''',dict(name=username))['User']
    def taxonomy(self):
        data=self.query('''query { MediaTagCollection { id name description category isAdult } GenreCollection }''',{})
        return dict(tags=sorted(data['MediaTagCollection'],key=lambda t:t['name'].casefold()),genres=sorted(data['GenreCollection']),source=URL)
    def search(self,text):
        query='query($search:String!){ Page(page:1,perPage:5){ media(search:$search,type:ANIME,isAdult:false){ '+MEDIA_FIELDS+' } } }'
        return self.query(query,dict(search=text))['Page']['media']
    def media(self,media_id):
        return self.query('query($id:Int!){ Media(id:$id,type:ANIME){ '+MEDIA_FIELDS+' } }',dict(id=int(media_id)))['Media']
    def candidates(self,media_id):
        query='''query($id:Int!){ Media(id:$id,type:ANIME){ recommendations(page:1,perPage:20,sort:RATING_DESC){ nodes { mediaRecommendation { '''+MEDIA_FIELDS+''' } } } } }'''
        data=self.query(query,dict(id=int(media_id)))['Media']['recommendations']['nodes']
        return [r['mediaRecommendation'] for r in data if r.get('mediaRecommendation') and r['mediaRecommendation'].get('type')=='ANIME' and not r['mediaRecommendation'].get('isAdult')]
    def discover(self,genre,excluded_ids,tag=None):
        query='''query($genre:String,$excluded:[Int],$tag:String){ Page(page:1,perPage:50){ media(type:ANIME,genre:$genre,tag:$tag,id_not_in:$excluded,status_not:NOT_YET_RELEASED,isAdult:false,sort:POPULARITY_DESC){ '''+MEDIA_FIELDS+''' } } }'''
        return self.query(query,dict(genre=genre,excluded=sorted(set(excluded_ids))[:10000],tag=tag))['Page']['media']
    def public_list(self,username,max_chunks=None,metadata_limit=None,known_media=None,progress=None):
        """Read a user's list cheaply; enrich only the strongest profile signals.

        Collection chunks hold <=500 lightweight entries. Rich metadata is
        bounded, reused when recently imported, and never collected globally.
        """
        report=progress or (lambda **values:None)
        report(stage='Consultando usuário e favoritos',count=0)
        user=self.user(username);entries={};known_media=known_media or {}
        if not user:raise ValueError('User not found or not publicly accessible.')
        query='''query($id:Int!,$chunk:Int!){ MediaListCollection(userId:$id,type:ANIME,chunk:$chunk,perChunk:500){ hasNextChunk
 lists { entries { mediaId status score(format:POINT_100) progress repeat updatedAt media { id idMal } } } } }'''
        truncated=True
        chunk=0
        while True:
            chunk+=1
            result=self.query(query,dict(id=user['id'],chunk=chunk))['MediaListCollection']
            if result is None:raise ValueError('Lista não disponível publicamente.')
            rows=[row for group in result.get('lists') or [] for row in group.get('entries') or [] if row]
            before=len(entries)
            for row in rows:entries[row['mediaId']]=row
            if rows and len(entries)==before and result.get('hasNextChunk'):raise RuntimeError('Paginação sem progresso; perfil anterior mantido.')
            report(stage='Lendo itens da lista',count=len(entries),chunk=chunk)
            if not result.get('hasNextChunk') or not rows:truncated=False;break
        nodes=user['favourites']['anime']['nodes'];page=1
        while len(nodes)==50:
            page+=1
            nodes=self.query('query($id:Int!,$page:Int!){User(id:$id){favourites{anime(page:$page,perPage:50){nodes{id}}}}}',dict(id=user['id'],page=page))['User']['favourites']['anime']['nodes']
            known_ids={n['id'] for n in user['favourites']['anime']['nodes']}
            if nodes and all(n['id'] in known_ids for n in nodes):raise RuntimeError('Paginação de favoritos sem progresso.')
            user['favourites']['anime']['nodes'].extend(nodes)
        favorite_ids={x['id'] for x in ((user.get('favourites') or {}).get('anime') or {}).get('nodes',[])}
        eligible=list(entries.values())
        eligible.sort(key=lambda r:(r['mediaId'] in favorite_ids,float(r.get('score') or 0),r.get('updatedAt') or 0,r['mediaId']),reverse=True)
        selected=list(dict.fromkeys(sorted(favorite_ids)+[r['mediaId'] for r in eligible]))
        metadata={i:known_media[i] for i in selected if i in known_media and 'format' in known_media[i] and 'seasonYear' in known_media[i] and 'episodes' in known_media[i] and 'duration' in known_media[i]}
        missing=[i for i in selected if i not in metadata]
        for offset in range(0,len(missing),50):
            batch=missing[offset:offset+50]
            result=self.query('query($ids:[Int]){ Page(page:1,perPage:50){ media(type:ANIME,id_in:$ids){ '+MEDIA_FIELDS+' } } }',dict(ids=batch))['Page']['media']
            for row in result:metadata[row['id']]=row
            report(stage='Obtendo sinopses e temas de todas as obras da lista',count=len(entries),metadata_count=len(metadata),metadata_target=len(selected))
        for row in entries.values():
            if row['mediaId'] in metadata:row['media']=metadata[row['mediaId']]
        favorite_media=[metadata[i] for i in favorite_ids if i in metadata]
        return dict(user=user,entries=list(entries.values()),truncated=truncated,favorite_media=favorite_media,metadata_count=len(metadata),metadata_limit=metadata_limit)
