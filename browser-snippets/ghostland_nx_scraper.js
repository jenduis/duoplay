// GhostLand / NLib API Nintendo Switch Content & Player Count Extractor
// Run in DevTools Console (F12) on: https://nx-content.ghostland.at/?view=content&page=1
(async () => {
  console.log("Starting GhostLand extraction with camelCase player counts...");

  const tids = new Set();
  const allImgs = [...document.querySelectorAll("img")].map(i => i.src || "");
  const allLinks = [...document.querySelectorAll("a")].map(a => a.href || "");
  [...allImgs, ...allLinks].forEach(url => {
    const match = url.match(/\b0100[0-9A-Fa-f]{12}\b/);
    if (match) tids.add(match[0].toUpperCase());
  });

  const tidList = Array.from(tids);
  console.log(`Found ${tidList.length} unique Title IDs on screen.`);

  if (tidList.length === 0) {
    alert("No Title IDs found on screen. Make sure you are on a content page.");
    return;
  }

  const banner = document.createElement("div");
  banner.style.cssText = "position:fixed;top:15px;right:15px;z-index:999999;background:#090d16;color:#38bdf8;padding:14px 20px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.6);font-family:sans-serif;font-size:14px;border:1px solid #0284c7;";
  banner.innerText = `Fetching metadata for ${tidList.length} games...`;
  document.body.appendChild(banner);

  let detailedGames = [];

  for (let i = 0; i < tidList.length; i++) {
    const tid = tidList[i];
    banner.innerText = `[${i + 1}/${tidList.length}] Fetching ${tid}...`;

    try {
      const res = await fetch(`https://api.nlib.cc/nx/${tid}?lang=en`);
      if (res.status === 200) {
        const d = await res.json();

        let players = d.numberOfPlayers ?? d.players ?? d.number_of_players ?? null;
        if (!players && d.description) {
          const descMatch = d.description.match(/(\d+)\s*(?:players|player)/i);
          if (descMatch) players = parseInt(descMatch[1], 10);
        }
        if (!players) players = 1;

        const gameItem = {
          title_id: d.id || tid,
          name: d.name || "Unknown Title",
          number_of_players: players,
          is_multiplayer: Number(players) > 1,
          publisher: d.publisher || "",
          developer: d.developer || "",
          release_date: d.releaseDate || d.release_date || "",
          categories: Array.isArray(d.category) ? d.category.join(", ") : (d.category || ""),
          intro: d.intro || "",
          icon_url: `https://api.nlib.cc/nx/${tid}/icon/256/256`,
          banner_url: `https://api.nlib.cc/nx/${tid}/banner`
        };

        detailedGames.push(gameItem);
        console.log(`[${i + 1}/${tidList.length}] ${gameItem.name} — Players: ${gameItem.number_of_players}`);
      }
    } catch (err) {
      console.warn(`Error on TID ${tid}:`, err);
    }

    await new Promise(r => setTimeout(r, 140));
  }

  banner.innerText = `Complete! Downloaded ${detailedGames.length} game records.`;

  const jsonBlob = new Blob([JSON.stringify(detailedGames, null, 2)], { type: "application/json" });
  const aJson = document.createElement("a");
  aJson.href = URL.createObjectURL(jsonBlob);
  aJson.download = `ghostland_games_with_players.json`;
  document.body.appendChild(aJson);
  aJson.click();
  document.body.removeChild(aJson);

  if (detailedGames.length > 0) {
    const keys = ["title_id", "name", "number_of_players", "is_multiplayer", "categories", "publisher", "release_date", "icon_url"];
    const csvRows = [keys.join(",")];
    detailedGames.forEach(g => {
      const row = keys.map(k => `"${String(g[k] || '').replace(/"/g, '""')}"`);
      csvRows.push(row.join(","));
    });
    const csvBlob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const aCsv = document.createElement("a");
    aCsv.href = URL.createObjectURL(csvBlob);
    aCsv.download = `ghostland_games_with_players.csv`;
    document.body.appendChild(aCsv);
    aCsv.click();
    document.body.removeChild(aCsv);
  }

  setTimeout(() => banner.remove(), 4000);
  alert(`Finished! Extracted player counts for ${detailedGames.length} games.`);
})();
