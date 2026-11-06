/* Same optional three-step preference editor in the local and hosted app. */
window.AniRecOnboarding = async function (adapter, onSaved) {
  const make = (tag, text, cls) => { const n = document.createElement(tag); if (text != null) n.textContent = text; if (cls) n.className = cls; return n; };
  const state = await adapter.config(), taxonomy = await adapter.taxonomy(), popular = await adapter.popular();
  const genres = new Set(taxonomy.genres), canonical = new Map([...taxonomy.genres,...taxonomy.tags.map(t=>t.name)].map(name=>[name.toLowerCase(),name])), preferred = new Set((state.profile.preferred || []).map(name=>canonical.get(name.toLowerCase())||name)), avoided = new Set((state.profile.avoided || []).map(name=>canonical.get(name.toLowerCase())||name));
  const favorites = new Map((state.profile.manual_favorites || []).map(item => [item.key, item]));
  // Presentation only: do not delete or silently change existing preferences.
  const sensitiveNames = new Set(['nudity','ero guro','psychosexual','incest','inseki',"teens' love",'succubus','hentai']);
  const sensitive = meta => meta.isAdult === true || /sexual content/i.test(meta.category || '') || sensitiveNames.has(meta.name.toLowerCase());
  const sensitiveName = name => sensitive(taxonomy.tags.find(tag => tag.name === name) || { name });
  let showSensitive = false, displaySettingsOpen = false;
  const dialog = make('dialog', null, 'wizard'); dialog.setAttribute('aria-labelledby', 'wizardTitle');
  const header = make('div', null, 'dialog-head'), title = make('h2', 'Um perfil com a sua cara'); title.id = 'wizardTitle';
  const close = make('button', '✕', 'quiet'); close.setAttribute('aria-label', 'Cancelar configuração de preferências'); close.onclick = () => dialog.close();
  header.append(title, close); const lead = make('p', 'Três passos opcionais. Sugerimos cerca de três escolhas em cada um. Você pode pular e não precisa dar notas.', 'muted');
  const progress = make('div', null, 'wizard-progress'), body = make('div', null, 'wizard-body'), status = make('p', '', 'status'); status.setAttribute('role', 'status');
  const footer = make('div', null, 'dialog-foot'), back = make('button', 'Voltar'), skip = make('button', 'Pular passo', 'quiet'), next = make('button', 'Continuar', 'primary');
  footer.append(back, skip, next); dialog.append(header, lead, progress, body, status, footer); document.body.append(dialog);
  let step = 0, renderedStep = -1, searchGeneration = 0; const drafts={0:{},1:{}};
  function toggle(set, other, name) {
    if (set.has(name)) set.delete(name);
    else { if (set.size >= 30) { status.textContent = 'Use até 30 preferências por campo.'; return; } set.add(name); other.delete(name); }
    render();
  }
  function choice(name, isTag) {
    const item = make('div', null, 'choice-tile'); item.append(make('strong', name));
    if (isTag) {
      const meta = taxonomy.tags.find(t => t.name === name), details = make('details');
      details.append(make('summary', 'O que significa?'));
      const description = new DOMParser().parseFromString(meta?.description || 'Sem definição fornecida.', 'text/html').body.textContent;
      details.append(make('p', description, 'tiny muted')); item.append(details);
    }
    const actions = make('div', null, 'row');
    for (const [set, other, label] of [[preferred, avoided, 'Gosto'], [avoided, preferred, 'Evitar']]) {
      const b = make('button', (set.has(name) ? '✓ ' : '') + label, 'small'); b.setAttribute('aria-pressed', String(set.has(name)));
      b.setAttribute('aria-label', label + ': ' + name); b.onclick = () => toggle(set, other, name); actions.append(b);
    }
    item.append(actions); return item;
  }
  function anime(item) {
    const b = make('button', null, 'anime-choice'); b.setAttribute('aria-label', 'Favorito: ' + item.title); b.setAttribute('aria-pressed', String(favorites.has(item.key)));
    if (item.cover && /^https:\/\//.test(item.cover)) { const image = make('img'); image.src = item.cover; image.alt = ''; image.loading = 'lazy'; image.referrerPolicy = 'no-referrer'; b.append(image); }
    b.append(make('strong', item.title), make('span', favorites.has(item.key) ? '✓ Favorito' : 'Selecionar', 'tiny'));
    b.onclick = () => { if (favorites.has(item.key)) favorites.delete(item.key); else if (favorites.size < 30) favorites.set(item.key, item); render(); }; return b;
  }
  function selected(names) {
    const row = make('div', null, 'selected-chips');
    for (const name of names) { const b = make('button', (avoided.has(name) ? 'Evitar: ' : '') + name + ' ×', 'small'); b.setAttribute('aria-label', 'Remover preferência ' + name); b.onclick = () => { preferred.delete(name); avoided.delete(name); render(); }; row.append(b); }
    return row;
  }
  function render() {
    if(renderedStep>=0&&renderedStep<2&&body.querySelector('.catalog-browser')){const previous=body.querySelector('.catalog-browser');drafts[renderedStep]={open:previous.open,query:previous.querySelector('input').value,category:previous.querySelector('select')?.value||''};}
    renderedStep=step;body.replaceChildren(); progress.textContent = `Passo ${step + 1} de 3 · ${['Gêneros', 'Tags e temas', 'Animes favoritos'][step]}`;
    back.disabled = step === 0; skip.classList.toggle('hidden', step === 2); next.textContent = step === 2 ? 'Salvar meu perfil' : 'Continuar'; status.textContent = '';
    if (step < 2) {
      const isTag = step === 1;
      body.append(make('h3', isTag ? 'Quais temas chamam sua atenção?' : 'Quais gêneros você gosta de assistir?'));
      const chosen = [...new Set([...preferred, ...avoided])].filter(name => genres.has(name) !== isTag);
      const visibleChosen = chosen.filter(name => showSensitive || !sensitiveName(name)), hiddenChosen = chosen.length-visibleChosen.length;
      body.append(make('p', `${chosen.length} escolhas neste passo. Cerca de três já ajudam; não é obrigatório.${hiddenChosen ? ` ${hiddenChosen} escolhas salvas estão ocultas nesta exibição.` : ''}`, 'tiny muted'), selected(visibleChosen));
      const display = make('details', null, 'tiny muted'); display.open = displaySettingsOpen;
      display.append(make('summary', 'Opções de exibição'));
      const reveal = make('input'); reveal.type = 'checkbox'; reveal.checked = showSensitive;
      const revealLabel = make('label', null, 'check'); revealLabel.append(reveal, document.createTextNode(' Mostrar temas adultos/sexuais'));
      display.append(revealLabel); display.ontoggle = () => { displaySettingsOpen = display.open; };
      reveal.onchange = () => { showSensitive = reveal.checked; displaySettingsOpen = true; render(); }; body.append(display);
      const suggestions = isTag ? ['Female Protagonist', 'Yuri', 'Found Family', 'Time Manipulation', 'Espionage', 'Cute Girls Doing Cute Things', 'Space', 'School', 'Magic'].filter(name => taxonomy.tags.some(t => t.name === name)) : ['Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Romance', 'Sci-Fi', 'Slice of Life'].filter(name => genres.has(name));
      body.append(make('h4', 'Algumas ideias para começar')); const quick = make('div', null, 'choice-grid'); for (const name of suggestions.filter(name => showSensitive || !sensitiveName(name))) quick.append(choice(name, isTag)); body.append(quick);
      const available = (isTag ? taxonomy.tags : taxonomy.genres.map(name => ({ name, description: '' }))).filter(meta => showSensitive || !sensitive(meta));
      const all = make('details', null, 'catalog-browser'); all.append(make('summary', isTag ? `Explorar ${available.length} tags disponíveis, por categoria` : `Explorar ${available.length} gêneros disponíveis`));
      const controls = make('div', null, 'row'), search = make('input'); search.type = 'search'; search.placeholder = 'Pesquisar nome ou definição'; search.setAttribute('aria-label', isTag ? 'Pesquisar todas as tags' : 'Pesquisar todos os gêneros'); controls.append(search);
      const category = make('select'); category.setAttribute('aria-label', 'Categoria das tags'); category.append(new Option('Todas as categorias', ''));
      if (isTag) { for (const name of [...new Set(available.map(t => t.category || 'Sem categoria'))].sort()) category.append(new Option(name, name)); controls.append(category); }
      const list = make('div', null, 'choice-grid all-choices');all.open=!!drafts[step].open;search.value=drafts[step].query||'';category.value=drafts[step].category||'';
      function filter() {
        const query = search.value.trim().toLowerCase(); list.replaceChildren();
        const rows = available;
        const matches = rows.filter(t => (!query || (t.name + ' ' + (t.description || '')).toLowerCase().includes(query)) && (!isTag || !category.value || (t.category || 'Sem categoria') === category.value));
        for (const meta of matches) { const node = choice(meta.name, isTag); if (isTag) node.prepend(make('span', meta.category || 'Sem categoria', 'eyebrow')); list.append(node); }
        if (!matches.length) list.append(make('p', 'Nenhuma opção encontrada. Tente um nome em inglês.'));
      }
      search.oninput = filter; category.onchange = filter; filter(); all.append(controls, list); body.append(all);
    } else {
      body.append(make('h3', 'Quais animes você já gosta?'), make('p', `${favorites.size} favoritos. Escolha cerca de três; nenhuma nota é exigida.`, 'tiny muted'));
      if (favorites.size) { const chosen = make('div', null, 'anime-grid'); for (const item of favorites.values()) chosen.append(anime(item)); body.append(chosen); }
      body.append(make('h4', 'Populares no recorte coletado do AniList'));
      const suggestions = make('div', null, 'anime-grid'); for (const item of popular.slice(0, 12)) suggestions.append(anime(item)); body.append(suggestions);
      const label = make('label', 'Não encontrou? Pesquise outro anime'), search = make('input'); search.type = 'search'; search.placeholder = 'Ex.: Lycoris Recoil'; search.setAttribute('aria-label', 'Pesquisar outros animes favoritos');
      const matches = make('div', null, 'anime-grid'), feedback = make('p', '', 'tiny muted'); let timer;
      search.oninput = () => { clearTimeout(timer); const generation = ++searchGeneration; const query = search.value.trim(); if (query.length < 2) { matches.replaceChildren(); return; } timer = setTimeout(async () => { feedback.textContent = 'Pesquisando…'; try { const result = await adapter.search(query, true); if (generation !== searchGeneration) return; matches.replaceChildren(); for (const item of result.items) matches.append(anime(item)); feedback.textContent = result.items.length ? 'Selecione os favoritos desejados.' : 'Nenhum resultado encontrado.'; } catch (e) { feedback.textContent = e.message; } }, 600); };
      body.append(label, search, feedback, matches);
    }
  }
  back.onclick = () => { step--; render(); }; skip.onclick = () => { step++; render(); };
  next.onclick = async () => {
    if (step < 2) { step++; render(); return; }
    next.disabled = back.disabled = skip.disabled = true; status.textContent = 'Salvando preferências…';
    try { await adapter.saveOnboarding({ preferred: [...preferred], avoided: [...avoided], favorites: [...favorites.values()] }, text => status.textContent = text); dialog.close(); await onSaved(); }
    catch (error) { status.textContent = error.message; next.disabled = back.disabled = false; }
  };
  dialog.onclose = () => dialog.remove(); render(); dialog.showModal();
};
