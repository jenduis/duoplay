import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

export const GET: APIRoute = async () => {
  const allGames = await getCollection('games');

  const slim = allGames.map(entry => {
    const g = entry.data;
    return {
      id: g.id,
      title: g.title,
      platforms: g.platforms,
      maxPlayers: g.maxPlayers,
      coop: {
        campaign: g.coop.campaign,
        sameScreen: g.coop.local.sameScreen,
        splitScreen: g.coop.local.splitScreen,
        localWireless: (g.coop.localWireless.max || 0) > 1,
        online: (g.coop.online.max || 0) > 1,
        downloadPlay: g.coop.downloadPlay,
        gameShare: g.coop.gameShare,
      },
      versus: g.versus,
      genres: g.genres.slice(0, 3),
      vibe: g.editorial.vibe,
      difficulty: g.editorial.difficulty,
      audiences: g.editorial.audiences,
      curatorPick: g.curatorPick,
      coverUrl: g.cover?.url || null,
      summary: g.editorial.summary,
    };
  });

  return new Response(JSON.stringify(slim), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
};
