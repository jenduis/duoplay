# DuoPlay — Nintendo Switch & 3DS Multiplayer & Co-Op Explorer 🎮✨

An interactive, responsive web application and comprehensive database of **267 local, wireless, and co-op games** for **Nintendo Switch** and **Nintendo 3DS / DS**, specially designed for date nights, couples, and multiplayer sessions.

Cross-referenced across Backloggd, Co-Optimus, Nintendo databases, and the Unofficial Multiplayer Mods Megalist.

---

## 🚀 Instant Deployment to Vercel

This repository is pre-configured with `vercel.json` for 1-click zero-config static hosting.

### Method 1: Deploy with Vercel CLI (Fastest)

1. Open your terminal in this directory:
   ```bash
   cd duoplay-app
   ```
2. Run:
   ```bash
   npx vercel
   ```
3. Follow the CLI prompts (default settings: `Y`, link project, deploy). Your live production URL will be ready in seconds!

### Method 2: Deploy via GitHub / GitLab

1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of DuoPlay Co-Op Explorer"
   git branch -M main
   git remote add origin https://github.com/your-username/duoplay-app.git
   git push -u origin main
   ```
2. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**.
3. Import your `duoplay-app` repository.
4. Leave all build settings at their defaults (Framework Preset: **Other**, Root Directory: `./`).
5. Click **Deploy**.

### Method 3: Drag & Drop via Vercel Dashboard

1. Zip the contents of the `duoplay-app` folder.
2. Go to [vercel.com/new](https://vercel.com/new).
3. Drag and drop the folder directly into the browser.

---

## 🌟 Key Features

1. **267 Curated Multiplayer Titles:**
   - **Nintendo Switch (180+ titles):** Couch co-op, split-screen, and local wireless across multiple consoles.
   - **Nintendo 3DS & DS (75+ titles):** Highlighting 30+ verified **Download Play (Single-Cartridge)** titles where only one person needs the game card.
   - **Emulation & Virtual Console (NSO / RetroArch):** 16-bit and 64-bit co-op classics with rewind and save-states.
   - **Unofficial Multiplayer Mods & Source Ports:** Verified community projects from the *Megalist* (e.g. *Super Mario 64 Coop DX*, *Zelda: Ship of Harkinian*, *Sonic 3 A.I.R.*).

2. **Date Night Matchmaker:**
   - An interactive 3-step recommendation tool matching your exact hardware (1 Switch, 2 Switches, 1 3DS, 2 3DS), your partner's gaming comfort level, and the desired date vibe (Cozy, Story, Chaos, Mystery, Party).

3. **Multi-Variable Filtering & Search:**
   - Real-time instant search across titles, summaries, setup instructions, and tags.
   - Filter by Platform, Category, Mode (Co-Op, Versus, Both), Connection Type, Difficulty/Stress Level, and Vibe.

4. **Date Night Shortlist & Bookmark Drawer:**
   - Save favorite games with the heart icon (persisted in `localStorage`).
   - Copy a formatted date night checklist directly to your clipboard.

5. **Detailed Hardware & Connection Guides:**
   - Step-by-step setup instructions for 3DS Download Play, Joy-Con sharing, Assist Mode toggles (e.g., in *Overcooked*), and source port installation.

---

## 💻 Local Testing & Development

Run a local preview server with Python (no installation required):
```bash
python3 -m http.server 3000
```
Open your browser to `http://localhost:3000`.

---

## 📁 Project Structure

```
duoplay-app/
├── index.html       # Semantic, accessible HTML5 layout
├── styles.css       # Responsive dark-theme styling with Nintendo red/blue accents
├── app.js           # Client-side filtering, matchmaker, and modal logic
├── data.js          # Unified database of 267 structured games
├── games.json       # Raw JSON export of the entire database
├── vercel.json      # Production caching and security headers for Vercel
├── package.json     # Project metadata and local scripts
└── README.md        # Deployment and usage documentation
```
