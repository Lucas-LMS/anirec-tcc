#!/usr/bin/env node
/** Build AniRec's public static catalog from the supplied AniList snapshot.
 * Uses only Node's built-in modules and the fixed word vectors already shipped
 * with AniRec. User lists, ratings, profiles, and account data are not read.
 */
import { createHash } from 'node:crypto';
import { createReadStream, readFileSync, writeFileSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { gzipSync } from 'node:zlib';
import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const online = path.join(here, 'online');
const modelDir = online;
const dims = 100;
const params = {
  version: 'ir-v12-series-frequency-profile', model: 'Word2Vec Skip-gram text8 100d',
  document_words: null, synopsis_policy: 'entire_available_source', idf_policy: 'anilist_catalog_smooth',
  base_semantic: .5, base_topics: .5, topic_metric: 'idf_weighted_tag_cosine_85_genres_15',
  affinity_metric: 'positive_coverage_times_one_minus_negative_coverage', profile_semantic: .7,
  profile_topics: .3, personal_min_topics: .15, profile_text_policy: 'positive_negative_centroid_contrast',
  default_personalization: .35, max_personalization: .6, explicit_topic_weight: 1,
  max_history_topics: null, rating_neutral: 'user_observed_midrange', rating_policy: 'signed_user_midrange',
  import_limit: null, profile_metadata_limit: null, api_cache_seconds: 3600,
};
const snapshotUtc = '2026-11-13T04:09:22.701253+00:00';
const fields = new Set([
  'id', 'idMal', 'type', 'format', 'seasonYear', 'status', 'title', 'description', 'genres', 'tags',
  'coverImage', 'siteUrl', 'isAdult', 'averageScore', 'meanScore', 'popularity', 'favourites',
  'stats', 'updatedAt', 'episodes', 'duration',
]);
const decodeEntities = text => text
  .replace(/&#(x[\da-f]+|\d+);?/gi, (_, code) => {
    const n = code[0].toLowerCase() === 'x' ? parseInt(code.slice(1), 16) : Number(code);
    return Number.isFinite(n) && n <= 0x10ffff ? String.fromCodePoint(n) : ' ';
  })
  .replace(/&(amp|lt|gt|quot|apos|nbsp|rsquo|lsquo|rdquo|ldquo|mdash|ndash|hellip|trade|copy|reg);/gi,
    (entity, name) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', rsquo: '’',
      lsquo: '‘', rdquo: '”', ldquo: '“', mdash: '—', ndash: '–', hellip: '…', trade: '™', copy: '©', reg: '®' })[name.toLowerCase()] || entity);
const clean = value => decodeEntities(String(value || '').replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
const tokens = text => String(text || '').normalize('NFKC').toLowerCase().match(/\p{L}+/gu) || [];
const norm = text => String(text).normalize('NFKC').toLowerCase().trim();
const json = (file, value) => writeFileSync(file, JSON.stringify(value));
const hashFile = async file => {
  const hash = createHash('sha256');
  for await (const part of createReadStream(file)) hash.update(part);
  return hash.digest('hex');
};

function usage() {
  console.error('Usage: node recomendador/import_complete_anilist.mjs --jsonl PATH --sqlite PATH [--output DIR]');
  process.exit(2);
}

const args = process.argv.slice(2);
const arg = name => { const i = args.indexOf(name); return i < 0 ? undefined : args[i + 1]; };
const jsonlPath = arg('--jsonl'), sqlitePath = arg('--sqlite'), output = path.resolve(arg('--output') || online);
if (!jsonlPath || !sqlitePath) usage();

console.log('Lendo catálogo JSONL e calculando frequências…');
const all = [], ids = new Set();
const input = createInterface({ input: createReadStream(jsonlPath, { encoding: 'utf8' }), crlfDelay: Infinity });
for await (const line of input) {
  if (!line.trim()) continue;
  const raw = JSON.parse(line);
  if (raw.type !== 'ANIME' || !Number.isInteger(raw.id)) throw Error('Registro ANIME inválido no JSONL.');
  if (ids.has(raw.id)) throw Error(`ID AniList duplicado: ${raw.id}`);
  ids.add(raw.id);
  const row = Object.fromEntries(Object.entries(raw).filter(([key]) => fields.has(key)));
  row.text = clean(row.description); delete row.description;
  all.push(row);
}
if (!all.length) throw Error('JSONL vazio.');
const records = all.filter(row => !row.isAdult);
const corpusTokens = records.map(row => tokens(row.text));
const df = new Map(), topicDf = new Map(), malCounts = new Map();
for (let i = 0; i < records.length; i++) {
  const row = records[i];
  for (const word of new Set(corpusTokens[i])) df.set(word, (df.get(word) || 0) + 1);
  const topics = new Set([...(row.genres || []), ...(row.tags || []).map(tag => tag.name).filter(Boolean)].map(norm));
  for (const topic of topics) topicDf.set(topic, (topicDf.get(topic) || 0) + 1);
  if (row.idMal) malCounts.set(row.idMal, (malCounts.get(row.idMal) || 0) + 1);
}
const n = records.length;
const idf = Object.fromEntries([...df].map(([word, count]) => [word, Math.log((n + 1) / (count + 1)) + 1]));
const unseen = Math.log(1 + n) + 1;
const topicIdf = Object.fromEntries([...topicDf].map(([topic, count]) => [topic, Math.log((n + 1) / (count + 1)) + 1]));

const vocabulary = JSON.parse(readFileSync(path.join(modelDir, 'vocabulary.json'), 'utf8'));
const vocabularyIndex = new Map(vocabulary.map((word, i) => [word, i]));
const modelManifest = JSON.parse(readFileSync(path.join(modelDir, 'model-manifest.json'), 'utf8'));
const shards = modelManifest.shards.map(shard => {
  const buffer = readFileSync(path.join(modelDir, shard.file));
  return { ...shard, values: new Float32Array(buffer.buffer, buffer.byteOffset, buffer.byteLength / 4) };
});
const vectorFor = words => {
  const vector = new Float64Array(dims); let totalWeight = 0;
  for (const word of words) {
    const index = vocabularyIndex.get(word);
    if (index === undefined) continue;
    const weight = idf[word] ?? unseen;
    const shard = shards.find(part => index >= part.start && index < part.start + part.count);
    const offset = (index - shard.start) * dims, values = shard.values;
    for (let d = 0; d < dims; d++) vector[d] += weight * values[offset + d];
    totalWeight += weight;
  }
  if (!totalWeight) return Array(dims).fill(0);
  let normSquared = 0;
  for (let d = 0; d < dims; d++) { vector[d] /= totalWeight; normSquared += vector[d] * vector[d]; }
  const length = Math.sqrt(normSquared);
  return length ? Array.from(vector, value => Math.fround(value / length)) : Array(dims).fill(0);
};

console.log(`Vetorizando ${n} obras não adultas de ${all.length} registros…`);
const outputRows = records.map((row, index) => {
  if (index && index % 2000 === 0) console.log(`  ${index}/${n}`);
  const title = row.title || {}, stats = row.stats || {};
  const malId = row.idMal || null;
  const ratingCount = stats.scoreDistribution == null ? null : stats.scoreDistribution.reduce((sum, item) => sum + (item.amount || 0), 0);
  const key = malId && malCounts.get(malId) === 1 ? `mal:${malId}` : `anilist:${row.id}`;
  return {
    encoding_id: '', key, title: title.english || title.romaji || String(row.id), romaji: title.romaji || '',
    text: row.text, genres: row.genres || [], tags: row.tags || [], cover: row.coverImage?.large || null,
    url: row.siteUrl || null, source: 'AniList (consulta sob demanda)', anilist_id: row.id, mal_id: malId,
    status: row.status || null, format: row.format || null, year: row.seasonYear ?? null, synopsis_source: row.text ? 'AniList description' : null,
    synopsis_complete: true, average_score: row.averageScore ?? null, mean_score: row.meanScore ?? null,
    popularity: row.popularity ?? null, community_favourites: row.favourites ?? null, rating_count: ratingCount,
    statistics_fetched_at: snapshotUtc, metadata_fetched_at: snapshotUtc,
    episodes: row.episodes ?? null, duration: row.duration ?? null,
    is_adult: false, vector: vectorFor(corpusTokens[index]),
  };
});
const stableIdf = Object.fromEntries(Object.entries(idf).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0));
const encodingId = createHash('sha256').update(JSON.stringify({ idf: stableIdf, unseen })).digest('hex');
for (const row of outputRows) row.encoding_id = encodingId;
const catalogBytes = Buffer.from(JSON.stringify({
  encoding_id: encodingId, params, topic_idf: topicIdf, records: outputRows,
  source: 'AniList public API snapshot; complete non-adult anime catalog as of 2026-11-13',
}));
const compressed = gzipSync(catalogBytes, { level: 9, mtime: 0 });
const catalogFile = path.join(output, 'catalog.json.gz');
await import('node:fs/promises').then(fs => fs.mkdir(output, { recursive: true }));
writeFileSync(catalogFile, compressed);
console.log(`Catálogo pronto: ${(compressed.length / 1048576).toFixed(1)} MiB compactado.`);

console.log('Exportando recomendações comunitárias do SQLite…');
const db = new DatabaseSync(sqlitePath, { readOnly: true });
const anchors = {};
for (const row of db.prepare('SELECT media_id,complete,edge_count,pages FROM recommendation_status ORDER BY media_id').iterate()) {
  anchors[String(row.media_id)] = {
    anchor_id: row.media_id, source: 'AniList GraphQL recommendations.rating',
    status: row.complete ? 'available' : 'incomplete', complete: Boolean(row.complete),
    edge_count: row.edge_count, pages: row.pages, edges: [],
  };
}
let edgeCount = 0;
for (const row of db.prepare('SELECT source_media_id,target_media_id,rating FROM recommendations WHERE target_media_id IS NOT NULL ORDER BY source_media_id,recommendation_id').iterate()) {
  const anchor = anchors[String(row.source_media_id)];
  if (anchor) { anchor.edges.push({ target_id: row.target_media_id, rating: row.rating }); edgeCount++; }
}
db.close();
const community = {
  format: 'anirec-pairwise-community-v1',
  purpose: 'AniList community recommendations for the frozen catalog; optional ranking evidence, not evaluation judgments.',
  snapshot_utc: '2026-11-13T18:16:38Z', anchors,
};
json(path.join(output, 'community-recommendations.json'), community);
console.log(`Grafo pronto: ${Object.keys(anchors).length} âncoras, ${edgeCount} arestas.`);

const sourceHash = await hashFile(jsonlPath);
const manifest = {
  count: outputRows.length, sha256: createHash('sha256').update(catalogBytes).digest('hex'),
  bytes: catalogBytes.length, catalog_file: 'catalog.json.gz', compressed_bytes: compressed.length,
  source_total_count: all.length, adult_records_excluded: all.length - outputRows.length,
  private_profile_included: false, anilist_cache_included: false, full_synopses: true,
  model: params.model, version: params.version, source_snapshot_utc: snapshotUtc,
};
json(path.join(output, 'build-manifest.json'), manifest);
json(path.join(output, 'source-manifest.json'), {
  source: 'AniList GraphQL',
  selection: 'Complete source snapshot; adult titles excluded by AniRec catalog policy.',
  count: outputRows.length, source_total_count: all.length, adult_records_excluded: all.length - outputRows.length,
  personal_ratings_included: false, usernames_included: false,
  snapshot_utc: manifest.source_snapshot_utc, source_jsonl_sha256: sourceHash,
});
json(path.join(output, 'idf.json'), { corpus_id: encodingId, idf, unseen });
console.log(JSON.stringify({ ...manifest, recommendation_anchors: Object.keys(anchors).length, recommendation_edges: edgeCount, output: output }));
