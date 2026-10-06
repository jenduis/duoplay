import { describe, it, expect } from 'vitest';
import { evaluateMatches, type MatchmakerGame, type MatchmakerAnswers } from './matchmaker';

const mockGames: MatchmakerGame[] = [
  {
    id: 'it-takes-two',
    title: 'It Takes Two',
    platforms: ['switch'],
    maxPlayers: 2,
    coop: {
      campaign: true,
      localMax: 2,
      sameScreen: true,
      splitScreen: true,
      localWirelessMax: 2,
      onlineMax: 2,
      downloadPlay: false,
      gameShare: false,
      dropInOut: true,
    },
    editorial: {
      summary: 'Pure co-op adventure',
      coopSummary: 'Two player split-screen adventure',
      setupGuide: 'Joy-con per player',
      vibe: 'Action',
      difficulty: 'Medium',
      audiences: ['couples', 'friends'],
    },
    coverUrl: null,
    curatorPick: true,
  },
  {
    id: 'mario-kart-7',
    title: 'Mario Kart 7',
    platforms: ['3ds'],
    maxPlayers: 8,
    coop: {
      campaign: false,
      localMax: null,
      sameScreen: false,
      splitScreen: false,
      localWirelessMax: 8,
      onlineMax: 8,
      downloadPlay: true,
      gameShare: false,
      dropInOut: null,
    },
    editorial: {
      summary: 'Iconic handheld racer',
      coopSummary: 'Race together with 1 cartridge',
      setupGuide: 'Host 3DS opens Download Play room',
      vibe: 'Chaos',
      difficulty: 'Low',
      audiences: ['friends', 'kids', 'party'],
    },
    coverUrl: null,
    curatorPick: true,
  },
  {
    id: 'snipperclips',
    title: 'Snipperclips',
    platforms: ['switch'],
    maxPlayers: 4,
    coop: {
      campaign: true,
      localMax: 4,
      sameScreen: true,
      splitScreen: false,
      localWirelessMax: null,
      onlineMax: null,
      downloadPlay: false,
      gameShare: false,
      dropInOut: true,
    },
    editorial: {
      summary: 'Creative paper puzzles',
      coopSummary: 'Cut each other into shapes',
      setupGuide: 'Pass a horizontal Joy-Con to player 2',
      vibe: 'Puzzle',
      difficulty: 'Low',
      audiences: ['couples', 'kids'],
    },
    coverUrl: null,
    curatorPick: true,
  }
];

describe('evaluateMatches', () => {
  it('strictly requires Download Play when 1-3ds-dlplay is selected', () => {
    const answers: MatchmakerAnswers = {
      hardware: '1-3ds-dlplay',
      experience: 'casual',
      audience: 'friends',
      vibe: 'any',
    };

    const matches = evaluateMatches(mockGames, answers);
    expect(matches.length).toBe(1);
    expect(matches[0].game.id).toBe('mario-kart-7');
    expect(matches[0].game.coop.downloadPlay).toBe(true);
  });

  it('filters out non-local games when 1-switch is selected', () => {
    const answers: MatchmakerAnswers = {
      hardware: '1-switch',
      experience: 'casual',
      audience: 'partner',
      vibe: 'any',
    };

    const matches = evaluateMatches(mockGames, answers);
    expect(matches.length).toBe(2);
    expect(matches.map(m => m.game.id)).toContain('it-takes-two');
    expect(matches.map(m => m.game.id)).toContain('snipperclips');
    expect(matches.map(m => m.game.id)).not.toContain('mario-kart-7');
  });

  it('boosts games matching vibe and beginner difficulty', () => {
    const answers: MatchmakerAnswers = {
      hardware: '1-switch',
      experience: 'beginner',
      audience: 'partner',
      vibe: 'puzzle',
    };

    const matches = evaluateMatches(mockGames, answers);
    expect(matches[0].game.id).toBe('snipperclips');
  });
});
