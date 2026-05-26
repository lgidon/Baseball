import datetime
import threading
import time
import requests
from config import SETTINGS
import mlb_api

# --- HYBRID MEMORY REPOSITORIES ---
LEAGUE_BULK_CACHE = {"last_updated": None, "games": {}, "standings": {}}
ROSTER_CACHE = {}

cache_lock = threading.Lock()
ALL_TEAM_IDS = []

def initialize_league_teams():
    """Runs once on startup to discover all active team configuration mappings."""
    global ALL_TEAM_IDS
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    try:
        res = requests.get(url, timeout=5).json()
        ALL_TEAM_IDS = [str(t['id']) for t in res.get('teams', [])]
        print(f"⚙️ Cached metadata structures for {len(ALL_TEAM_IDS)} active MLB teams.")
    except Exception:
        ALL_TEAM_IDS = ["147"] # Fallback array

def refresh_eager_cache():
    """Triggers bulk network retrievals to populate games and standings profiles."""
    games = mlb_api.fetch_bulk_league_schedule()
    standings = mlb_api.fetch_bulk_league_standings()
    
    with cache_lock:
        LEAGUE_BULK_CACHE["last_updated"] = datetime.datetime.now().strftime('%H:%M:%S')
        LEAGUE_BULK_CACHE["games"] = games
        LEAGUE_BULK_CACHE["standings"] = standings

def background_sync_worker():
    """Long-running background engine processing automated cron cycles."""
    initialize_league_teams()
    refresh_eager_cache() # Initial seed pass on boot
    
    while True:
        interval = max(1, SETTINGS["sync_interval_mins"])
        time.sleep(interval * 60)
        refresh_eager_cache()

def start_background_worker():
    """Kicks off the detached orchestrator worker."""
    worker = threading.Thread(target=background_sync_worker, daemon=True)
    worker.start()

def get_roster_lazy(team_id):
    """Fetches a team's roster only if it is missing or older than 24 hours."""
    team_id_str = str(team_id)
    now = datetime.datetime.now()
    
    with cache_lock:
        cached = ROSTER_CACHE.get(team_id_str)
        
    if cached and (now - cached["fetched_at"]) < datetime.timedelta(hours=24):
        return cached["players"]
        
    # Cache miss -> hit the endpoint
    players = mlb_api.fetch_team_roster(team_id_str)
    if players:
        with cache_lock:
            ROSTER_CACHE[team_id_str] = {"fetched_at": now, "players": players}
        return players
        
    return cached["players"] if cached else []

def compile_dashboard_data(team_id):
    """Aggregates eager league cache items and lazy rosters into a unified payload."""
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
    upcoming_placeholder = [{"date": "See main schedule", "opponent": "Next Matchup", "venue": "Ballpark", "is_home": True}]

    return {
        'today': today_game,
        'schedule': upcoming_placeholder,
        'standings': team_standings,
        'roster': roster,
        'last_updated': bulk["last_updated"]
    }