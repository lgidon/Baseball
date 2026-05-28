# health.py (Updated)
import time
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)
_is_shutting_down = False

def set_shutting_down():
    global _is_shutting_down
    _is_shutting_down = True

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    return jsonify({"status": "alive"}), 200

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    if _is_shutting_down:
        return jsonify({"status": "draining_traffic"}), 503
    return jsonify({"status": "ready"}), 200

# NEW: The trigger endpoint for K8s lifecycle
@health_bp.route('/prepare-shutdown', methods=['POST'])
def prepare_shutdown():
    """Called by K8s preStop hook before SIGTERM is sent."""
    set_shutting_down()
    
    # Optional: Sleep for 3-5 seconds here. This keeps the preStop hook active,
    # forcing K8s to wait while the networking layer updates and routes traffic away.
    time.sleep(3) 
    
    return jsonify({"status": "draining"}), 200