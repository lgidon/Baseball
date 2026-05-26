import datetime
import threading
import time
from config import SETTINGS
import mlb_api

# --- HYBRID MEMORY REPOSITORIES ---
LEAGUE_BULK_CACHE = {"last_updated": None, "games": {}, "standings": {}}
ROSTER_CACHE = {}
SCHEDULE_CACHE = {}  # New cache repo for slow-moving lookaheads

cache_lock = threading.Lock()
ALL_TEAM_IDS = []

def initialize_league_teams():
    global ALL_TEAM_IDS
    import requests
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    try:
        res = requests.get(url, timeout=5).json()
        ALL_TEAM_IDS = [str(t['id']) for t in res.get('teams', [])]
        print(f"⚙️ Cached metadata structures for {len(ALL_TEAM_IDS)} active MLB teams.")
    except Exception:
        ALL_TEAM_IDS = ["147"]

def refresh_eager_cache():
    games = mlb_api.fetch_bulk_league_schedule()
    standings = mlb_api.fetch_bulk_league_standings()
    
    with cache_lock:
        LEAGUE_BULK_CACHE["last_updated"] = datetime.datetime.now().strftime('%H:%M:%S')
        LEAGUE_BULK_CACHE["games"] = games
        LEAGUE_BULK_CACHE["standings"] = standings
    print("✅ Bulk cache refresh complete.")

def background_sync_worker():
    initialize_league_teams()
    refresh_eager_cache()
    while True:
        interval = max(1, SETTINGS["sync_interval_mins"])
        time.sleep(interval * 60)
        refresh_eager_cache()

def start_background_worker():
    worker = threading.Thread(target=background_sync_worker, daemon=True)
    worker.start()

def get_roster_lazy(team_id):
    team_id_str = str(team_id)
    now = datetime.datetime.now()
    
    with cache_lock:
        cached = ROSTER_CACHE.get(team_id_str)
        
    if cached and (now - cached["fetched_at"]) < datetime.timedelta(hours=24):
        return cached["players"]
        
    players = mlb_api.fetch_team_roster(team_id_str)
    if players:
        with cache_lock:
            ROSTER_CACHE[team_id_str] = {"fetched_at": now, "players": players}
        return players
    return cached["players"] if cached else []

# --- NEW: LAZY LOOKAHEAD SCHEDULE ENGINE ---
def get_schedule_lazy(team_id):
    """Fetches upcoming 5 matches only if missing or older than 12 hours."""
    team_id_str = str(team_id)
    now = datetime.datetime.now()
    
    with cache_lock:
        cached = SCHEDULE_CACHE.get(team_id_str)
        
    if cached and (now - cached["fetched_at"]) < datetime.timedelta(hours=12):
        return cached["matches"]
        
    # Cache miss or expired -> pull from API layer
    print(f"🦥 Lazy-fetching future schedule for team {team_id_str}...")
    matches = mlb_api.fetch_team_schedule(team_id_str)
    if matches:
        with cache_lock:
            SCHEDULE_CACHE[team_id_str] = {"fetched_at": now, "matches": matches}
        return matches
    return cached["matches"] if cached else []

def compile_dashboard_data(team_id):
    team_id_str = str(team_id)
    
    with cache_lock:
        bulk = LEAGUE_BULK_CACHE.copy()
        
    today_game = bulk["games"].get(team_id_str)
    
    team_standings = []
    for div_teams in bulk["standings"].values():
        if any(t['id'] == team_id_str for t in div_teams):
            team_standings = [{
                'name': t['name'], 'w': t['w'], 'l': t['l'], 'gb': t['gb'],
                'is_target': (t['id'] == team_id_str)
            } for t in div_teams]
            break
            
    roster = get_roster_lazy(team_id_str)
    schedule = get_schedule_lazy(team_id_str) # Fetching true lookahead matches

    return {
        'today': today_game,
        'schedule': schedule,
        'standings': team_standings,
        'roster': roster,
        'last_updated': bulk["last_updated"]
    }