window.AniRecAdapter = (() => {
  async function request(path, data) {
    const response = await fetch(path, data === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    const result = await response.json(); if (!response.ok) throw Error(result.error || 'Não foi possível concluir a operação.'); return result;
  }
  return {
    init: async () => {},
    moreDiscoveries: anchor => request('/api/discover-more',{key:anchor.key}),
    config: async () => ({ ...await request('/api/config'), mode: 'local' }),
    taxonomy: () => request('/api/tags'), popular: () => request('/api/popular'),
    search: (query, online) => request('/api/search?q=' + encodeURIComponent(query) + '&online=' + online),
    saveOnboarding: selection => request('/api/profile/onboarding', { preferred: selection.preferred, avoided: selection.avoided, favorite_keys: selection.favorites.map(item => item.key) }),
    preferences: (preferred, avoided) => request('/api/profile/preferences', { preferred, avoided }),
    favorite: (key, add) => request('/api/profile/favorite', { key, add }),
    reject: (key, add = true) => request('/api/profile/reject', { key, add }),
    clearImport: () => request('/api/profile/clear-import', {}),
    recommend: options => request('/api/recommend', options),
    statistics: scope => request('/api/profile/statistics?scope='+encodeURIComponent(scope)),
    study: options => request('/api/study',options),
    dataset: () => request('/api/dataset'), exportProfile: () => request('/api/profile/export'),
    importProfile: async (username, progress) => {
      const timer = setInterval(async () => { try { const state = await request('/api/import-status'); if (state.active) progress(state.stage + (state.count ? ` · ${state.count} entradas` : '') + (state.metadata_target ? ` · ${state.metadata_count}/${state.metadata_target} metadados` : '')); } catch {} }, 1500);
      try { return await request('/api/profile/import', { username }); } finally { clearInterval(timer); }
    }
  };
})();
