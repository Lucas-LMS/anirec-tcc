importScripts('../assets/history-profile.js', '../assets/ir-core.js');
let catalog, manifest, rowById, rowKeys;
const rootURL = path => new URL('../' + path, self.location.href);
const report = text => self.postMessage({ type: 'progress', text });
async function json(url) {
  const response = await fetch(url, { cache: 'no-cache' });
  if (!response.ok) throw Error('Não foi possível carregar ' + url);
  return response.json();
}
async function hash(buffer) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', buffer)), b => b.toString(16).padStart(2, '0')).join('');
}
function choices(query) {
  const text = String(query || '').normalize('NFKC').toLowerCase();
  return catalog.records.filter(row => (row.title + ' ' + (row.romaji || '')).normalize('NFKC').toLowerCase().includes(text))
    .slice(0, 100).map(row => ({ key: row.key, title: row.title }));
}
async function initialize() {
  report('Carregando manifesto e catálogo compacto…');
  const [corpus, models] = await Promise.all([json(rootURL('lab/comparison-catalog-manifest.json')), json(rootURL('lab/models.json'))]);
  const response = await fetch(rootURL(corpus.file), { cache: 'no-cache' });
  if (!response.ok) throw Error('Catálogo compacto do comparador indisponível.');
  const compressed = await response.arrayBuffer();
  if (await hash(compressed) !== corpus.compressed_sha256) throw Error('Hash do catálogo compactado inválido.');
  if (!('DecompressionStream' in self)) throw Error('Este navegador não oferece suporte à leitura do catálogo compactado.');
  const bytes = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  if (await hash(bytes) !== corpus.sha256) throw Error('Hash do catálogo compacto inválido.');
  const full = JSON.parse(new TextDecoder().decode(bytes));
  if (full.records.length !== corpus.count || corpus.source_catalog_sha256 !== models.corpus_sha256) throw Error('Contagem ou snapshot incompatível com o manifesto.');
  if (models.row_keys.length !== full.records.length || models.row_keys.some((key, i) => key !== full.records[i].key)) throw Error('A ordem dos modelos não corresponde ao catálogo completo.');
  catalog = full; manifest = models; rowKeys = new Set(models.row_keys);
  rowById = new Map(full.records.map(row => [Number(row.anilist_id), row]));
  self.postMessage({ type: 'ready', manifest, choices: choices('Lycoris Recoil'), count: catalog.records.length });
}
async function compare(input) {
  const anchor = catalog.records.find(row => row.key === input.anchor_key);
  if (!anchor) throw Error('Referência não encontrada no catálogo.');
  const normalizedProfile = { ...(input.profile || {}), notes: {} };
  for (const [key, score] of Object.entries(input.profile?.notes || {})) {
    let target = rowKeys.has(key) ? key : null;
    if (!target) {
      const match = /^(?:outside:|anilist:)(\d+)$/.exec(key);
      if (match) target = rowById.get(Number(match[1]))?.key || null;
    }
    if (target) normalizedProfile.notes[target] = score;
  }
  const rated_inside = Object.keys(normalizedProfile.notes).length;
  const rated_outside = Object.keys(input.profile?.notes || {}).length - rated_inside;
  const results = {}, timings = [];
  for (let index = 0; index < manifest.models.length; index++) {
    const spec = manifest.models[index], started = performance.now();
    report(`Carregando vetores de ${spec.label} (${index + 1}/${manifest.models.length})…`);
    const response = await fetch(rootURL(spec.file), { cache: 'force-cache' });
    if (!response.ok) throw Error('Vetores indisponíveis para ' + spec.label);
    const buffer = await response.arrayBuffer();
    if (buffer.byteLength !== spec.rows * spec.dimensions * 4) throw Error('Tamanho inválido dos vetores de ' + spec.label);
    if (await hash(buffer) !== spec.sha256) throw Error('Hash dos vetores inválido para ' + spec.label);
    const values = new Float32Array(buffer);
    for (let i = 0; i < catalog.records.length; i++) catalog.records[i].vector = Array.from(values.subarray(i * spec.dimensions, (i + 1) * spec.dimensions));
    const load_ms = performance.now() - started;
    report(`Calculando ${spec.label} no catálogo completo (${index + 1}/${manifest.models.length})…`);
    const options = {
      records: catalog.records, anchor, pure: !input.profile_enabled,
      ratings: normalizedProfile.notes, favorites: normalizedProfile.favorites || [],
      preferred: normalizedProfile.preferred || [], avoided: normalizedProfile.avoided || [],
      seenIds: normalizedProfile.seenIds || [], params: { ...catalog.params, model: spec.label },
      topic_idf: catalog.topic_idf, personalization: .35, personal_min_topics: .25,
      strategy: input.strategy, community_weight: input.community_weight, diagnostics: false,
    };
    const ranking = AniRecIR.rank(options);
    results[spec.id] = {
      anchor: { key: anchor.key, title: anchor.title },
      general: ranking.general.slice(0, 10).map(row => ({ key: row.key, title: row.title, base_score: row.base_score, personalized_score: row.personalized_score })),
      personalized: ranking.personalized.slice(0, 10).map(row => ({ key: row.key, title: row.title, base_score: row.base_score, personalized_score: row.personalized_score })),
      params: ranking.params, filters: ranking.filters, candidate_count: ranking.candidate_count,
      eligible_count: ranking.eligible_count, personal_eligible_count: ranking.personal_eligible_count,
      ranking_ms: ranking.ranking_ms,
    };
    timings.push({ id: spec.id, ranking_ms: ranking.ranking_ms, load_ms });
  }
  const reportData = {
    at: new Date().toISOString(), corpus_sha256: manifest.corpus_sha256,
    anchor: anchor.title, params: results.skipgram.params, filters: results.skipgram.filters,
    profile_enabled: input.profile_enabled, candidate_count: results.skipgram.candidate_count,
    eligible_count: results.skipgram.eligible_count, rated_inside, rated_outside, timings,
    models: manifest.models.map(model => ({ id: model.id, label: model.label, dimensions: model.dimensions, artifact_sha256: model.sha256 })),
    rankings: Object.fromEntries(Object.entries(results).map(([id, value]) => [id, {
      general: value.general.map(row => ({ key: row.key, title: row.title, score: row.base_score })),
      personalized: value.personalized.map(row => ({ key: row.key, title: row.title, score: row.personalized_score })),
    }])),
  };
  self.postMessage({ type: 'complete', results, report: reportData });
}
self.onmessage = async event => {
  try {
    const input = event.data;
    if (input.type === 'init') await initialize();
    else if (input.type === 'search') self.postMessage({ type: 'choices', request_id: input.request_id, choices: choices(input.query) });
    else if (input.type === 'compare') await compare(input);
  } catch (error) {
    self.postMessage({ type: 'error', message: error?.message || String(error) });
  }
};
