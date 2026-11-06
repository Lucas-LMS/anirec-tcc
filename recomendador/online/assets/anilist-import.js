'use strict';
let frozenEncoder = null, apiLast = 0, apiQueue = Promise.resolve();
const apiCache = new Map(), wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const ANI_FIELDS = 'id idMal type status format seasonYear countryOfOrigin title{english romaji} description(asHtml:false) genres tags{name rank isGeneralSpoiler isMediaSpoiler} coverImage{large} siteUrl averageScore meanScore popularity favourites stats{scoreDistribution{score amount}} isAdult';
function aniQuery(query, variables) {
  const cacheKey = JSON.stringify([query, variables]), cached = apiCache.get(cacheKey);
  if (cached && Date.now() - cached.at < 3600000) return Promise.resolve(cached.data);
  const task = apiQueue.then(async () => {
    await wait(Math.max(0, 2200 - (Date.now() - apiLast)));
    for (let attempt = 0; attempt < 2; attempt++) {
      const response = await fetch('https://graphql.anilist.co', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ query, variables }) }); apiLast = Date.now();
      if (response.status === 429 && attempt === 0) { const seconds = Number(response.headers.get('Retry-After') || 60); if (seconds <= 60) { await wait(seconds * 1000); continue; } }
      if (!response.ok) throw Error('AniList HTTP ' + response.status + '. Tente mais tarde.');
      const result = await response.json(); if (result.errors) throw Error(result.errors.map(e => e.message).join('; '));
      apiCache.set(cacheKey, { at: Date.now(), data: result.data }); return result.data;
    }
    throw Error('Limite temporário do AniList.');
  });
  apiQueue = task.catch(() => {}); return task;
}
async function loadFrozenEncoder(progress = () => {}) {
  if (frozenEncoder) return frozenEncoder;
  progress('Carregando o vocabulário estático para novas sinopses (primeira vez: cerca de 30 MB)…');
  const [manifest, vocabulary, idf] = await Promise.all(['model-manifest.json', 'vocabulary.json', 'idf.json'].map(async file => { const response = await fetch(file,{cache:'no-cache'}); if (!response.ok) throw Error('Modelo estático indisponível.'); return response.json(); }));
  if(idf.corpus_id!==window.AniRecEncodingId)throw Error('Modelo e catálogo de versões diferentes. Recarregue a página.');
  const shards = [];
  for (const [i, part] of manifest.shards.entries()) { progress(`Carregando vetores fixos: ${i + 1}/${manifest.shards.length} blocos…`); const response = await fetch(part.file); if (!response.ok) throw Error('Não foi possível carregar os vetores.'); const buffer = await response.arrayBuffer(); if (buffer.byteLength !== part.bytes) throw Error('Bloco incompleto.'); shards.push({ start: part.start, end: part.start + part.count, values: new Float32Array(buffer) }); }
  frozenEncoder = { manifest, index: new Map(vocabulary.map((word, i) => [word, i])), shards, idf }; return frozenEncoder;
}
function encodeFullSynopsis(text, model) {
  const words = text.normalize('NFKC').toLowerCase().match(/\p{L}+/gu) || [], vector = Array(100).fill(0);
  for (const word of words) { const index = model.index.get(word); if (index === undefined) continue; const part = model.shards.find(p => index >= p.start && index < p.end), offset = (index - part.start) * 100, weight = model.idf.idf[word] ?? model.idf.unseen; for (let i = 0; i < 100; i++) vector[i] += weight * part.values[offset + i]; }
  return window.AniRecIR.unit(vector).map(Math.fround);
}
function cleanAniText(value) { return (new DOMParser().parseFromString(value || '', 'text/html').body.textContent || '').replace(/\s+/g, ' ').trim(); }
async function materializeAniRows(raws, existing, progress) {
  const byAni = new Map(existing.map(item => [item.anilist_id, item])), records = []; let encoder;
  for (const raw of raws) {
    const old = byAni.get(raw.id), text = cleanAniText(raw.description), sameText = old && old.text === text && old.vector && old.encoding_id === window.AniRecEncodingId;
    if (!sameText && !encoder) encoder = await loadFrozenEncoder(progress);
    records.push({ key: old?.key || 'anilist:' + raw.id, anilist_id: raw.id, mal_id: raw.idMal, title: raw.title.english || raw.title.romaji,
      romaji: raw.title.romaji, text, genres: raw.genres || [], tags: raw.tags || [], cover: raw.coverImage?.large, url: raw.siteUrl,
      statistics_fetched_at: new Date().toISOString(), average_score: raw.averageScore ?? null, mean_score: raw.meanScore ?? null, popularity: raw.popularity ?? null, community_favourites: raw.favourites ?? null, rating_count: raw.stats?.scoreDistribution?.reduce((sum,row)=>sum+row.amount,0) ?? null, status: raw.status, is_adult: !!raw.isAdult, source: 'AniList · consulta pública', synopsis_source: 'AniList description', synopsis_complete: true,
      encoding_id: window.AniRecEncodingId, metadata_fetched_at: new Date().toISOString(), vector: sameText ? old.vector : encodeFullSynopsis(text, encoder) });
  }
  return records;
}
async function importAniListProfile(username, existing, progress) {
  const user = (await aniQuery('query($name:String!){User(name:$name){id name}}', { name: username })).User;
  if (!user) throw Error('Usuário não encontrado.'); const entries = new Map(); let chunk = 0;
  while (true) { chunk++; progress(`Lendo lista pública: bloco ${chunk}, ${entries.size} itens…`); const result = (await aniQuery('query($id:Int!,$chunk:Int!){MediaListCollection(userId:$id,type:ANIME,chunk:$chunk,perChunk:500){hasNextChunk lists{entries{mediaId score(format:POINT_100) status}}}}', { id: user.id, chunk })).MediaListCollection; if (!result) throw Error('Lista não disponível publicamente.'); const before = entries.size; for (const group of result.lists || []) for (const entry of group.entries || []) entries.set(entry.mediaId, entry); if (!result.hasNextChunk) break; if (before === entries.size) throw Error('Paginação sem progresso.'); }
  const rated = [...entries.values()].filter(e => e.score > 0), metadata = new Map(), byAni = new Map(existing.map(item => [item.anilist_id, item]));
  for (const entry of rated) { const cached = byAni.get(entry.mediaId); if (cached?.encoding_id === window.AniRecEncodingId && cached?.metadata_fetched_at && Date.now() - Date.parse(cached.metadata_fetched_at) < 7 * 86400000) metadata.set(entry.mediaId, cached); }
  const missingIds = rated.map(e => e.mediaId).filter(id => !metadata.has(id)), fresh = [];
  for (let start = 0; start < missingIds.length; start += 50) { progress(`Atualizando metadados: ${metadata.size + Math.min(start + 50, missingIds.length)}/${rated.length} obras com nota…`); const data = await aniQuery('query($ids:[Int]){Page(page:1,perPage:50){media(type:ANIME,id_in:$ids){' + ANI_FIELDS + '}}}', { ids: missingIds.slice(start, start + 50) }); fresh.push(...data.Page.media); }
  for (const row of await materializeAniRows(fresh, existing, progress)) metadata.set(row.anilist_id, row);
  const records = [], notes = {}; let missing = 0;
  for (const entry of rated) { const row = metadata.get(entry.mediaId); if (!row) { missing++; continue; } records.push(row); notes[row.key] = entry.score / 10; }
  const seenIds = [...entries.values()].filter(e => ['COMPLETED', 'CURRENT', 'REPEATING', 'DROPPED', 'PAUSED'].includes(e.status)).map(e => e.mediaId);
  return { records, notes, missing, entries: entries.size, seenIds, username: user.name };
}
async function browserDatabase() { return new Promise((resolve, reject) => { const request = indexedDB.open('anirec-private-browser', 1); request.onupgradeneeded = () => request.result.createObjectStore('imports'); request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error); }); }
async function writeBrowserValue(key, value) { const db = await browserDatabase(); return new Promise((resolve, reject) => { const tx = db.transaction('imports', 'readwrite'); tx.objectStore('imports').put(value, key); tx.oncomplete = () => { db.close(); resolve(); }; tx.onerror = () => { db.close(); reject(tx.error); }; }); }
async function readBrowserValue(key) { const db = await browserDatabase(); return new Promise((resolve, reject) => { const tx = db.transaction('imports', 'readonly'), request = tx.objectStore('imports').get(key); request.onsuccess = () => { db.close(); resolve(request.result); }; request.onerror = () => { db.close(); reject(request.error); }; }); }
async function saveImportedWorks(records) { return writeBrowserValue('works', records); }
async function restoreImportedWorks() { return await readBrowserValue('works') || []; }
