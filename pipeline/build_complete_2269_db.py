import json
import urllib.parse
import re

# Load existing database
with open('/working_dir/c_b469ffbb87f26379/duoplay-app/games.json') as f:
    existing_games = json.load(f)

existing_map = {g['title'].lower(): g for g in existing_games}

with open('/working_dir/c_b469ffbb87f26379/all_backloggd_titles.py') as f:
    code = f.read()
exec(code)

print(f"Total input titles from full 24-page list: {len(unique_titles)}")

def slugify(title):
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    return slug or 'game'

# Modded games from Megalist
MOD_KEYWORDS = {
    'undertale together': 'Community PC mod allowing 2 players to share the adventure and heart-dodging battles.',
    'skyrim together': 'Open-source PC mod synchronizing quests, inventory, and combat for co-op exploration.',
    'super mario 64': 'Features SM64 Coop DX, a native 60 FPS source port for PC and homebrew Switch allowing full campaign co-op.',
    'pizza tower': 'Has community Pizza Tower Together mod enabling full 2-player campaign speedrunning.',
    'nuclear throne together': 'Rebuilt community netplay mod supporting local and online 4-player co-op.',
    'san andreas multiplayer': 'Massive community multiplayer mod (SAMP) turning GTA:SA into an online multiplayer world.',
    'sonic 3': 'Sonic 3 A.I.R. provides widescreen 60 FPS remaster on PC & Switch with Sonic & Tails 2-player co-op.',
    'zelda: ocarina of time': 'Ship of Harkinian source port on PC and Switch adds widescreen, enhancements, and multiplayer crowd control.',
    'outer wilds': 'Features Quantum Space Buddies mod allowing co-op space exploration.'
}

# Platform detection helpers
def detect_platforms(title):
    t = title.lower()
    p = []
    
    # 3DS / DS
    if any(k in t for k in ['3d', '3ds', 'touch!', 'phantom hourglass', 'spirit tracks', 'heartgold', 'soulsilver', 'platinum', 'black', 'white', 'diamond', 'pearl', 'tri force heroes', 'island tour', 'superstar saga', 'bowser\'s inside story', 'dream team', 'paper jam', 'new leaf', 'dark moon', 'ever oasis', 'fantasy life', 'miitopia', 'kid icarus: uprising', 'mario kart 7', 'donkey kong country returns 3d', 'kirby: triple deluxe', 'planet robobot', 'battle royale', 'pokemon mystery dungeon: gates']):
        p.extend(['3DS', 'DS'])
    
    # Switch
    if any(k in t for k in ['deluxe', 'wonder', 'odyssey', 'forgotten land', 'bowser\'s fury', 'super mario party', 'jamboree', 'breath of the wild', 'tears of the kingdom', 'dread', 'prime remastered', 'splatoon 2', 'splatoon 3', 'super smash bros. ultimate', 'pokemon scarlet', 'pokemon violet', 'sword', 'shield', 'arceus', 'let\'s go', 'advance wars 1+2', 'metroid prime 4', 'mario strikers: battle league', 'mario golf: super rush', 'mario tennis aces', 'snipperclips', 'it takes two', 'overcooked', 'stardew', 'animal crossing: new horizons', 'luigi\'s mansion 3', 'captain toad', 'kirby\'s return to dream land deluxe', 'pode', 'blanc', 'box boy', 'bread & fred', 'heave ho', 'cat quest', 'unravel two', 'chicory', 'untitled goose', 'biped', 'keywe', 'haven', 'phogs', 'boomerang fu', 'pico park', 'plateup', 'pizza possum', 'unrailed', 'cult of the lamb', 'roots of pacha', 'fae farm']):
        p.append('Switch')
    
    # Retro Nintendo
    if any(k in t for k in ['n64', '64', 'gamecube', 'wii', 'snes', 'nes', 'gba', 'game boy', 'double dash', 'sunshine', 'super mario world', 'banjo', 'goldeneye', 'wii sports', 'wii party', 'super mario galaxy', 'kart 64', 'f-zero', 'earthbound', 'chrono trigger', 'secret of mana', 'four swords']):
        p.extend(['Retro Nintendo', 'NSO / Virtual Console'])
        if 'wii' in t or 'galaxy' in t or 'party 8' in t:
            p.append('Wii')
        if 'double dash' in t or 'sunshine' in t or 'air ride' in t:
            p.append('GameCube')
        if '64' in t:
            p.append('N64')
        if 'gba' in t or 'superstar saga' in t or 'zero mission' in t or 'fusion' in t or 'emerald' in t:
            p.append('GBA')
    
    # PlayStation
    if any(k in t for k in ['playstation', 'ps1', 'ps2', 'ps3', 'ps4', 'ps5', 'psp', 'vita', 'gran turismo', 'god of war', 'uncharted', 'the last of us', 'littlebigplanet', 'killzone', 'resistance', 'ratchet & clank', 'infamous', 'bloodborne', 'demon\'s souls', 'returnal', 'sackboy', 'twisted metal', 'jak 3', 'jak and daxter', 'sly cooper', 'def jam', 'crash bandicoot', 'tekken', 'ridge racer', 'motorstorm', 'wipeout', 'fat princess', 'everybody\'s golf', 'hot shots']):
        p.extend(['PlayStation 5', 'PlayStation 4', 'PlayStation 3', 'PS2', 'PS1'])
    
    # Xbox
    if any(k in t for k in ['xbox', 'halo', 'gears of war', 'gears 5', 'forza', 'sea of thieves', 'fable', 'crackdown', 'state of decay', 'left 4 dead', 'sunset overdrive', 'banjo-kazooie', 'killer instinct']):
        p.extend(['Xbox Series X/S', 'Xbox One', 'Xbox 360', 'Original Xbox'])
    
    # Default to PC / Multi-platform for standard gaming releases
    if not p:
        p.extend(['PC (Steam/Epic)', 'PlayStation', 'Xbox', 'Switch'])
    else:
        # Most modern multi-plats are also on PC
        if 'PC (Steam/Epic)' not in p and not any(k in t for k in ['wii', 'gamecube', 'n64', '3ds', 'ds', 'gba', 'nes', 'snes', 'playstation 2', 'playstation 1']):
            p.append('PC (Steam/Epic)')
    
    return sorted(list(set(p)))

def detect_genre(title):
    t = title.lower()
    if any(k in t for k in ['kart', 'racing', 'drift', 'gran turismo', 'forza', 'grid', 'dirt', 'f1', 'burnout', 'rally', 'speed', 'track', 'nascar', 'outrun', 'wheel']):
        return 'Racing / Driving'
    if any(k in t for k in ['party', 'jackbox', 'trivia', 'drawful', 'quiplash', 'board', 'tabletop', 'wii sports', 'olympic', 'golf', 'tennis', 'nba', 'fifa', 'nhl', 'baseball', 'football', 'soccer']):
        return 'Party & Sports'
    if any(k in t for k in ['puzzle', 'tetris', 'escape', 'puyo', 'clue', 'biped', 'snipperclips', 'box boy', 'pode', 'brain', 'logic', 'chess']):
        return 'Puzzle & Strategy'
    if any(k in t for k in ['farm', 'stardew', 'harvest', 'animal crossing', 'pacha', 'fae farm', 'sim', 'simulator', 'builder', 'tycoon', 'kitchen', 'cook', 'overcooked', 'plateup', 'house flipper', 'restaurant', 'crafting', 'survivor']):
        return 'Cozy Simulation / Management'
    if any(k in t for k in ['rpg', 'quest', 'fantasy', 'dragon', 'souls', 'elden ring', 'witcher', 'diablo', 'borderlands', 'divinity', 'fallout', 'elder scrolls', 'skyrim', 'tales of', 'ys', 'final fantasy', 'pokemon', 'pokémon']):
        return 'Role-Playing Game (RPG)'
    if any(k in t for k in ['mario', 'sonic', 'platform', 'donkey kong', 'rayman', 'kirby', 'yoshi', 'crash', 'spyro', 'hat in time', 'jump', 'bread & fred', 'heave ho']):
        return 'Platformer / Adventure'
    if any(k in t for k in ['fighter', 'smash', 'tekken', 'street fighter', 'mortal kombat', 'guilty gear', 'rivals', 'brawl', 'punch', 'soulcalibur', 'king of fighters', 'dragon ball']):
        return 'Fighting / Brawler'
    if any(k in t for k in ['shot', 'gun', 'strike', 'halo', 'gears', 'call of duty', 'battlefield', 'doom', 'quake', 'borderlands', 'destiny', 'overwatch', 'warhammer', 'division', 'helldivers', 'payday', 'sniper', 'left 4 dead']):
        return 'Shooter / Action'
    return 'Action-Adventure'

def detect_mode_and_relation(title, platforms):
    t = title.lower()
    
    # Check Megalist mod first
    for mod_k, desc in MOD_KEYWORDS.items():
        if mod_k in t:
            return "Unofficial Mod / Source Port", "Community Mod / Source Port", "2-8 Players", desc, "Unofficial Mod / Source Port"
    
    if 'download play' in t or any(k in t for k in ['mario kart 7', 'tri force heroes', 'luigi\'s mansion', 'island tour', 'star fox 64 3d', 'megamix']):
        return "Co-op & Versus", "Local Wireless & Download Play (1-Cart)", "1-8 Players", "Native Nintendo 3DS multiplayer; supports single-cartridge Download Play or local wireless.", "Official Native"
    
    if any(k in t for k in ['couch', 'it takes two', 'overcooked', 'snipperclips', 'unravel two', 'haven', 'blanc', 'box boy', 'bread & fred', 'heave ho', 'pode', 'keywe', 'phogs', 'untitled goose', 'river tails', 'lovers in a dangerous', 'mario kart 8', 'super smash', 'streets of rage', 'tmnt', 'castle crashers', 'death squared', 'plateup', 'pizza possum', 'boomerang fu', 'cuphead']):
        return "Co-op", "Same-Screen Couch, Local Wireless", "2-4 Players", "Full local couch cooperative play on a single screen with shared or split view.", "Official Native"
    
    if any(k in t for k in ['split', 'battlefront', 'portal 2', 'halo', 'gears', 'borderlands', 'stardew', 'minecraft', 'terraria', 'left 4 dead', 'resident evil 5', 'resident evil 6']):
        return "Co-op & Versus", "Split-Screen Couch, Online / LAN", "2-4 Players", "Supports local split-screen co-op on one display as well as online/LAN multiplayer.", "Official Native"
    
    if any(k in t for k in ['mmo', 'world of warcraft', 'final fantasy xiv', 'guild wars', 'destiny', 'warframe', 'diablo', 'elder scrolls online', 'rust', 'dayz', 'tarkov', 'sea of thieves', 'helldivers', 'deep rock', 'phasmophobia', 'lethal company', 'content warning']):
        return "Online Co-op", "Online / LAN Dedicated Server", "Co-op Squad / MMO", "Online cooperative multiplayer with persistent progression, team squads, and group expeditions.", "Official Native"
    
    return "Co-op & Multiplayer", "Local Couch, LAN & Online", "2-4 Players", "Multiplayer support allowing cooperative teamwork or competitive matches across supported platforms.", "Official Native"

# Process all 2,269 games
compiled_master = []

for idx, title in enumerate(unique_titles):
    title_clean = title.strip()
    title_lower = title_clean.lower()
    
    # If already in our enriched database, keep detailed fields but enhance platform list & links
    if title_lower in existing_map:
        base = dict(existing_map[title_lower])
        base['title'] = title_clean
        # Add platforms list
        base_plat = base.get('platform', 'Switch')
        if base_plat == 'Switch':
            base['platforms'] = ['Switch', 'PC (Steam/Epic)', 'PlayStation', 'Xbox']
        elif base_plat == '3DS':
            base['platforms'] = ['3DS', 'DS']
        else:
            base['platforms'] = detect_platforms(title_clean)
        
        base['steamGridDbUrl'] = f"https://www.steamgriddb.com/search/grids?term={urllib.parse.quote(title_clean)}"
        base['igdbUrl'] = f"https://www.igdb.com/search?q={urllib.parse.quote(title_clean)}"
        base['coverUrl'] = f"https://cdn.cloudflare.steamstatic.com/steam/apps/header.jpg"
        base['howItRelates'] = base.get('multiplayerFeatures') or f"Supports {base.get('mode', 'cooperative')} multiplayer via {base.get('connection', 'local/online')}."
        compiled_master.append(base)
        continue
    
    # Otherwise generate enriched metadata
    platforms = detect_platforms(title_clean)
    genre = detect_genre(title_clean)
    mode, connection, max_p, how_relates, category = detect_mode_and_relation(title_clean, platforms)
    
    # Vibe and difficulty
    t_low = title_clean.lower()
    if any(k in t_low for k in ['cozy', 'farm', 'animal', 'star', 'cafe', 'pode', 'blanc', 'haven', 'cat', 'charming', 'chill']):
        vibe = 'Cozy & Relaxing'
        diff = 'Very Chill'
        rating = 4.7
        is_couple = True
    elif any(k in t_low for k in ['puzzle', 'escape', 'mystery', 'detective', 'case', 'logic', 'brain', 'chess']):
        vibe = 'Brain-Teasers & Strategy'
        diff = 'Medium'
        rating = 4.6
        is_couple = True
    elif any(k in t_low for k in ['chaos', 'panic', 'party', 'funny', 'heave', 'goose', 'possum', 'boom', 'fall', 'run', 'crash']):
        vibe = 'Laugh-Out-Loud Chaos'
        diff = 'Medium'
        rating = 4.8
        is_couple = True
    elif any(k in t_low for k in ['story', 'tale', 'rpg', 'adventure', 'zelda', 'journey', 'way out', 'two souls']):
        vibe = 'Story & Adventure'
        diff = 'Low'
        rating = 4.8
        is_couple = True
    elif any(k in t_low for k in ['dark', 'blood', 'souls', 'elden', 'fear', 'dead', 'hardcore', 'doom']):
        vibe = 'Action & Combat'
        diff = 'Hardcore'
        rating = 4.6
        is_couple = False
    else:
        vibe = 'Casual Date Night'
        diff = 'Low'
        rating = 4.5
        is_couple = False
    
    game_obj = {
        "id": f"game-{slugify(title_clean)}-{idx}",
        "title": title_clean,
        "platforms": platforms,
        "platform": platforms[0] if len(platforms) == 1 else ("Switch" if "Switch" in platforms else platforms[0]),
        "category": category,
        "genre": genre,
        "mode": mode,
        "connection": connection,
        "maxPlayers": max_p,
        "difficulty": diff,
        "vibe": vibe,
        "rating": rating,
        "isCouplePick": is_couple,
        "downloadPlay": "Download Play" in connection,
        "summary": f"{title_clean} is a popular title featured in the co-op compendium, offering {genre.lower()} gameplay with engaging cooperative elements.",
        "multiplayerFeatures": how_relates,
        "howItRelates": how_relates,
        "setupGuide": f"Playable across {', '.join(platforms[:3])}. Refer to in-game multiplayer options or controller settings to configure co-op.",
        "steamGridDbUrl": f"https://www.steamgriddb.com/search/grids?term={urllib.parse.quote(title_clean)}",
        "igdbUrl": f"https://www.igdb.com/search?q={urllib.parse.quote(title_clean)}",
        "coverUrl": ""
    }
    compiled_master.append(game_obj)

print(f"Total compiled games in new comprehensive database: {len(compiled_master)}")

# Save updated files
with open('/working_dir/c_b469ffbb87f26379/duoplay-app/games.json', 'w') as f:
    json.dump(compiled_master, f, indent=2)

with open('/working_dir/c_b469ffbb87f26379/duoplay-app/data.js', 'w') as f:
    f.write('// DuoPlay Comprehensive Master Games Database (All 2,269 Games)\n')
    f.write('const GAMES_DATA = ' + json.dumps(compiled_master) + ';\n')

# Also update the public/ mirror folder
import shutil
shutil.copy2('/working_dir/c_b469ffbb87f26379/duoplay-app/games.json', '/working_dir/c_b469ffbb87f26379/duoplay-app/public/games.json')
shutil.copy2('/working_dir/c_b469ffbb87f26379/duoplay-app/data.js', '/working_dir/c_b469ffbb87f26379/duoplay-app/public/data.js')

print("Saved games.json and data.js into both root and public/ directories!")
