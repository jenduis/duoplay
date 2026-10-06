import { defineCollection, z } from 'astro:content';
import { file, glob } from 'astro/loaders';

const games = defineCollection({
  loader: file('../data/games.json'),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    platforms: z.array(z.enum(['switch', 'switch2', '3ds', 'ds'])).min(1),
    coop: z.object({
      campaign: z.boolean(),
      local: z.object({
        max: z.number().nullable(),
        sameScreen: z.boolean(),
        splitScreen: z.boolean(),
      }),
      localWireless: z.object({
        max: z.number().nullable(),
      }),
      online: z.object({
        max: z.number().nullable(),
      }),
      downloadPlay: z.boolean(),
      gameShare: z.boolean(),
      dropInOut: z.boolean().nullable(),
    }),
    versus: z.boolean(),
    maxPlayers: z.number().nullable(),
    genres: z.array(z.string()),
    releaseDate: z.string().nullable(),
    publisher: z.string().nullable(),
    ids: z.object({
      switchTitleId: z.string().optional(),
      nsuId: z.string().optional(),
      ctrProductCode: z.string().optional(),
      cooptimusUrl: z.string().optional(),
    }),
    cover: z.object({
      url: z.string(),
      source: z.enum(['titledb', 'nlib', 'gametdb', 'manual']),
    }).nullable(),
    curatorPick: z.boolean(),
    editorial: z.object({
      summary: z.string(),
      coopSummary: z.string(),
      setupGuide: z.string(),
      vibe: z.enum(['Cozy', 'Story', 'Chaos', 'Puzzle', 'Action', 'Competitive']),
      difficulty: z.enum(['Very Chill', 'Low', 'Medium', 'Hard']),
      audiences: z.array(z.enum(['couples', 'friends', 'kids', 'family', 'party'])),
      aiGenerated: z.boolean(),
      reviewed: z.boolean(),
    }),
    sources: z.array(z.string()),
    updatedAt: z.string(),
  }),
});

const guides = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/guides' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    icon: z.string(),
    order: z.number().default(0),
  }),
});

export const collections = { games, guides };
