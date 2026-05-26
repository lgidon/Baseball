import os
from functools import wraps
from flask import request

# --- GLOBAL SETTINGS & USER PREFERENCES ---
SETTINGS = {
    "user_name": "Baseball Fan",
    "theme_color": "dark",        # Layout accents: dark, primary, success, info, danger
    "sync_interval_mins": 5,      # Frequency of bulk API calls
    "admin_user": os.environ.get("ADMIN_USER", "admin"),
    "admin_password": os.environ.get("ADMIN_PASSWORD", "baseball2026")
}

# --- SECURITY: HTTP BASIC AUTHENTICATION DECORATOR ---
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != SETTINGS["admin_user"] or auth.password != SETTINGS["admin_password"]:
            return ('Unauthorized access. Invalid credentials.', 401,
                    {'WWW-Authenticate': 'Basic realm="Admin Login"'})
        return f(*args, **kwargs)
    return decorated