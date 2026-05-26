import datetime
import requests

def fetch_bulk_league_schedule():
    """Queries league-wide game statuses and weather info in a single call."""
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_str}&hydrate=linescore,game"
    
    games_by_team = {}
    try:
        res = requests.get(url, timeout=5).json()
        for date_entry in res.get('dates', []):
            for g in date_entry.get('games', []):
                weather_info = "Weather info not available"
                game_info = g.get('gameData', {}).get('game', {}).get('weather', {})
                if game_info:
                    temp = game_info.get('temp', '')
                    cond = game_info.get('condition', '')
                    wind = game_info.get('wind', '')
                    if temp or cond:
                        weather_info = f"{temp}°F, {cond} (Wind: {wind})"

                payload = {
                    'home_team': g['teams']['home']['team']['name'],
                    'away_team': g['teams']['away']['team']['name'],
                    'home_score': g['teams']['home'].get('score', 0),
                    'away_score': g['teams']['away'].get('score', 0),
                    'status': g['status']['detailedState'],
                    'venue': g['venue']['name'],
                    'weather': weather_info
                }
                games_by_team[str(g['teams']['home']['team']['id'])] = payload
                games_by_team[str(g['teams']['away']['team']['id'])] = payload
    except Exception as e:
        print(f"🚨 API Error fetching schedule network stream: {e}")
    return games_by_team

def fetch_bulk_league_standings():
    """Queries league standings for all teams in a single call."""
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104"
    standings_by_division = {}
    try:
        res = requests.get(url, timeout=5).json()
        for record in res.get('records', []):
            div_id = record['division']['id']
            division_teams = []
            for t in record.get('teamRecords', []):
                division_teams.append({
                    'id': str(t['team']['id']),
                    'name': t['team']['name'],
                    'w': t['leagueRecord']['wins'],
                    'l': t['leagueRecord']['losses'],
                    'gb': t.get('gamesBack', '-')
                })
            standings_by_division[div_id] = division_teams
    except Exception as e:
        print(f"🚨 API Error fetching standings network stream: {e}")
    return standings_by_division

def fetch_team_roster(team_id):
    """Queries individual active squad roster sheets on demand."""
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    players = []
    try:
        res = requests.get(url, timeout=4).json()
        for p in res.get('roster', []):
            players.append({
                'name': p['person']['fullName'],
                'number': p.get('jerseyNumber', '-'),
                'position': p['position']['abbreviation'],
                'type': p['position']['type']
            })
        players.sort(key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
    except Exception as e:
        print(f"🚨 API Error fetching team roster context for {team_id}: {e}")
    return players