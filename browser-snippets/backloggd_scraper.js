// Backloggd 24-Page Scraper Snippet
// Run in Firefox / Chrome DevTools Console (F12) while on:
// https://backloggd.com/u/mogwai/list/bestoarkadalarla-dene-ultimate-coop-list/
(async () => {
  console.log("Starting Backloggd 24-page extraction...");
  const basePath = window.location.pathname.replace(/\/$/, "");
  let games = [];
  const totalPages = 24;

  const banner = document.createElement("div");
  banner.style.cssText = "position:fixed;top:15px;right:15px;z-index:999999;background:#1e293b;color:#fff;padding:14px 20px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.4);font-family:sans-serif;font-size:14px;";
  banner.innerText = "Extracting Backloggd (Page 1/24)...";
  document.body.appendChild(banner);

  for (let page = 1; page <= totalPages; page++) {
    banner.innerText = `Extracting Backloggd (Page ${page}/${totalPages})... [${games.length} titles found]`;
    try {
      const res = await fetch(`${basePath}?page=${page}`);
      const text = await res.text();
      const doc = new DOMParser().parseFromString(text, "text/html");

      const cards = doc.querySelectorAll(".card, .game-card, .game-cover, a[href*='/games/']");
      let seenOnPage = new Set();

      cards.forEach(card => {
        const title = card.getAttribute("aria-label") || card.getAttribute("title") || card.innerText.trim();
        const href = card.getAttribute("href") || card.querySelector("a")?.getAttribute("href") || "";
        
        if (title && title.length > 1 && !title.includes("Reviews") && !title.includes("Backloggd") && !seenOnPage.has(title)) {
          seenOnPage.add(title);
          games.push({
            title: title.replace(/[\n\r]+/g, " ").trim(),
            url: href.startsWith("http") ? href : `https://backloggd.com${href}`,
            page: page
          });
        }
      });

      console.log(`Page ${page}/${totalPages} complete.`);
      await new Promise(r => setTimeout(r, 600));
    } catch (err) {
      console.error(`Error on page ${page}:`, err);
    }
  }

  const uniqueMap = new Map();
  games.forEach(g => { if (!uniqueMap.has(g.title)) uniqueMap.set(g.title, g); });
  const finalGames = Array.from(uniqueMap.values());

  banner.innerText = `Done! Saving ${finalGames.length} unique games...`;

  // 1. Download JSON
  const blob = new Blob([JSON.stringify(finalGames, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "backloggd_coop_full_list.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // 2. Download plain text list of titles (sorted)
  const titlesList = finalGames.map(g => g.title).sort().join("\n");
  const txtBlob = new Blob([titlesList], { type: "text/plain;charset=utf-8;" });
  const aTxt = document.createElement("a");
  aTxt.href = URL.createObjectURL(txtBlob);
  aTxt.download = "backloggd_titles.txt";
  document.body.appendChild(aTxt);
  aTxt.click();
  document.body.removeChild(aTxt);

  setTimeout(() => banner.remove(), 4000);
})();
