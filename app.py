import datetime
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# A small lookup dictionary for major MLB teams to filter the standings easily
# 103 = American League, 104 = National League
DIVISION_LOOKUP = {
    133: {"leagueId": 103, "divisionId": 200},  # Oakland Athletics (AL West)
    134: {"leagueId": 103, "divisionId": 201},  # Pittsburgh Pirates -> wait, Pirates are NL Central (104, 205)
    147: {"leagueId": 104, "divisionId": 203},  # NY Yankees (AL East - 103, 201) actually Yankees are 147
}


def get_all_teams():
    """Fetches all active MLB teams for our dropdown selector."""
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    try:
        response = requests.get(url, timeout=5).json()
        teams = response.get("teams", [])
        # Sort alphabetically by team name
        return sorted(
            [{"id": t["id"], "name": t["name"]} for t in teams],
            key=lambda x: x["name"],
        )
    except Exception:
        return [{"id": 147, "name": "New York Yankees"}]  # Fallback


def get_team_dashboard(team_id):
    """Gathers today's game, weather, future schedule, standings, and active roster."""
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    
    # --- 1. TODAY'S GAME & LIVE WEATHER ---
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
        print(f"Error fetching today's game details: {e}")

    # --- 2. UPCOMING SCHEDULE (Next 5 Games) ---
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
        print(f"Error fetching upcoming schedule: {e}")

    # --- 3. STANDINGS ---
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
        print(f"Error parsing league standings: {e}")

    # --- 4. NEW: ACTIVE ROSTER FETCH ---
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    active_roster = []
    
    try:
        roster_data = requests.get(roster_url, timeout=5).json()
        for player in roster_data.get('roster', []):
            active_roster.append({
                'name': player['person']['fullName'],
                'number': player.get('jerseyNumber', '-'),
                'position': player['position']['abbreviation'],
                'type': player['position']['type'] # Pitcher, Hitter, etc.
            })
        # Sort roster by jersey number numerically if possible
        active_roster.sort(key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
    except Exception as e:
        print(f"Error parsing roster: {e}")

    return {
        'today': today_game,
        'schedule': upcoming,
        'standings': division_standings,
        'roster': active_roster
    }

@app.route("/", methods=["GET", "POST"])
def index():
    teams = get_all_teams()
    selected_team = request.form.get("team_id") or request.args.get("team_id")

    # Default to the first team if none chosen yet
    if not selected_team and teams:
        selected_team = teams[0]["id"]

    data = get_team_dashboard(selected_team) if selected_team else None
    current_team_name = next(
        (t["name"] for t in teams if str(t["id"]) == str(selected_team)), ""
    )

    return render_template(
        "index.html",
        teams=teams,
        selected_team=int(selected_team) if selected_team else None,
        current_team_name=current_team_name,
        data=data,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
