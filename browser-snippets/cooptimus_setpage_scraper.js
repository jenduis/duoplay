// Co-Optimus Native setPage() Multi-Page Scraper
// Run in DevTools Console (F12) on: https://www.co-optimus.com/games.php?system=28 (or any system)
(async () => {
  console.log("Starting native setPage() Co-Optimus extractor...");

  let allGames = JSON.parse(sessionStorage.getItem("coop_cache") || "[]");
  const seen = new Set(allGames.map(g => g.title.toLowerCase()));

  const banner = document.createElement("div");
  banner.style.cssText = "position:fixed;top:15px;right:15px;z-index:999999;background:#0f172a;color:#38bdf8;padding:14px 20px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.5);font-family:sans-serif;font-size:14px;border:1px solid #0284c7;";
  banner.innerText = "Starting extraction...";
  document.body.appendChild(banner);

  function scrapeVisibleScreen(pageNum) {
    const dateNodes = [...document.querySelectorAll("*")].filter(el => {
      return el.children.length === 0 && /^\d{2}\/\d{2}\/\d{4}$/.test(el.innerText.trim());
    });

    let count = 0;
    dateNodes.forEach(dateEl => {
      let row = dateEl.parentElement;
      while (row && row !== document.body && row.querySelectorAll("*").length < 5) {
        row = row.parentElement;
      }
      if (!row) return;

      const links = [...row.querySelectorAll("a")].filter(a => {
        const txt = a.innerText.trim();
        return txt.length > 1 && !txt.includes("http") && !txt.includes("SHARE");
      });

      const link = links[0];
      const title = link ? link.innerText.trim() : (row.innerText.split("\n")[0] || "").trim();

      if (title && !seen.has(title.toLowerCase())) {
        seen.add(title.toLowerCase());
        const href = link ? (link.href || link.getAttribute("href") || "") : "";
        const details = row.innerText.replace(/[\n\r\t]+/g, " | ").trim();

        allGames.push({
          title: title,
          url: href.startsWith("http") ? href : `https://www.co-optimus.com${href}`,
          release_date: dateEl.innerText.trim(),
          page: pageNum,
          details: details
        });
        count++;
      }
    });

    sessionStorage.setItem("coop_cache", JSON.stringify(allGames));
    return count;
  }

  scrapeVisibleScreen(1);
  console.log(`Page 1 captured. Total: ${allGames.length} games.`);

  const totalPages = 84;

  for (let p = 2; p <= totalPages; p++) {
    banner.innerText = `Extracting Co-Optimus: Page ${p}/${totalPages}... (${allGames.length} games captured)`;
    console.log(`Calling native setPage('${p}')...`);

    try {
      window.setPage(String(p));
      await new Promise(r => setTimeout(r, 1400));

      const added = scrapeVisibleScreen(p);
      console.log(`Page ${p} loaded: Found ${added} new games. (Total: ${allGames.length})`);

      if (added === 0) {
        await new Promise(r => setTimeout(r, 1500));
        const retryAdded = scrapeVisibleScreen(p);
        if (retryAdded === 0) {
          console.log(`No new entries rendered for page ${p}. Reached end.`);
          break;
        }
      }
    } catch (err) {
      console.error(`Error on page ${p}:`, err);
      break;
    }
  }

  banner.innerText = `Complete! Saving ${allGames.length} games...`;

  const jsonBlob = new Blob([JSON.stringify(allGames, null, 2)], { type: "application/json" });
  const aJson = document.createElement("a");
  aJson.href = URL.createObjectURL(jsonBlob);
  aJson.download = `cooptimus_all_switch_games.json`;
  document.body.appendChild(aJson);
  aJson.click();
  document.body.removeChild(aJson);

  if (allGames.length > 0) {
    const keys = ["title", "release_date", "page", "url", "details"];
    const csvRows = [keys.join(",")];
    allGames.forEach(g => {
      const row = keys.map(k => `"${String(g[k] || '').replace(/"/g, '""')}"`);
      csvRows.push(row.join(","));
    });
    const csvBlob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const aCsv = document.createElement("a");
    aCsv.href = URL.createObjectURL(csvBlob);
    aCsv.download = `cooptimus_all_switch_games.csv`;
    document.body.appendChild(aCsv);
    aCsv.click();
    document.body.removeChild(aCsv);
  }

  sessionStorage.removeItem("coop_cache");
  setTimeout(() => banner.remove(), 4000);
  alert(`Success! Extracted ${allGames.length} games across ${totalPages} pages.`);
})();
