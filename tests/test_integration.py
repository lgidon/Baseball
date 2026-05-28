import pytest
from app import app

@pytest.fixture
def client():
    """
    Setup fixture: Configures the Flask app for a testing context
    and provisions a clean environment wrapper.
    """
    app.config['TESTING'] = True
    app.config['FLASK_SECRET_KEY'] = 'test-environment-crypto-key'
    
    # Create the virtual execution context client
    with app.test_client() as test_client:
        yield test_client  # Pass this instance directly to our tests

def test_dashboard_homepage_route(client):
    """
    Integration Test: Hits the root or main dashboard UI route 
    and checks if it serves HTML with the correct template markers.
    """
    # 1. Act: Make a virtual GET request to your application
    response = client.get('/')
    
    # 2. Assert: Verify HTTP status code is 200 OK
    assert response.status_code == 200
    
    # 3. Assert: Verify specific keywords exist inside the rendered HTML response
    assert b"Baseball" in response.data or b"Dashboard" in response.data

def test_liveness_probe_endpoint(client):
    """
    Integration Test: Confirms the endpoint targeted by your Kubernetes 
    Startup/Liveness probes is up and serving the correct JSON footprint.
    """
    response = client.get('/live')
    
    assert response.status_code == 200
    # Verifies the response returns proper application/json headers
    assert response.is_json
    assert response.get_json() == {"status": "alive"}
