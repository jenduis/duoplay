// DuoPlay Universal Co-Op & Multiplayer App Logic
document.addEventListener('DOMContentLoaded', () => {
  // State
  const state = {
    platform: 'all',
    category: 'all',
    mode: 'all',
    connection: 'all',
    difficulty: 'all',
    vibe: 'all',
    search: '',
    sort: 'couple-first',
    currentPage: 1,
    pageSize: 36,
    shortlist: new Set(JSON.parse(localStorage.getItem('duoplay_favs') || '[]')),
    activeModalGameId: null
  };

  // DOM Elements
  const gamesGrid = document.getElementById('gamesGrid');
  const emptyState = document.getElementById('emptyState');
  const searchInput = document.getElementById('searchInput');
  const clearSearchBtn = document.getElementById('clearSearchBtn');
  const sortSelect = document.getElementById('sortSelect');
  const resetFiltersBtn = document.getElementById('resetFiltersBtn');
  const filteredCountEl = document.getElementById('filteredCount');
  const totalCatalogCountEl = document.getElementById('totalCatalogCount');

  const filterMode = document.getElementById('filterMode');
  const filterConnection = document.getElementById('filterConnection');
  const filterDifficulty = document.getElementById('filterDifficulty');
  const filterVibe = document.getElementById('filterVibe');

  // Pagination Elements
  const paginationBar = document.getElementById('paginationBar');
  const prevPageBtn = document.getElementById('prevPageBtn');
  const nextPageBtn = document.getElementById('nextPageBtn');
  const pageIndicator = document.getElementById('pageIndicator');

  // Matchmaker Elements
  const matchmakerSection = document.getElementById('matchmakerSection');
  const openMatchmakerBtn = document.getElementById('openMatchmakerBtn');
  const closeMatchmakerBtn = document.getElementById('closeMatchmakerBtn');
  const generateMatchesBtn = document.getElementById('generateMatchesBtn');
  const matchResultsContainer = document.getElementById('matchResultsContainer');
  const matchCardsGrid = document.getElementById('matchCardsGrid');

  // Shortlist Elements
  const openShortlistBtn = document.getElementById('openShortlistBtn');
  const closeShortlistBtn = document.getElementById('closeShortlistBtn');
  const shortlistBackdrop = document.getElementById('shortlistBackdrop');
  const shortlistCountEl = document.getElementById('shortlistCount');
  const drawerCountEl = document.getElementById('drawerCount');
  const shortlistItemsEl = document.getElementById('shortlistItems');
  const copyShortlistBtn = document.getElementById('copyShortlistBtn');
  const clearShortlistBtn = document.getElementById('clearShortlistBtn');

  // Modal Elements
  const modalBackdrop = document.getElementById('gameModalBackdrop');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const modalCloseActionBtn = document.getElementById('modalCloseActionBtn');
  const modalBookmarkBtn = document.getElementById('modalBookmarkBtn');

  // Validate Database
  const allGames = typeof GAMES_DATA !== 'undefined' ? GAMES_DATA : [];
  totalCatalogCountEl.textContent = allGames.length.toLocaleString();

  // Initialize Counts on Tabs
  updatePlatformCounts();
  updateShortlistBadges();

  // Initial Render
  renderGames();

  // ==========================================
  // Event Listeners: Search & Sort
  // ==========================================

  searchInput.addEventListener('input', (e) => {
    state.search = e.target.value.trim().toLowerCase();
    clearSearchBtn.style.display = state.search ? 'block' : 'none';
    state.currentPage = 1;
    renderGames();
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    state.search = '';
    clearSearchBtn.style.display = 'none';
    state.currentPage = 1;
    renderGames();
  });

  sortSelect.addEventListener('change', (e) => {
    state.sort = e.target.value;
    state.currentPage = 1;
    renderGames();
  });

  // Platform Tabs
  document.getElementById('platformTabs').addEventListener('click', (e) => {
    const btn = e.target.closest('.tab-btn');
    if (!btn) return;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.platform = btn.dataset.platform;
    state.currentPage = 1;
    renderGames();
  });

  // Category Pills
  document.getElementById('categoryPills').addEventListener('click', (e) => {
    const pill = e.target.closest('.cat-pill');
    if (!pill) return;
    document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    state.category = pill.dataset.category;
    state.currentPage = 1;
    renderGames();
  });

  // Secondary Dropdowns
  filterMode.addEventListener('change', (e) => { state.mode = e.target.value; state.currentPage = 1; renderGames(); });
  filterConnection.addEventListener('change', (e) => { state.connection = e.target.value; state.currentPage = 1; renderGames(); });
  filterDifficulty.addEventListener('change', (e) => { state.difficulty = e.target.value; state.currentPage = 1; renderGames(); });
  filterVibe.addEventListener('change', (e) => { state.vibe = e.target.value; state.currentPage = 1; renderGames(); });

  resetFiltersBtn.addEventListener('click', resetAllFilters);

  // Pagination Handlers
  prevPageBtn.addEventListener('click', () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      renderGames();
      window.scrollTo({ top: document.querySelector('.filter-controls-container').offsetTop - 60, behavior: 'smooth' });
    }
  });

  nextPageBtn.addEventListener('click', () => {
    const totalPages = Math.ceil(getFilteredGames().length / state.pageSize);
    if (state.currentPage < totalPages) {
      state.currentPage++;
      renderGames();
      window.scrollTo({ top: document.querySelector('.filter-controls-container').offsetTop - 60, behavior: 'smooth' });
    }
  });

  // ==========================================
  // Filtering & Sorting Logic
  // ==========================================

  function matchPlatform(game, filter) {
    if (filter === 'all') return true;
    const plats = (game.platforms || [game.platform]).map(p => p.toLowerCase());
    if (filter === 'Switch') return plats.some(p => p.includes('switch'));
    if (filter === 'PC') return plats.some(p => p.includes('pc') || p.includes('steam') || p.includes('epic'));
    if (filter === 'PlayStation') return plats.some(p => p.includes('playstation') || p.includes('ps'));
    if (filter === 'Xbox') return plats.some(p => p.includes('xbox'));
    if (filter === '3DS') return plats.some(p => p.includes('3ds') || p.includes('ds'));
    if (filter === 'Retro') return plats.some(p => p.includes('retro') || p.includes('wii') || p.includes('gamecube') || p.includes('n64') || p.includes('snes') || p.includes('nes') || p.includes('gba'));
    if (filter === 'Mods') return game.category.toLowerCase().includes('mod') || game.connection.toLowerCase().includes('mod');
    return true;
  }

  function getFilteredGames() {
    return allGames.filter(game => {
      // Platform / Console Filter
      if (!matchPlatform(game, state.platform)) return false;

      // Category Filter
      if (state.category === 'couples') {
        if (!game.isCouplePick) return false;
      } else if (state.category !== 'all' && !game.category.includes(state.category)) {
        return false;
      }

      // Multiplayer Mode
      if (state.mode !== 'all') {
        const m = (game.mode || '').toLowerCase();
        if (state.mode === 'Co-op' && !m.includes('co-op')) return false;
        if (state.mode === 'Versus' && !m.includes('versus')) return false;
        if (state.mode === 'Co-op & Versus' && !(m.includes('co-op') && m.includes('versus'))) return false;
      }

      // Connection Type
      if (state.connection !== 'all') {
        const conn = (game.connection || '').toLowerCase();
        if (state.connection === 'same-screen' && !conn.includes('same-screen')) return false;
        if (state.connection === 'split-screen' && !conn.includes('split-screen')) return false;
        if (state.connection === 'online' && !conn.includes('online') && !conn.includes('lan')) return false;
        if (state.connection === 'local-wireless' && !conn.includes('local wireless')) return false;
        if (state.connection === 'download-play' && !game.downloadPlay) return false;
        if (state.connection === 'mod' && !conn.includes('mod') && !game.category.toLowerCase().includes('mod')) return false;
      }

      // Difficulty
      if (state.difficulty !== 'all' && game.difficulty !== state.difficulty) return false;

      // Vibe
      if (state.vibe !== 'all' && game.vibe !== state.vibe) return false;

      // Search (Query matches title, platforms, genre, description, how it relates)
      if (state.search) {
        const query = state.search;
        const platformsStr = (game.platforms || []).join(' ').toLowerCase();
        const textToSearch = [
          game.title,
          platformsStr,
          game.genre,
          game.summary,
          game.howItRelates || game.multiplayerFeatures,
          game.setupGuide,
          game.vibe
        ].join(' ').toLowerCase();

        if (!textToSearch.includes(query)) return false;
      }

      return true;
    }).sort((a, b) => {
      if (state.sort === 'couple-first') {
        if (a.isCouplePick !== b.isCouplePick) return b.isCouplePick ? 1 : -1;
        if (b.rating !== a.rating) return b.rating - a.rating;
        return a.title.localeCompare(b.title);
      }
      if (state.sort === 'rating-desc') {
        if (b.rating !== a.rating) return b.rating - a.rating;
        return a.title.localeCompare(b.title);
      }
      if (state.sort === 'title-asc') {
        return a.title.localeCompare(b.title);
      }
      if (state.sort === 'players-desc') {
        const getP = (p) => parseInt(String(p).match(/\d+$/)?.[0] || '1', 10);
        return getP(b.maxPlayers) - getP(a.maxPlayers);
      }
      return 0;
    });
  }

  function renderGames() {
    const filtered = getFilteredGames();
    filteredCountEl.textContent = filtered.length.toLocaleString();

    const isFiltered = state.platform !== 'all' || 
                       state.category !== 'all' || 
                       state.mode !== 'all' || 
                       state.connection !== 'all' || 
                       state.difficulty !== 'all' || 
                       state.vibe !== 'all' || 
                       state.search !== '';

    resetFiltersBtn.style.display = isFiltered ? 'inline-block' : 'none';

    if (filtered.length === 0) {
      gamesGrid.innerHTML = '';
      emptyState.style.display = 'block';
      paginationBar.style.display = 'none';
      return;
    }

    emptyState.style.display = 'none';

    // Pagination Calculation
    const totalPages = Math.ceil(filtered.length / state.pageSize) || 1;
    if (state.currentPage > totalPages) state.currentPage = totalPages;
    if (state.currentPage < 1) state.currentPage = 1;

    pageIndicator.textContent = `Page ${state.currentPage} of ${totalPages}`;
    prevPageBtn.disabled = state.currentPage === 1;
    nextPageBtn.disabled = state.currentPage === totalPages;
    paginationBar.style.display = totalPages > 1 ? 'flex' : 'none';

    const startIdx = (state.currentPage - 1) * state.pageSize;
    const pageGames = filtered.slice(startIdx, startIdx + state.pageSize);

    gamesGrid.innerHTML = pageGames.map(game => {
      const isSaved = state.shortlist.has(game.id);
      const catClass = game.category.includes('Native') ? 'native' : game.category.includes('Emulation') ? 'emu' : 'mod';
      const stars = '★'.repeat(Math.floor(game.rating)) + (game.rating % 1 !== 0 ? '½' : '');
      const platformsDisplay = (game.platforms || [game.platform]).slice(0, 3).join(', ') + ((game.platforms && game.platforms.length > 3) ? '...' : '');

      return `
        <article class="game-card" data-id="${game.id}">
          <div class="card-top-bar">
            <div class="badge-group">
              <span class="badge platform-badge">${escapeHtml(game.platform || 'Multi')}</span>
              <span class="badge category-badge ${catClass}">${escapeHtml((game.category || 'Official').split('/')[0])}</span>
              ${game.isCouplePick ? '<span class="badge couple-badge">⭐ Top Duo Pick</span>' : ''}
              ${game.downloadPlay ? '<span class="badge download-play-badge">⚡ 1-Cart Download Play</span>' : ''}
            </div>
            <button class="bookmark-icon-btn ${isSaved ? 'saved' : ''}" 
                    aria-label="${isSaved ? 'Remove from favorites' : 'Add to favorites'}"
                    onclick="toggleShortlist('${game.id}', event)">
              ${isSaved ? '⭐' : '☆'}
            </button>
          </div>

          <div class="card-header-with-cover">
            <div class="card-cover-container">
              <div class="card-cover-placeholder">🎮</div>
            </div>
            <div class="card-header-text">
              <h3 class="card-title">${escapeHtml(game.title)}</h3>
              <div class="card-meta">
                <span>🎭 ${escapeHtml(game.genre || 'Action')}</span><br>
                <span>👥 ${escapeHtml(game.maxPlayers || '2 Players')}</span>
              </div>
            </div>
          </div>

          <!-- How It Relates to Co-Op Box -->
          <div class="card-relation-box">
            <strong>Co-Op Relation:</strong> ${escapeHtml(game.howItRelates || game.multiplayerFeatures || 'Multiplayer supported.')}
          </div>

          <div class="card-platforms">
            ${(game.platforms || [game.platform]).slice(0, 4).map(p => `<span class="platform-pill-tag">${escapeHtml(p)}</span>`).join('')}
          </div>

          <div class="card-footer">
            <span class="rating-stars" title="${game.rating} out of 5 stars">${stars}</span>
            <button class="btn btn-secondary btn-sm" onclick="openGameModal('${game.id}')">
              Co-Op Details ➔
            </button>
          </div>
        </article>
      `;
    }).join('');
  }

  function updatePlatformCounts() {
    document.getElementById('count-all').textContent = allGames.length.toLocaleString();
    document.getElementById('count-switch').textContent = allGames.filter(g => matchPlatform(g, 'Switch')).length.toLocaleString();
    document.getElementById('count-pc').textContent = allGames.filter(g => matchPlatform(g, 'PC')).length.toLocaleString();
    document.getElementById('count-ps').textContent = allGames.filter(g => matchPlatform(g, 'PlayStation')).length.toLocaleString();
    document.getElementById('count-xbox').textContent = allGames.filter(g => matchPlatform(g, 'Xbox')).length.toLocaleString();
    document.getElementById('count-3ds').textContent = allGames.filter(g => matchPlatform(g, '3DS')).length.toLocaleString();
    document.getElementById('count-retro').textContent = allGames.filter(g => matchPlatform(g, 'Retro')).length.toLocaleString();
    document.getElementById('count-mods').textContent = allGames.filter(g => matchPlatform(g, 'Mods')).length.toLocaleString();
  }

  function resetAllFilters() {
    state.platform = 'all';
    state.category = 'all';
    state.mode = 'all';
    state.connection = 'all';
    state.difficulty = 'all';
    state.vibe = 'all';
    state.search = '';
    state.sort = 'couple-first';
    state.currentPage = 1;

    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    sortSelect.value = 'couple-first';
    filterMode.value = 'all';
    filterConnection.value = 'all';
    filterDifficulty.value = 'all';
    filterVibe.value = 'all';

    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.platform === 'all'));
    document.querySelectorAll('.cat-pill').forEach(p => p.classList.toggle('active', p.dataset.category === 'all'));

    renderGames();
  }
  window.resetAllFilters = resetAllFilters;

  // ==========================================
  // Game Detail Modal Logic
  // ==========================================

  window.openGameModal = function(gameId) {
    const game = allGames.find(g => g.id === gameId);
    if (!game) return;

    state.activeModalGameId = gameId;

    document.getElementById('modalTitle').textContent = game.title;
    document.getElementById('modalPlatform').textContent = game.platform || 'Multi-Platform';
    document.getElementById('modalCategory').textContent = game.category || 'Official Release';
    document.getElementById('modalCategory').className = `badge category-badge ${game.category.includes('Native') ? 'native' : game.category.includes('Emulation') ? 'emu' : 'mod'}`;

    document.getElementById('modalCoupleBadge').style.display = game.isCouplePick ? 'inline-block' : 'none';
    document.getElementById('modalGenre').textContent = game.genre || 'Action';
    document.getElementById('modalPlayers').textContent = `${game.maxPlayers || '2'} Players`;
    document.getElementById('modalRating').textContent = '★'.repeat(Math.floor(game.rating || 4.5)) + ` (${game.rating || 4.5}/5)`;

    // External SteamGridDB & IGDB links
    document.getElementById('modalSteamGridDbLink').href = game.steamGridDbUrl || `https://www.steamgriddb.com/search/grids?term=${encodeURIComponent(game.title)}`;
    document.getElementById('modalIgdbLink').href = game.igdbUrl || `https://www.igdb.com/search?q=${encodeURIComponent(game.title)}`;

    document.getElementById('modalHowItRelates').textContent = game.howItRelates || game.multiplayerFeatures || 'Multiplayer functionality available across supported hardware.';
    document.getElementById('modalSummary').textContent = game.summary;
    document.getElementById('modalSetupGuide').textContent = game.setupGuide;

    // Platform tags list
    const platsContainer = document.getElementById('modalPlatformsList');
    platsContainer.innerHTML = (game.platforms || [game.platform]).map(p => `
      <span class="platform-tag-item">${escapeHtml(p)}</span>
    `).join('');

    document.getElementById('modalConnection').textContent = game.connection;
    document.getElementById('modalMode').textContent = game.mode;
    document.getElementById('modalDifficulty').textContent = game.difficulty;
    document.getElementById('modalVibe').textContent = game.vibe;

    updateModalBookmarkBtn();

    modalBackdrop.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  };

  function closeGameModal() {
    modalBackdrop.style.display = 'none';
    document.body.style.overflow = '';
    state.activeModalGameId = null;
  }

  closeModalBtn.addEventListener('click', closeGameModal);
  modalCloseActionBtn.addEventListener('click', closeGameModal);
  modalBackdrop.addEventListener('click', (e) => {
    if (e.target === modalBackdrop) closeGameModal();
  });

  modalBookmarkBtn.addEventListener('click', () => {
    if (state.activeModalGameId) {
      window.toggleShortlist(state.activeModalGameId);
      updateModalBookmarkBtn();
    }
  });

  function updateModalBookmarkBtn() {
    if (!state.activeModalGameId) return;
    const isSaved = state.shortlist.has(state.activeModalGameId);
    modalBookmarkBtn.innerHTML = isSaved ? '⭐ Remove from Favorites' : '⭐ Save to Favorites';
    modalBookmarkBtn.className = isSaved ? 'btn btn-primary' : 'btn btn-secondary';
  }

  // ==========================================
  // Favorites / Shortlist Logic
  // ==========================================

  window.toggleShortlist = function(gameId, event) {
    if (event) event.stopPropagation();

    if (state.shortlist.has(gameId)) {
      state.shortlist.delete(gameId);
    } else {
      state.shortlist.add(gameId);
    }

    localStorage.setItem('duoplay_favs', JSON.stringify([...state.shortlist]));
    updateShortlistBadges();
    renderGames();
    renderShortlistDrawer();
  };

  function updateShortlistBadges() {
    const count = state.shortlist.size;
    shortlistCountEl.textContent = count;
    drawerCountEl.textContent = count;
  }

  function renderShortlistDrawer() {
    if (state.shortlist.size === 0) {
      shortlistItemsEl.innerHTML = '<p class="empty-drawer-text">You haven\'t bookmarked any games yet. Click the star icon on any game card to add it to your saved list!</p>';
      return;
    }

    const savedGames = allGames.filter(g => state.shortlist.has(g.id));
    shortlistItemsEl.innerHTML = savedGames.map(game => `
      <div class="shortlist-item">
        <div class="shortlist-item-info">
          <h5>${escapeHtml(game.title)}</h5>
          <span>${(game.platforms || [game.platform]).slice(0, 2).join(', ')} • ${game.vibe}</span>
        </div>
        <button class="btn btn-link btn-sm" onclick="toggleShortlist('${game.id}')" style="color: #ef4444;">
          Remove
        </button>
      </div>
    `).join('');
  }

  openShortlistBtn.addEventListener('click', () => {
    renderShortlistDrawer();
    shortlistBackdrop.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  });

  closeShortlistBtn.addEventListener('click', () => {
    shortlistBackdrop.style.display = 'none';
    document.body.style.overflow = '';
  });

  shortlistBackdrop.addEventListener('click', (e) => {
    if (e.target === shortlistBackdrop) {
      shortlistBackdrop.style.display = 'none';
      document.body.style.overflow = '';
    }
  });

  clearShortlistBtn.addEventListener('click', () => {
    state.shortlist.clear();
    localStorage.removeItem('duoplay_favs');
    updateShortlistBadges();
    renderGames();
    renderShortlistDrawer();
  });

  copyShortlistBtn.addEventListener('click', () => {
    const savedGames = allGames.filter(g => state.shortlist.has(g.id));
    if (savedGames.length === 0) {
      alert('Your favorites list is empty!');
      return;
    }
    const text = savedGames.map((g, i) => `${i + 1}. ${g.title} [${(g.platforms || [g.platform]).join(', ')}] - ${g.howItRelates || g.summary} (Setup: ${g.setupGuide})`).join('\n\n');
    navigator.clipboard.writeText(text).then(() => {
      alert('Favorites list copied to clipboard!');
    });
  });

  // ==========================================
  // Inclusive Co-Op Matchmaker Logic
  // ==========================================

  openMatchmakerBtn.addEventListener('click', () => {
    const isVisible = matchmakerSection.style.display === 'block';
    matchmakerSection.style.display = isVisible ? 'none' : 'block';
    if (!isVisible) {
      matchmakerSection.scrollIntoView({ behavior: 'smooth' });
    }
  });

  closeMatchmakerBtn.addEventListener('click', () => {
    matchmakerSection.style.display = 'none';
  });

  setupPillGroup('matchHardwareGroup');
  setupPillGroup('matchComfortGroup');
  setupPillGroup('matchVibeGroup');

  function setupPillGroup(groupId) {
    const container = document.getElementById(groupId);
    container.addEventListener('click', (e) => {
      const btn = e.target.closest('.pill');
      if (!btn) return;
      container.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
    });
  }

  generateMatchesBtn.addEventListener('click', () => {
    const hardware = document.querySelector('#matchHardwareGroup .pill.active').dataset.val;
    const comfort = document.querySelector('#matchComfortGroup .pill.active').dataset.val;
    const vibe = document.querySelector('#matchVibeGroup .pill.active').dataset.val;

    const candidates = allGames.map(game => {
      let score = 0;
      const plats = (game.platforms || [game.platform]).map(p => p.toLowerCase());

      // Console match
      if (hardware === 'switch' && plats.some(p => p.includes('switch'))) score += 20;
      if (hardware === 'pc' && plats.some(p => p.includes('pc') || p.includes('steam'))) score += 20;
      if (hardware === 'playstation' && plats.some(p => p.includes('playstation') || p.includes('ps'))) score += 20;
      if (hardware === 'xbox' && plats.some(p => p.includes('xbox'))) score += 20;
      if (hardware === '3ds' && plats.some(p => p.includes('3ds') || p.includes('ds'))) score += 20;
      if (hardware === 'any') score += 10;

      // Experience Comfort match
      if (comfort === 'beginner') {
        if (game.difficulty === 'Very Chill' || game.difficulty === 'Low') score += 20;
        if (game.difficulty === 'Hardcore') score -= 35;
      } else if (comfort === 'casual') {
        if (game.difficulty === 'Low' || game.difficulty === 'Medium') score += 15;
      } else if (comfort === 'gamer') {
        if (game.difficulty === 'Medium' || game.difficulty === 'Hardcore' || game.difficulty === 'High Chaos') score += 15;
      }

      // Vibe match
      if (vibe === 'cozy' && (game.vibe === 'Cozy & Relaxing' || game.vibe === 'Romantic & Emotional')) score += 25;
      if (vibe === 'story' && (game.vibe === 'Story & Adventure' || game.vibe === 'Romantic & Emotional')) score += 25;
      if (vibe === 'chaos' && game.vibe === 'Laugh-Out-Loud Chaos') score += 25;
      if (vibe === 'puzzle' && game.vibe === 'Brain-Teasers & Strategy') score += 25;
      if (vibe === 'action' && (game.vibe === 'Action & Combat' || game.vibe === 'Story & Adventure')) score += 25;

      // Duo pick recommendation bonus
      if (game.isCouplePick) score += 15;

      return { game, score };
    });

    candidates.sort((a, b) => b.score - a.score);
    const topMatches = candidates.slice(0, 3).map(c => c.game);

    matchCardsGrid.innerHTML = topMatches.map(m => `
      <div class="game-card" style="border-color: var(--cyan-accent);">
        <div class="card-top-bar">
          <span class="badge platform-badge">${escapeHtml((m.platforms || [m.platform])[0])}</span>
          <span class="badge couple-badge">Top Match</span>
        </div>
        <h4 style="font-size: 1.15rem; font-weight: 800; margin: 8px 0 4px;">${escapeHtml(m.title)}</h4>
        <p style="font-size: 0.825rem; color: var(--text-muted); margin-bottom: 12px;">${escapeHtml(m.summary)}</p>
        <div style="font-size: 0.775rem; background: rgba(255,255,255,0.04); padding: 8px 10px; border-radius: 6px; margin-bottom: 12px; border-left: 2px solid var(--cyan-accent);">
          <strong>Co-Op Setup:</strong> ${escapeHtml(m.setupGuide)}
        </div>
        <div style="display:flex; gap:8px; margin-bottom:12px;">
          <a href="${m.steamGridDbUrl}" target="_blank" rel="noopener" class="btn btn-outline btn-sm" style="flex:1; justify-content:center;">🖼️ SteamGridDB</a>
          <a href="${m.igdbUrl}" target="_blank" rel="noopener" class="btn btn-outline btn-sm" style="flex:1; justify-content:center;">🎮 IGDB</a>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="openGameModal('${m.id}')" style="width: 100%;">
          View Full Breakdown ➔
        </button>
      </div>
    `).join('');

    matchResultsContainer.style.display = 'block';
  });

  // Global ESC to close modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (modalBackdrop.style.display === 'flex') closeGameModal();
      if (shortlistBackdrop.style.display === 'flex') {
        shortlistBackdrop.style.display = 'none';
        document.body.style.overflow = '';
      }
    }
  });

  // Utility
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
