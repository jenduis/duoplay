import { describe, it, expect } from 'vitest';
import { filterAndSortGames, type SlimGame, type FilterState } from './filters';

const mockGames: SlimGame[] = [
  {
    id: 'mario-kart-7',
    title: 'Mario Kart 7',
    platforms: ['3ds'],
    maxPlayers: 8,
    coop: {
      campaign: false,
      sameScreen: false,
      splitScreen: false,
      localWireless: true,
      online: true,
      downloadPlay: true,
      gameShare: false,
    },
    versus: true,
    genres: ['Racing'],
    vibe: 'Competitive',
    difficulty: 'Low',
    audiences: ['friends', 'family'],
    curatorPick: true,
    coverUrl: 'https://example.com/mk7.png',
    summary: '3DS racing game.',
  },
  {
    id: 'it-takes-two',
    title: 'It Takes Two',
    platforms: ['switch'],
    maxPlayers: 2,
    coop: {
      campaign: true,
      sameScreen: true,
      splitScreen: true,
      localWireless: false,
      online: true,
      downloadPlay: false,
      gameShare: false,
    },
    versus: false,
    genres: ['Platformer', 'Adventure'],
    vibe: 'Story',
    difficulty: 'Medium',
    audiences: ['couples', 'friends'],
    curatorPick: true,
    coverUrl: 'https://example.com/itt.png',
    summary: 'Award-winning co-op adventure.',
  },
];

const defaultState: FilterState = {
  platform: 'all',
  playStyle: 'all',
  campaignOnly: false,
  minPlayers: 1,
  vibe: 'all',
  difficulty: 'all',
  audience: 'all',
  search: '',
  sort: 'curator',
};

describe('filterAndSortGames', () => {
  it('filters by platform correctly', () => {
    const res = filterAndSortGames(mockGames, { ...defaultState, platform: '3ds' });
    expect(res.length).toBe(1);
    expect(res[0].id).toBe('mario-kart-7');
  });

  it('filters by single-card Download Play correctly', () => {
    const res = filterAndSortGames(mockGames, { ...defaultState, playStyle: 'download-play' });
    expect(res.length).toBe(1);
    expect(res[0].id).toBe('mario-kart-7');
  });

  it('filters by co-op campaign correctly', () => {
    const res = filterAndSortGames(mockGames, { ...defaultState, campaignOnly: true });
    expect(res.length).toBe(1);
    expect(res[0].id).toBe('it-takes-two');
  });
});
