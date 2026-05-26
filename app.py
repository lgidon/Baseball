import datetime
import os
import threading
import time
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-dev-key")

# --- GLOBAL APPLICATION STATE (IN-MEMORY CACHE) ---
SETTINGS = {
    "user_name": "Baseball Fan",
    "theme_color": "dark",        # Options: dark, primary, success, info, danger
    "sync_interval_mins": 5,      # Default lookup frequency
    "admin_user": os.environ.get("ADMIN_USER", "admin"),
    "admin_password": os.environ.get("ADMIN_PASSWORD", "baseball2026") # Fallback for dev
}

# In-memory storage for cached API payloads
# Structure: { team_id: { "timestamp": datetime, "payload": data_dict } }
DATA_CACHE = {}
cache_lock = threading.Lock()

# --- SECURITY: BASIC AUTH DECORATOR ---
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != SETTINGS["admin_user"] or auth.password != SETTINGS["admin_password"]:
            return ('Unauthorized access. Please provide correct admin credentials.', 401,
                    {'WWW-Authenticate': 'Basic realm="Admin Login"'})
        return f(*args, **kwargs)
    return decorated

# --- DATA FETCH ENGINE ---
def fetch_mlb_data_for_team(team_id):
    """Pulls live schedule, standings, rosters, and weather from the MLB API."""
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    
    # 1. Today's Game & Live Weather
    game_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&date={today_str}&hydrate=linescore,game"
    today_game = None
    try:
        game_data = requests.get(game_url, timeout=5).json()
        dates = game_data.get('dates', [])
        if dates and dates[0].get('games'):
            raw_game = dates[0]['games'][0]
            game_pk = raw_game.get('gamePk')
            weather_info = "Weather info not available yet"
            
            if game_pk:
                feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
                feed_data = requests.get(feed_url, timeout=5).json()
                game_info = feed_data.get('gameData', {}).get('game', {}).get('weather', {})
                if game_info:
                    temp = game_info.get('temp', '')
                    cond = game_info.get('condition', '')
                    wind = game_info.get('wind', '')
                    if temp or cond:
                        weather_info = f"{temp}°F, {cond} (Wind: {wind})"

            today_game = {
                'home_team': raw_game['teams']['home']['team']['name'],
                'away_team': raw_game['teams']['away']['team']['name'],
                'home_score': raw_game['teams']['home'].get('score', 0),
                'away_score': raw_game['teams']['away'].get('score', 0),
                'status': raw_game['status']['detailedState'],
                'venue': raw_game['venue']['name'],
                'weather': weather_info
            }
    except Exception as e:
        print(f"Error fetching game details: {e}")

    # 2. Upcoming Schedule
    start_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = (datetime.date.today() + datetime.timedelta(days=15)).strftime('%Y-%m-%d')
    sched_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&startDate={start_date}&endDate={end_date}"
    upcoming = []
    try:
        sched_data = requests.get(sched_url, timeout=5).json()
        for date_entry in sched_data.get('dates', []):
            for g in date_entry.get('games', []):
                if len(upcoming) < 5:
                    upcoming.append({
                        'date': g['gameDate'][:10],
                        'opponent': g['teams']['away']['team']['name'] if g['teams']['home']['team']['id'] == int(team_id) else g['teams']['home']['team']['name'],
                        'venue': g['venue']['name'],
                        'is_home': g['teams']['home']['team']['id'] == int(team_id)
                    })
    except Exception as e:
        print(f"Error fetching schedule: {e}")

    # 3. Standings
    standings_url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104"
    division_standings = []
    try:
        standings_data = requests.get(standings_url, timeout=5).json()
        target_records = None
        for record in standings_data.get('records', []):
            team_records = record.get('teamRecords', [])
            if any(t['team']['id'] == int(team_id) for t in team_records):
                target_records = team_records
                break
        if target_records:
            for t in target_records:
                division_standings.append({
                    'name': t['team']['name'],
                    'w': t['leagueRecord']['wins'],
                    'l': t['leagueRecord']['losses'],
                    'gb': t.get('gamesBack', '-'),
                    'is_target': t['team']['id'] == int(team_id)
                })
    except Exception as e:
        print(f"Error parsing standings: {e}")

    # 4. Active Roster
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    active_roster = []
    try:
        roster_data = requests.get(roster_url, timeout=5).json()
        for player in roster_data.get('roster', []):
            active_roster.append({
                'name': player['person']['fullName'],
                'number': player.get('jerseyNumber', '-'),
                'position': player['position']['abbreviation'],
                'type': player['position']['type']
            })
        active_roster.sort(key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
    except Exception as e:
        print(f"Error parsing roster: {e}")

    return {
        'today': today_game,
        'schedule': upcoming,
        'standings': division_standings,
        'roster': active_roster,
        'last_updated': datetime.datetime.now().strftime('%H:%M:%S')
    }

# --- AUTOMATED BACKGROUND THREAD ---
def background_cache_worker():
    """Background loop that automatically refreshes active cache objects."""
    print("🤖 Background synchronization worker initiated.")
    while True:
        with cache_lock:
            active_teams = list(DATA_CACHE.keys())
        
        if active_teams:
            print(f"🔄 Background refresh running for active teams: {active_teams}")
            for team_id in active_teams:
                fresh_data = fetch_mlb_data_for_team(team_id)
                with cache_lock:
                    DATA_CACHE[team_id] = {
                        "timestamp": datetime.datetime.now(),
                        "payload": fresh_data
                    }
        
        # Pull interval from settings dynamically, fall back safely if modified incorrectly
        sleep_seconds = max(60, SETTINGS["sync_interval_mins"] * 60)
        time.sleep(sleep_seconds)

# Start background thread automatically on boot
worker = threading.Thread(target=background_cache_worker, daemon=True)
worker.start()

def get_all_teams():
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    try:
        response = requests.get(url, timeout=5).json()
        teams = response.get('teams', [])
        return sorted([{'id': t['id'], 'name': t['name']} for t in teams], key=lambda x: x['name'])
    except Exception:
        return [{'id': 147, 'name': 'New York Yankees'}]

# --- APPLICATION ROUTING ---
@app.route('/', methods=['GET', 'POST'])
def index():
    teams = get_all_teams()
    selected_team = request.form.get('team_id') or request.args.get('team_id')
    
    if not selected_team and teams:
        selected_team = teams[0]['id']
        
    team_id_str = str(selected_team)
    
    # Check cache first to avoid hitting external API rate limits
    with cache_lock:
        cached_entry = DATA_CACHE.get(team_id_str)
        
    if cached_entry:
        data = cached_entry["payload"]
        is_cached = True
    else:
        # Initial cold boot lookup, then seed background monitor cache tracker
        print(f"❄️ Cache cold-miss for team {team_id_str}. Querying live...")
        data = fetch_mlb_data_for_team(team_id_str)
        with cache_lock:
            DATA_CACHE[team_id_str] = {
                "timestamp": datetime.datetime.now(),
                "payload": data
            }
        is_cached = False
        
    current_team_name = next((t['name'] for t in teams if str(t['id']) == team_id_str), "")
    
    return render_template(
        'index.html',
        teams=teams,
        selected_team=int(selected_team) if selected_team else None,
        current_team_name=current_team_name,
        data=data,
        settings=SETTINGS,
        is_cached=is_cached
    )

@app.route('/admin', methods=['GET', 'POST'])
@requires_auth # Protecing the route via HTTP Basic Authentication
def admin():
    if request.method == 'POST':
        SETTINGS["user_name"] = request.form.get("user_name", "Baseball Fan").strip()
        SETTINGS["theme_color"] = request.form.get("theme_color", "dark")
        
        try:
            SETTINGS["sync_interval_mins"] = max(1, int(request.form.get("sync_interval_mins", 5)))
        except ValueError:
            SETTINGS["sync_interval_mins"] = 5
            
        flash("Configuration preferences updated successfully!", "success")
        return redirect(url_for('admin'))
        
    return render_template('admin.html', settings=SETTINGS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)