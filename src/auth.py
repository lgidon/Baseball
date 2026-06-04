# middleware/auth.py
from functools import wraps
from flask import request, jsonify
from config import settings

def requires_auth(f):
    """HTTP Basic Authentication decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != settings.ADMIN_USER  or auth.password != settings.ADMIN_PASSWORD:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid credentials"
            }), 401, {'WWW-Authenticate': 'Basic realm="Admin Login"'}
        return f(*args, **kwargs)
    return decorated