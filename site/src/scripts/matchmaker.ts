export interface MatchmakerGame {
  id: string;
  title: string;
  platforms: ('switch' | 'switch2' | '3ds' | 'ds')[];
  maxPlayers: number | null;
  coop: {
    campaign: boolean;
    localMax: number | null;
    sameScreen: boolean;
    splitScreen: boolean;
    localWirelessMax: number | null;
    onlineMax: number | null;
    downloadPlay: boolean;
    gameShare: boolean;
    dropInOut: boolean | null;
  };
  editorial: {
    summary: string;
    coopSummary: string;
    setupGuide: string;
    vibe: string;
    difficulty: string;
    audiences: string[];
  };
  coverUrl: string | null;
  curatorPick: boolean;
}

export interface MatchmakerAnswers {
  hardware: string;    // '1-switch' | '2-switch' | 'switch2' | '1-3ds-dlplay' | '2-3ds'
  experience: string;  // 'beginner' | 'casual' | 'gamer'
  audience: string;    // 'partner' | 'friends' | 'kids' | 'party'
  vibe: string;        // 'cozy' | 'story' | 'chaos' | 'puzzle' | 'action' | 'any'
}

export interface MatchResult {
  game: MatchmakerGame;
  score: number;
  reasons: string[];
}

export function evaluateMatches(games: MatchmakerGame[], answers: MatchmakerAnswers): MatchResult[] {
  const results: MatchResult[] = [];

  for (const game of games) {
    const reasons: string[] = [];
    let score = 0;

    // Hard constraints based on hardware
    if (answers.hardware === '1-switch') {
      const isSwitch = game.platforms.includes('switch') || game.platforms.includes('switch2');
      const hasLocalSameOrSplit = (game.coop.localMax !== null && game.coop.localMax >= 2) ||
                                  game.coop.sameScreen || game.coop.splitScreen;
      if (!isSwitch || !hasLocalSameOrSplit) {
        continue; // HARD FAIL: cannot play together on 1 Switch
      }
      score += 20;
      reasons.push('Supports same-console multiplayer on 1 Switch');
    } else if (answers.hardware === '2-switch') {
      const isSwitch = game.platforms.includes('switch') || game.platforms.includes('switch2');
      const hasWirelessOrOnline = (game.coop.localWirelessMax !== null && game.coop.localWirelessMax >= 2) ||
                                  (game.coop.onlineMax !== null && game.coop.onlineMax >= 2);
      if (!isSwitch || !hasWirelessOrOnline) {
        continue;
      }
      score += 20;
      reasons.push('Supports 2-console local wireless or online play');
    } else if (answers.hardware === 'switch2') {
      const isSwitch2 = game.platforms.includes('switch2');
      if (!isSwitch2 && !game.coop.gameShare) {
        // Must be Switch 2 or explicitly support GameShare
        continue;
      }
      score += 25;
      reasons.push('Features Switch 2 GameShare or next-gen capabilities');
    } else if (answers.hardware === '1-3ds-dlplay') {
      const is3dsOrDs = game.platforms.includes('3ds') || game.platforms.includes('ds');
      if (!is3dsOrDs || !game.coop.downloadPlay) {
        continue; // HARD FAIL: Must support Download Play!
      }
      score += 30;
      reasons.push('Single-cartridge 3DS Download Play (guest joins free)');
    } else if (answers.hardware === '2-3ds') {
      const is3dsOrDs = game.platforms.includes('3ds') || game.platforms.includes('ds');
      const hasWireless = (game.coop.localWirelessMax !== null && game.coop.localWirelessMax >= 2) ||
                          game.coop.downloadPlay;
      if (!is3dsOrDs || !hasWireless) {
        continue;
      }
      score += 20;
      reasons.push('Dedicated 3DS/DS local wireless multiplayer');
    }

    // Experience match
    if (answers.experience === 'beginner') {
      if (game.editorial.difficulty === 'Very Chill') {
        score += 25;
        reasons.push('Extremely accessible with zero gamer stress');
      } else if (game.editorial.difficulty === 'Low') {
        score += 15;
        reasons.push('Forgiving controls and gentle learning curve');
      } else if (game.editorial.difficulty === 'Hard') {
        score -= 25;
      }
    } else if (answers.experience === 'casual') {
      if (game.editorial.difficulty === 'Low' || game.editorial.difficulty === 'Medium') {
        score += 20;
        reasons.push('Great balanced challenge for casual players');
      }
    } else if (answers.experience === 'gamer') {
      if (game.editorial.difficulty === 'Medium' || game.editorial.difficulty === 'Hard') {
        score += 20;
        reasons.push('Deep mechanics and rewarding challenge');
      }
    }

    // Audience match
    const targetAudience = answers.audience;
    const audienceMap: Record<string, string> = {
      partner: 'couples',
      friends: 'friends',
      kids: 'kids',
      party: 'party'
    };
    const mappedAudience = audienceMap[targetAudience] || targetAudience;
    if (game.editorial.audiences.includes(mappedAudience)) {
      score += 20;
      reasons.push(`Handcrafted recommendation for ${targetAudience}`);
    }

    // Vibe match
    if (answers.vibe !== 'any') {
      const v = answers.vibe.toLowerCase();
      const gv = (game.editorial.vibe || '').toLowerCase();
      if (gv.includes(v)) {
        score += 25;
        reasons.push(`Matches your requested "${game.editorial.vibe}" vibe`);
      }
    }

    // Campaign bonus
    if (game.coop.campaign) {
      score += 10;
    }

    // Curator pick bonus
    if (game.curatorPick) {
      score += 10;
      reasons.push("Curator's verified recommendation");
    }

    results.push({
      game,
      score,
      reasons: reasons.slice(0, 3)
    });
  }

  results.sort((a, b) => b.score - a.score);
  return results.slice(0, 6);
}
