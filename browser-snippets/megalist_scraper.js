// Unofficial Multiplayer Mods Mega-List (MPM) Scraper
// Run in DevTools Console (F12) on: https://megalist.neocities.org/mpm
(async () => {
  console.log("Extracting Unofficial Multiplayer Mods Mega-List...");
  let mods = [];

  const rows = document.querySelectorAll("table tr");
  rows.forEach(r => {
    const cells = [...r.querySelectorAll("td, th")].map(c => c.innerText.trim());
    const links = [...r.querySelectorAll("a")].map(a => a.href);
    if (cells.length >= 2 && cells[0].toLowerCase() !== "game") {
      mods.push({
        title: cells[0],
        mod_name: cells[1] || "",
        details: cells[2] || "",
        links: links,
        source: "DOM Table"
      });
    }
  });

  const scripts = [...document.querySelectorAll("script")].map(s => s.innerText);
  for (const s of scripts) {
    const match = s.match(/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
    if (match) {
      const sheetId = match[1];
      console.log("Found embedded Google Sheet backend:", sheetId);
      try {
        const res = await fetch(`https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:json`);
        const text = await res.text();
        const jsonText = text.substring(text.indexOf("{"), text.lastIndexOf("}") + 1);
        const data = JSON.parse(jsonText);
        
        data.table.rows.forEach(row => {
          const c = row.c.map(cell => cell ? (cell.v || cell.f || "") : "");
          if (c[0] && c[0] !== "Game") {
            mods.push({
              title: String(c[0]).trim(),
              mod_name: String(c[1] || "").trim(),
              details: String(c[2] || "").trim(),
              source: "Live Google Sheet"
            });
          }
        });
      } catch (err) {
        console.warn("Could not query direct Sheet endpoint:", err);
      }
    }
  }

  const unique = [];
  const seen = new Set();
  mods.forEach(m => {
    if (!seen.has(m.title.toLowerCase())) {
      seen.add(m.title.toLowerCase());
      unique.push(m);
    }
  });

  const blob = new Blob([JSON.stringify(unique, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "megalist_multiplayer_mods.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  alert(`Extracted ${unique.length} multiplayer mods!`);
})();
