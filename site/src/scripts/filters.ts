export interface SlimGame {
  id: string;
  title: string;
  platforms: string[];
  maxPlayers: number | null;
  coop: {
    campaign: boolean;
    sameScreen: boolean;
    splitScreen: boolean;
    localWireless: boolean;
    online: boolean;
    downloadPlay: boolean;
    gameShare: boolean;
  };
  versus: boolean;
  genres: string[];
  vibe: string;
  difficulty: string;
  audiences: string[];
  curatorPick: boolean;
  coverUrl: string | null;
  summary: string;
}

export interface FilterState {
  platform: string;     // 'all' | 'switch' | '3ds' | 'ds'
  playStyle: string;    // 'all' | 'same-screen' | 'split-screen' | 'local-wireless' | 'online' | 'download-play'
  campaignOnly: boolean;
  minPlayers: number;
  vibe: string;
  difficulty: string;
  audience: string;
  search: string;
  sort: string;
}

export function filterAndSortGames(games: SlimGame[], state: FilterState): SlimGame[] {
  const query = state.search.trim().toLowerCase();

  return games.filter(g => {
    // Platform
    if (state.platform !== 'all' && !g.platforms.includes(state.platform)) {
      return false;
    }

    // Play Style
    if (state.playStyle !== 'all') {
      if (state.playStyle === 'same-screen' && !g.coop.sameScreen) return false;
      if (state.playStyle === 'split-screen' && !g.coop.splitScreen) return false;
      if (state.playStyle === 'local-wireless' && !g.coop.localWireless) return false;
      if (state.playStyle === 'online' && !g.coop.online) return false;
      if (state.playStyle === 'download-play' && !g.coop.downloadPlay) return false;
    }

    // Campaign only
    if (state.campaignOnly && !g.coop.campaign) {
      return false;
    }

    // Minimum Players
    if (state.minPlayers > 1 && (g.maxPlayers || 0) < state.minPlayers) {
      return false;
    }

    // Vibe
    if (state.vibe !== 'all' && g.vibe !== state.vibe) {
      return false;
    }

    // Difficulty
    if (state.difficulty !== 'all' && g.difficulty !== state.difficulty) {
      return false;
    }

    // Audience
    if (state.audience !== 'all' && !g.audiences.includes(state.audience)) {
      return false;
    }

    // Search query
    if (query) {
      const match = g.title.toLowerCase().includes(query) ||
                    g.genres.some(genre => genre.toLowerCase().includes(query)) ||
                    g.summary.toLowerCase().includes(query);
      if (!match) return false;
    }

    return true;
  }).sort((a, b) => {
    if (state.sort === 'curator') {
      if (a.curatorPick !== b.curatorPick) return b.curatorPick ? 1 : -1;
      return a.title.localeCompare(b.title);
    }
    if (state.sort === 'title-asc') {
      return a.title.localeCompare(b.title);
    }
    if (state.sort === 'players-desc') {
      return (b.maxPlayers || 0) - (a.maxPlayers || 0);
    }
    return 0;
  });
}
