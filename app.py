import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from config import SETTINGS, requires_auth
import cache_manager
from health import health_bp, set_shutting_down


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-dev-key")

app.register_blueprint(health_bp)

# Fire up our asynchronous caching system background worker on startup
cache_manager.start_background_worker()

def get_dropdown_team_list():
    url = "https://statsapi.mlb.com/api/v1/teams?sportId=1"
    try:
        res = requests.get(url, timeout=5).json()
        teams = res.get('teams', [])
        return sorted([{'id': t['id'], 'name': t['name']} for t in teams], key=lambda x: x['name'])
    except Exception:
        return [{'id': 147, 'name': 'New York Yankees'}]

@app.route('/', methods=['GET', 'POST'])
def index():
    teams = get_dropdown_team_list()
    selected_team = request.form.get('team_id') or request.args.get('team_id')
    
    if not selected_team and teams:
        selected_team = teams[0]['id']
        
    team_id_str = str(selected_team)
    data = cache_manager.compile_dashboard_data(team_id_str)
    current_team_name = next((t['name'] for t in teams if str(t['id']) == team_id_str), "")
    
    return render_template(
        'index.html',
        teams=teams,
        selected_team=int(selected_team) if selected_team else None,
        current_team_name=current_team_name,
        data=data,
        settings=SETTINGS
    )

@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
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