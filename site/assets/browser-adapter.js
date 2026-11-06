window.AniRecAdapter = (() => {
  let data, records = [], notes = {}, favorites = [], preferred = [], avoided = [], hidden = [], metadata = {}, idf, profileSnapshots=[], favoriteSnapshots=[];
  const neutralKeys=new Set();
  const byKey = new Map(), byAni = new Map(), publicKeys = new Set(),frozenByAni=new Map();
  const readJSON = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
  function merge(rows, preferPublic = false) {
    for (const row of rows) {
      const canonical = byAni.get(row.anilist_id), key = canonical?.key || row.key;
      if (key !== row.key && notes[row.key] !== undefined) { notes[key] = notes[row.key]; delete notes[row.key]; }
      if (preferPublic && publicKeys.has(key)) continue;
      const item = { ...row, key }; byKey.set(key, item); byAni.set(item.anilist_id, item);
    }
    records = [...byKey.values()]; idf = idf || data.topic_idf || window.AniRecIR.topicIdf(records.filter(item => !item.is_adult));
  }
  function persist() {
    localStorage.setItem('anirec-demo-notes', JSON.stringify(notes));
    localStorage.setItem('anirec-demo-preferences', JSON.stringify({ preferred: preferred.join(', '), avoided: avoided.join(', ') }));
    localStorage.setItem('anirec-demo-favorites', JSON.stringify(favorites)); localStorage.setItem('anirec-hidden', JSON.stringify(hidden));
  }
  function seenIds() {
    return metadata.seenIds || Object.keys(notes).map(key => byKey.get(key)?.anilist_id).filter(Boolean);
  }
  function referenceRecords(){return [...new Map([...data.records,...profileSnapshots,...favoriteSnapshots].map(row=>{const frozen=frozenByAni.get(row.anilist_id),key=frozen?.key||byAni.get(row.anilist_id)?.key||row.key;return [key,frozen||{...row,key}];})).values()];}
  function summary() {
    const state = window.AniRecIR.profile(referenceRecords(), notes, favorites, preferred);
    return { ...state.info, username: metadata.username || null, import_count: metadata.entries || Object.keys(notes).length,
      preferred, avoided, manual_favorites: favorites.map(key => byKey.get(key)).filter(Boolean),
      seen_count: new Set([...seenIds(), ...favorites.map(key => byKey.get(key)?.anilist_id)]).size,
      rejected: hidden.map(key => byKey.get(key)).filter(Boolean), truncated: false };
  }
  async function ensureRows(raws, progress, neutral=false) {
    const rows = await materializeAniRows(raws.filter(row => row && row.type === 'ANIME' && !row.isAdult), records, progress);
    merge(rows); if(neutral)rows.forEach(row=>neutralKeys.add(byAni.get(row.anilist_id).key)); return rows;
  }
  async function expansion(anchor, progress, pure=false) {
    if (!anchor.anilist_id) return;
    progress(pure?'Consultando obras relacionadas à referência…':'Consultando sugestões e candidatos ainda não iniciados…');
    const related = (await aniQuery('query($id:Int!){Media(id:$id,type:ANIME){recommendations(page:1,perPage:20,sort:RATING_DESC){nodes{mediaRecommendation{' + ANI_FIELDS + '}}}}}', { id: anchor.anilist_id })).Media.recommendations.nodes.map(n => n.mediaRecommendation).filter(Boolean);
    const genres = new Set(records.flatMap(item => item.genres).map(x => x.toLowerCase()));
    const tag = (pure?[]:preferred).find(name => !genres.has(name.toLowerCase())) || null;
    const excluded = [...new Set([anchor.anilist_id, ...(pure?[]:seenIds()), ...(pure?[]:favorites).map(key => byKey.get(key)?.anilist_id).filter(Boolean)])].slice(0, 10000);
    const found = (await aniQuery('query($genre:String,$tag:String,$excluded:[Int]){Page(page:1,perPage:50){media(type:ANIME,genre:$genre,tag:$tag,id_not_in:$excluded,status_not:NOT_YET_RELEASED,isAdult:false,sort:POPULARITY_DESC){' + ANI_FIELDS + '}}}', { genre: tag ? null : anchor.genres[0] || null, tag, excluded })).Page.media;
    await ensureRows([...new Map([...related, ...found].map(row => [row.id, row])).values()], progress, pure);
  }
  async function ensureProfileEncoding(progress){
    const cached=[...profileSnapshots,...favoriteSnapshots],stale=[...new Map(cached.filter(row=>!frozenByAni.has(row.anilist_id)&&row.text&&row.encoding_id!==data.encoding_id).map(row=>[row.anilist_id,row])).values()];
    if(!stale.length)return;
    progress('Atualizando vetores do histórico para o IDF deste snapshot…');
    const raw=stale.map(row=>({id:row.anilist_id,idMal:row.mal_id,type:'ANIME',isAdult:!!row.is_adult,title:{english:row.title,romaji:row.romaji},description:row.text,genres:row.genres,tags:row.tags,coverImage:{large:row.cover},siteUrl:row.url,status:row.status,averageScore:row.average_score,meanScore:row.mean_score,popularity:row.popularity,favourites:row.community_favourites}));
    const encoded=await materializeAniRows(raw,records,progress),old=new Map(stale.map(row=>[row.anilist_id,row]));
    for(const row of encoded){row.metadata_fetched_at=old.get(row.anilist_id).metadata_fetched_at;row.statistics_fetched_at=old.get(row.anilist_id).statistics_fetched_at;row.rating_count=old.get(row.anilist_id).rating_count;}
    merge(encoded);const map=new Map(encoded.map(row=>[row.anilist_id,row]));profileSnapshots=profileSnapshots.map(row=>map.get(row.anilist_id)||row);favoriteSnapshots=favoriteSnapshots.map(row=>map.get(row.anilist_id)||row);await saveImportedWorks(profileSnapshots);await writeBrowserValue('favorite-works',favoriteSnapshots);
  }
  return {
    async study(options){
      if(!options.pure)await ensureProfileEncoding(()=>{});
      const anchor=byKey.get(options.key);if(!anchor)throw Error('Escolha a referência novamente.');
      const rows=options.pure?records.filter(row=>neutralKeys.has(row.key)):records;
      const value=window.AniRecIR.study({...options,records:rows,profile_records:options.pure?[]:referenceRecords(),anchor,ratings:notes,favorites,preferred,avoided,seenIds:seenIds(),hidden,params:data.params,topic_idf:idf});
      if(!options.pure){const bytes=new TextEncoder().encode(JSON.stringify({notes,favorites,preferred,avoided}));value.profile_fingerprint=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');}
      value.encoding_id=data.encoding_id;return value;
    },
    async moreDiscoveries(anchor, progress) {
      for(const genre of (anchor.genres||[]).slice(0,2)) {
        progress('Buscando novos candidatos de '+genre+'…');
        const excluded=[...new Set([...seenIds(),...records.map(r=>r.anilist_id)])];
        const found=await aniQuery('query($genre:String,$excluded:[Int]){Page(page:1,perPage:50){media(type:ANIME,genre:$genre,id_not_in:$excluded,status_not:NOT_YET_RELEASED,isAdult:false,sort:POPULARITY_DESC){'+ANI_FIELDS+'}}}',{genre,excluded});
        await ensureRows(found.Page.media,progress);
      }
    },
    async init() {
      const response = await fetch('catalog.json',{cache:'no-cache'}); if (!response.ok) throw Error('Catálogo indisponível.'); data = await response.json(); window.AniRecEncodingId = data.encoding_id;
      notes = readJSON('anirec-demo-notes', {}); const prefs = readJSON('anirec-demo-preferences', {});
      preferred = (prefs.preferred || '').split(',').map(x => x.trim()).filter(Boolean); avoided = (prefs.avoided || '').split(',').map(x => x.trim()).filter(Boolean);
      favorites = readJSON('anirec-demo-favorites', []); hidden = readJSON('anirec-hidden', []);
      merge(data.records); for (const item of data.records){publicKeys.add(item.key);neutralKeys.add(item.key);frozenByAni.set(item.anilist_id,item);}
      try { metadata = await readBrowserValue('profile-meta') || {}; profileSnapshots=await restoreImportedWorks();favoriteSnapshots=await readBrowserValue('favorite-works') || [];merge(profileSnapshots,true);merge(favoriteSnapshots,true);profileSnapshots=profileSnapshots.map(row=>publicKeys.has(byAni.get(row.anilist_id)?.key)?byAni.get(row.anilist_id):row); } catch { metadata.storageWarning = true; }
    },
    async config() { return { mode: 'browser', profile: summary(), params: data.params, catalog_size: records.length }; },
    async taxonomy() { const response = await fetch('taxonomy.json'); if (!response.ok) throw Error('Taxonomia indisponível.'); return response.json(); },
    async popular() { const response = await fetch('popular.json'); return response.json(); },
    async search(query, online = true) {
      let matches = records.filter(item => (item.title + ' ' + item.romaji).toLowerCase().includes(query.toLowerCase())); let warning;
      if (online) try { const data = await aniQuery('query($search:String!){Page(page:1,perPage:5){media(search:$search,type:ANIME,isAdult:false){' + ANI_FIELDS + '}}}', { search: query }); const fresh = await ensureRows(data.Page.media, () => {}, true); matches = [...new Map([...fresh, ...matches].map(item => [item.key, item])).values()]; } catch (e) { warning = e.message; }
      return { items: matches.slice(0, 20), warning };
    },
    async saveOnboarding(selection, progress) {
      for (const item of selection.favorites) if (!byKey.has(item.key)) merge([item]);
      await writeBrowserValue('favorite-works', selection.favorites);favoriteSnapshots=selection.favorites.map(row=>({...row}));
      preferred = selection.preferred; avoided = selection.avoided; favorites = selection.favorites.map(item => item.key); persist();
      return summary();
    },
    async preferences(positive, negative) { preferred = positive; avoided = negative; persist(); return summary(); },
    async favorite(key, add) { favorites = favorites.filter(k => k !== key); if (add) favorites.push(key); favoriteSnapshots=favorites.map(k=>byKey.get(k)).filter(Boolean).map(row=>({...row}));await writeBrowserValue('favorite-works',favoriteSnapshots); persist(); return summary(); },
    async reject(key, add = true) { hidden = hidden.filter(k => k !== key); if (add) hidden.push(key); persist(); return summary(); },
    async importProfile(username, progress) {
      if (!/^[A-Za-z0-9_-]{1,50}$/.test(username)) throw Error('Informe um usuário AniList válido.');
      const imported = await importAniListProfile(username, records, progress);
      const meta = { username: imported.username, seenIds: imported.seenIds, entries: imported.entries, updated_at: new Date().toISOString() };
      await saveImportedWorks(imported.records); await writeBrowserValue('profile-meta', meta);
      merge(imported.records);profileSnapshots=imported.records.map(row=>({...row})); metadata = meta; notes = imported.notes; persist();
      progress(`${imported.entries} entradas · ${Object.keys(notes).length} obras com nota · ${imported.seenIds.length} vistas/iniciadas · ${imported.missing} registros indisponíveis.`);
      return summary();
    },
    async clearImport() { await saveImportedWorks([]); await writeBrowserValue('profile-meta', {}); notes = {}; metadata = {};profileSnapshots=[];persist(); return summary(); },
    async exportProfile() { return { format: 'anirec-browser-profile-v2', notes, favorites, preferred, avoided, metadata }; },
    async recommend(options, progress) {
      if(!options.pure)await ensureProfileEncoding(progress);
      const anchor = byKey.get(options.key); if (!anchor) throw Error('Pesquise novamente a obra.'); let warning;
      if (options.online) try { await expansion(anchor, progress,options.pure); } catch (e) { warning = 'A ampliação AniList falhou; usando o catálogo disponível. ' + e.message; }
      const result = window.AniRecIR.rank({ ...options, records:options.pure?records.filter(row=>neutralKeys.has(row.key)):records,profile_records:options.pure?[]:referenceRecords(), anchor, ratings: notes, favorites, preferred, avoided, seenIds: seenIds(), hidden, params: data.params, topic_idf: idf });
      if (warning) result.warning = warning; return result;
    },
    async dataset() { const response = await fetch('build-manifest.json'); const manifest = await response.json(); return { version: data.params.version, description: 'Metadados públicos AniList e vetores do mesmo snapshot da versão local. Seu perfil continua apenas neste navegador.', quality: { public_catalog: manifest.count, current_browser_catalog: records.length, works_with_notes: Object.keys(notes).length, known_started_ids: seenIds().length } }; }
  };
})();
