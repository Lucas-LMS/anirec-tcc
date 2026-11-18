(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const node = (tag, text) => { const item = document.createElement(tag); item.textContent = text; return item; };
  const worker = new Worker('lab/comparison-worker.js');
  let manifest, rowKeys, results = {}, report, profile = {}, requestId = 0, searchTimer;
  function showChoices(items) {
    const select = $('anchor'), previous = select.value;
    select.replaceChildren();
    for (const row of items) {
      const option = node('option', row.title); option.value = row.key; select.append(option);
    }
    if (items.some(row => row.key === previous)) select.value = previous;
  }
  async function getProfile() {
    if (location.hostname === '127.0.0.1' && location.port === '8765') {
      const response = await fetch('/api/profile/export'), data = await response.json(), value = data.profile;
      return {
        notes: Object.fromEntries((value.entries || []).filter(row => row.score > 0).map(row => {
          const id = row.mediaId || row.media?.id, key = `anilist:${id}`, item = rowKeys.has(key) ? key : null;
          return [item || `outside:${id}`, row.score / 10];
        })),
        favorites: (value.manual_favorites || []).map(row => row.key), preferred: value.preferred || [],
        avoided: value.avoided || [], seenIds: (value.entries || []).filter(row => ['COMPLETED','CURRENT','PAUSED','DROPPED','REPEATING'].includes(row.status)).map(row => row.mediaId || row.media?.id),
      };
    }
    const prefs = JSON.parse(localStorage.getItem('anirec-demo-preferences') || '{}');
    return { notes: JSON.parse(localStorage.getItem('anirec-demo-notes') || '{}'),
      favorites: JSON.parse(localStorage.getItem('anirec-demo-favorites') || '[]'),
      preferred: (prefs.preferred || '').split(',').map(value => value.trim()).filter(Boolean),
      avoided: (prefs.avoided || '').split(',').map(value => value.trim()).filter(Boolean) };
  }
  function onComplete(value) {
    results = value.results; report = value.report;
    $('status').textContent = `Pronto: ${report.candidate_count.toLocaleString('pt-BR')} obras avaliadas, ${manifest.models.length} modelos. ` +
      `${report.rated_inside} notas no catálogo; ${report.rated_outside} fora dele.`;
    $('run').disabled = false; render();
  }
  worker.onmessage = event => {
    const message = event.data;
    if (message.type === 'progress') { $('status').textContent = message.text; return; }
    if (message.type === 'ready') {
      manifest = message.manifest;
      rowKeys = new Set(manifest.row_keys);
      for (const model of manifest.models) { const option = node('option', model.label); option.value = model.id; $('model').append(option); }
      showChoices(message.choices);
      $('status').textContent = `Catálogo completo pronto: ${message.count.toLocaleString('pt-BR')} obras. Escolha uma referência.`;
      return;
    }
    if (message.type === 'choices') { if (message.request_id === requestId) showChoices(message.choices); return; }
    if (message.type === 'complete') { onComplete(message); return; }
    if (message.type === 'error') { $('status').textContent = message.message; $('run').disabled = false; }
  };
  worker.onerror = event => { $('status').textContent = 'Falha no comparador: ' + event.message; $('run').disabled = false; };
  $('search').oninput = () => {
    clearTimeout(searchTimer); const query = $('search').value, id = ++requestId;
    searchTimer = setTimeout(() => worker.postMessage({ type: 'search', query, request_id: id }), 120);
  };
  $('run').onclick = async () => {
    if (!$('anchor').value || !manifest) return;
    $('run').disabled = true; report = null; $('status').textContent = 'Preparando comparação…';
    try {
      profile = $('useProfile').checked ? await getProfile() : {};
      worker.postMessage({ type: 'compare', anchor_key: $('anchor').value, profile,
        profile_enabled: $('useProfile').checked, strategy: $('strategy').value,
        community_weight: Number($('community').value) });
    } catch (error) { $('status').textContent = error.message; $('run').disabled = false; }
  };
  $('model').onchange = $('mode').onchange = render;
  $('export').onclick = () => {
    if (!report) return;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    link.download = 'anirec-comparacao-estaticos.json'; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  };
  function render() {
    if (!report || !results.skipgram) return;
    const mode = $('mode').value, reference = results.skipgram[mode], referenceKeys = new Set(reference.map(row => row.key));
    $('comparison').replaceChildren();
    for (const spec of manifest.models) {
      const rows = results[spec.id][mode], overlap = rows.filter(row => referenceKeys.has(row.key)).length;
      const time = report.timings.find(value => value.id === spec.id), tr = document.createElement('tr');
      for (const value of [spec.label, spec.dimensions, (100 * spec.mean_token_coverage).toFixed(1) + '%',
        (100 * overlap / Math.max(1, reference.length)).toFixed(0) + '%', time.ranking_ms.toFixed(2), time.load_ms.toFixed(2)]) tr.append(node('td', value));
      $('comparison').append(tr);
    }
    const selected = $('model').value, value = results[selected], rows = value[mode];
    $('ranking').replaceChildren();
    rows.forEach((row, i) => { const box = node('div', `#${i + 1} · ${row.title} · ${(mode === 'general' ? row.base_score : row.personalized_score).toFixed(3)}`); box.className = 'rankrow'; $('ranking').append(box); });
    $('changes').replaceChildren(); const baseline = new Map(results.skipgram[mode].map((row, i) => [row.key, i + 1]));
    rows.forEach((row, i) => $('changes').append(node('p', `${row.title}: Skip-gram #${baseline.get(row.key) || 'fora'} → selecionado #${i + 1}`)));
    $('metrics').replaceChildren();
    for (const [number, label] of [[manifest.row_keys.length.toLocaleString('pt-BR'), 'obras comparáveis'],
      [manifest.models.length, 'modelos treinados na mesma base'], [report.rated_inside, 'notas no catálogo'],
      [value.ranking_ms.toFixed(0) + ' ms', 'ranking selecionado']]) {
      const box = document.createElement('div'); box.className = 'kpi'; box.append(node('strong', number), node('p', label)); $('metrics').append(box);
    }
    const spec = manifest.models.find(model => model.id === selected);
    $('provenance').replaceChildren(node('h3', 'Artefato e treinamento'));
    $('provenance').append(node('pre', JSON.stringify({ source: spec.source, settings: spec.settings,
      rows: spec.rows, vector_sha256: spec.sha256 }, null, 2)));
  }
  $('status').textContent = 'Iniciando comparador…';
  worker.postMessage({ type: 'init' });
})();
