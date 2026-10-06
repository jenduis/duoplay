const STORAGE_KEY_V2 = 'duoplay_favs_v2';
const STORAGE_KEY_V1 = 'duoplay_favs';

export function getFavorites(): string[] {
  try {
    const rawV2 = localStorage.getItem(STORAGE_KEY_V2);
    if (rawV2) {
      return JSON.parse(rawV2);
    }

    // Auto-migration from v1
    const rawV1 = localStorage.getItem(STORAGE_KEY_V1);
    if (rawV1) {
      const parsed = JSON.parse(rawV1);
      if (Array.isArray(parsed)) {
        localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(parsed));
        return parsed;
      }
    }
  } catch (err) {
    console.error('Failed to parse favorites:', err);
  }
  return [];
}

export function saveFavorites(favs: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY_V2, JSON.stringify(favs));
    window.dispatchEvent(new Event('storage'));
  } catch (err) {
    console.error('Failed to save favorites:', err);
  }
}

export function isFavorite(id: string): boolean {
  return getFavorites().includes(id);
}

export function toggleFavorite(id: string): boolean {
  const favs = getFavorites();
  const idx = favs.indexOf(id);
  let nowFavorite = false;

  if (idx >= 0) {
    favs.splice(idx, 1);
  } else {
    favs.push(id);
    nowFavorite = true;
  }

  saveFavorites(favs);
  return nowFavorite;
}

export function clearFavorites(): void {
  saveFavorites([]);
}
