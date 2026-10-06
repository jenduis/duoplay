// Co-Optimus DevTools Multi-Page Console Scraper
// Usage:
// 1. Open DevTools (F12 or Cmd+Option+I) -> Console tab on any Co-Optimus games list page:
//    - Switch:   https://www.co-optimus.com/games.php?system=28
//    - 3DS:      https://www.co-optimus.com/games.php?system=20
//    - DS:       https://www.co-optimus.com/games.php?system=17
// 2. Paste this entire script and press Enter.
// 3. Keep the tab active. When finished, it will automatically download:
//    `cooptimus_<system>.json`
// 4. Move the downloaded JSON file into `data/raw/` in this repository.

(async () => {
  console.log("Starting DuoPlay Co-Optimus extractor...");

  // Detect system from query string
  const urlParams = new URLSearchParams(window.location.search);
  const systemId = urlParams.get("system") || "unknown";
  const systemMap = {
    "28": "switch",
    "20": "3ds",
    "17": "ds",
    "32": "switch2" // placeholder if Co-Optimus adds Switch 2 ID
  };
  const systemName = systemMap[systemId] || `system_${systemId}`;

  let allGames = JSON.parse(sessionStorage.getItem(`coop_cache_${systemName}`) || "[]");
  const seen = new Set(allGames.map(g => g.title.toLowerCase()));

  const banner = document.createElement("div");
  banner.style.cssText = "position:fixed;top:15px;right:15px;z-index:999999;background:#0f172a;color:#38bdf8;padding:14px 20px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.5);font-family:sans-serif;font-size:14px;border:1px solid #0284c7;";
  banner.innerText = `Starting extraction for ${systemName.toUpperCase()}...`;
  document.body.appendChild(banner);

  function parseRow(row, pageNum, dateText) {
    const titleLink = row.querySelector("a[href*='/game/']");
    const title = titleLink ? titleLink.innerText.trim() : (row.innerText.split("\n")[0] || "").trim();
    if (!title || seen.has(title.toLowerCase())) return null;

    seen.add(title.toLowerCase());
    const relUrl = titleLink ? (titleLink.getAttribute("href") || "") : "";
    const fullUrl = relUrl.startsWith("http") ? relUrl : (relUrl ? `https://www.co-optimus.com${relUrl}` : "");

    // Extract table columns if table-based
    const cols = [...row.querySelectorAll("td")].map(td => td.innerText.trim());
    
    // Extract feature icons or images with alt/title
    const icons = [...row.querySelectorAll("img, i, span[title], span[data-original-title]")].map(el => {
      return el.getAttribute("title") || el.getAttribute("data-original-title") || el.getAttribute("alt") || "";
    }).filter(t => t.length > 0);

    const details = row.innerText.replace(/[\n\r\t]+/g, " | ").trim();

    return {
      title: title,
      system: systemName,
      url: fullUrl,
      release_date: dateText || (cols[3] || ""),
      columns: cols,
      features: [...new Set(icons)],
      details: details,
      page: pageNum
    };
  }

  function scrapeVisibleScreen(pageNum) {
    let count = 0;
    // Method 1: Check standard table rows
    const tableRows = document.querySelectorAll("table.game-list tbody tr, table.table tbody tr, #game-table tr");
    if (tableRows.length > 0) {
      tableRows.forEach(row => {
        const item = parseRow(row, pageNum, null);
        if (item) {
          allGames.push(item);
          count++;
        }
      });
    } else {
      // Method 2: Date node ancestor crawling fallback
      const dateNodes = [...document.querySelectorAll("*")].filter(el => {
        return el.children.length === 0 && /^\d{2}\/\d{2}\/\d{4}$/.test(el.innerText.trim());
      });

      dateNodes.forEach(dateEl => {
        let row = dateEl.parentElement;
        while (row && row !== document.body && row.querySelectorAll("*").length < 5) {
          row = row.parentElement;
        }
        if (!row) return;

        const item = parseRow(row, pageNum, dateEl.innerText.trim());
        if (item) {
          allGames.push(item);
          count++;
        }
      });
    }

    sessionStorage.setItem(`coop_cache_${systemName}`, JSON.stringify(allGames));
    return count;
  }

  // Detect total pages if possible from pagination
  let detectedTotalPages = 1;
  const pageLinks = [...document.querySelectorAll(".pagination a, a[onclick*='setPage']")];
  pageLinks.forEach(a => {
    const match = (a.innerText || "").match(/\b\d+\b/) || (a.getAttribute("onclick") || "").match(/setPage\((\d+)\)/);
    if (match) {
      const num = parseInt(match[1] || match[0], 10);
      if (num > detectedTotalPages && num < 500) detectedTotalPages = num;
    }
  });

  console.log(`Detected approx total pages: ${detectedTotalPages}`);

  // Page 1 scrape
  scrapeVisibleScreen(1);
  console.log(`Page 1 captured. Total: ${allGames.length} games.`);

  let p = 2;
  const maxSafetyPage = detectedTotalPages > 1 ? detectedTotalPages : 100;

  while (p <= maxSafetyPage) {
    banner.innerText = `Extracting ${systemName.toUpperCase()}: Page ${p}/${maxSafetyPage}... (${allGames.length} games captured)`;
    console.log(`Calling native setPage('${p}')...`);

    try {
      if (typeof window.setPage === "function") {
        window.setPage(String(p));
      } else {
        console.warn("setPage() is not defined on window. Attempting pagination click...");
        const targetLink = pageLinks.find(a => (a.innerText || "").trim() === String(p));
        if (targetLink) targetLink.click();
        else break;
      }

      await new Promise(r => setTimeout(r, 1500));

      let added = scrapeVisibleScreen(p);
      console.log(`Page ${p} loaded: Found ${added} new games. (Total: ${allGames.length})`);

      if (added === 0) {
        await new Promise(r => setTimeout(r, 2000));
        added = scrapeVisibleScreen(p);
        if (added === 0) {
          console.log(`No new entries for page ${p}. Reached end of catalog.`);
          break;
        }
      }
      p++;
    } catch (err) {
      console.error(`Error on page ${p}:`, err);
      break;
    }
  }

  banner.innerText = `Complete! Saving ${allGames.length} games for ${systemName}...`;

  const filename = `cooptimus_${systemName}.json`;
  const jsonBlob = new Blob([JSON.stringify(allGames, null, 2)], { type: "application/json" });
  const aJson = document.createElement("a");
  aJson.href = URL.createObjectURL(jsonBlob);
  aJson.download = filename;
  document.body.appendChild(aJson);
  aJson.click();
  document.body.removeChild(aJson);

  sessionStorage.removeItem(`coop_cache_${systemName}`);
  setTimeout(() => banner.remove(), 4000);
  alert(`Success! Extracted ${allGames.length} games for ${systemName}. File saved as: ${filename}`);
})();
