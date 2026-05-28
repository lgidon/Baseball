import pytest
import sys
from unittest.mock import patch, MagicMock
from flask import template_rendered
from contextlib import contextmanager

# -------------------------------------------------------------------
# 1. Monkey-patch requires_auth BEFORE importing the app
# -------------------------------------------------------------------
import config
config.requires_auth = lambda f: f   # disable authentication for all tests

# Now it is safe to import the Flask app
from app import app as flask_app   # flask_app is the Flask instance
from app import get_dropdown_team_list   # function needed for some tests
import cache_manager
import config as config_module

# -------------------------------------------------------------------
# Helper: capture rendered templates for context inspection
# -------------------------------------------------------------------
@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

# -------------------------------------------------------------------
# Fixture: test client using the already‑patched Flask app
# -------------------------------------------------------------------
@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

# -------------------------------------------------------------------
# Tests for get_dropdown_team_list
# -------------------------------------------------------------------
@patch('app.requests.get')
def test_get_dropdown_team_list_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'teams': [
            {'id': 147, 'name': 'New York Yankees'},
            {'id': 141, 'name': 'Boston Red Sox'},
            {'id': 137, 'name': 'San Francisco Giants'}
        ]
    }
    mock_get.return_value = mock_response
    teams = get_dropdown_team_list()
    expected = [
        {'id': 141, 'name': 'Boston Red Sox'},
        {'id': 147, 'name': 'New York Yankees'},
        {'id': 137, 'name': 'San Francisco Giants'}
    ]
    assert teams == expected
    mock_get.assert_called_once_with(
        "https://statsapi.mlb.com/api/v1/teams?sportId=1", timeout=5
    )

@patch('app.requests.get')
def test_get_dropdown_team_list_exception(mock_get):
    mock_get.side_effect = Exception("API down")
    teams = get_dropdown_team_list()
    expected = [{'id': 147, 'name': 'New York Yankees'}]
    assert teams == expected

# -------------------------------------------------------------------
# Tests for index route (/)
# -------------------------------------------------------------------
@patch('cache_manager.compile_dashboard_data')
@patch('app.get_dropdown_team_list')
def test_index_get_no_team_selected(mock_get_teams, mock_compile_data, client):
    mock_get_teams.return_value = [
        {'id': 147, 'name': 'Yankees'},
        {'id': 141, 'name': 'Red Sox'}
    ]
    mock_compile_data.return_value = {'some': 'dashboard_data'}

    with captured_templates(flask_app) as templates:
        client.get('/')
        template, context = templates[0]
        assert template.name == 'index.html'
        assert context['selected_team'] == 147
        assert context['teams'] == mock_get_teams.return_value
        assert context['data'] == mock_compile_data.return_value

    mock_compile_data.assert_called_once_with('147')

@patch('cache_manager.compile_dashboard_data')
@patch('app.get_dropdown_team_list')
def test_index_get_with_team_id_arg(mock_get_teams, mock_compile_data, client):
    mock_get_teams.return_value = [
        {'id': 147, 'name': 'Yankees'},
        {'id': 141, 'name': 'Red Sox'}
    ]
    mock_compile_data.return_value = {}
    client.get('/?team_id=141')
    mock_compile_data.assert_called_once_with('141')

@patch('cache_manager.compile_dashboard_data')
@patch('app.get_dropdown_team_list')
def test_index_post_with_team_id(mock_get_teams, mock_compile_data, client):
    mock_get_teams.return_value = [{'id': 141, 'name': 'Red Sox'}]
    mock_compile_data.return_value = {}
    client.post('/', data={'team_id': '141'})
    mock_compile_data.assert_called_once_with('141')

@patch('cache_manager.compile_dashboard_data')
@patch('app.get_dropdown_team_list')
def test_index_missing_team_name(mock_get_teams, mock_compile_data, client):
    mock_get_teams.return_value = [{'id': 147, 'name': 'Yankees'}]
    mock_compile_data.return_value = {}
    with captured_templates(flask_app) as templates:
        client.get('/?team_id=999')
        context = templates[0][1]
        assert context['current_team_name'] == ''

# -------------------------------------------------------------------
# Tests for admin route (/admin) – authentication is already disabled
# -------------------------------------------------------------------
@patch('cache_manager.start_background_worker')
@patch('config.SETTINGS', new={
    "user_name": "Baseball Fan",
    "theme_color": "dark",
    "sync_interval_mins": 5
})
def test_admin_get_authenticated(mock_start_worker, client):
    with captured_templates(flask_app) as templates:
        response = client.get('/admin')
        assert response.status_code == 200
        template, context = templates[0]
        assert template.name == 'admin.html'
        assert context['settings'] == {
            "user_name": "Baseball Fan",
            "theme_color": "dark",
            "sync_interval_mins": 5
        }

@patch('cache_manager.start_background_worker')
def test_admin_post_update_settings(mock_start_worker, client):
    original = config_module.SETTINGS.copy()
    try:
        config_module.SETTINGS.update({
            "user_name": "Old Name",
            "theme_color": "light",
            "sync_interval_mins": 10
        })
        response = client.post('/admin', data={
            'user_name': 'New Fan',
            'theme_color': 'blue',
            'sync_interval_mins': '7'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert config_module.SETTINGS['user_name'] == 'New Fan'
        assert config_module.SETTINGS['theme_color'] == 'blue'
        assert config_module.SETTINGS['sync_interval_mins'] == 7
        assert b'Configuration preferences updated successfully!' in response.data
    finally:
        config_module.SETTINGS.clear()
        config_module.SETTINGS.update(original)

@patch('cache_manager.start_background_worker')
def test_admin_post_invalid_sync_interval(mock_start_worker, client):
    original = config_module.SETTINGS.copy()
    try:
        config_module.SETTINGS['sync_interval_mins'] = 10
        client.post('/admin', data={
            'user_name': 'Test',
            'theme_color': 'dark',
            'sync_interval_mins': 'not_a_number'
        }, follow_redirects=True)
        assert config_module.SETTINGS['sync_interval_mins'] == 5
    finally:
        config_module.SETTINGS.clear()
        config_module.SETTINGS.update(original)

@patch('cache_manager.start_background_worker')
def test_admin_post_minimum_sync_interval(mock_start_worker, client):
    original = config_module.SETTINGS.copy()
    try:
        config_module.SETTINGS['sync_interval_mins'] = 5
        client.post('/admin', data={
            'user_name': 'Fan',
            'theme_color': 'dark',
            'sync_interval_mins': '0'
        }, follow_redirects=True)
        assert config_module.SETTINGS['sync_interval_mins'] == 1
    finally:
        config_module.SETTINGS.clear()
        config_module.SETTINGS.update(original)

# -------------------------------------------------------------------
# Test that background worker is started when app loads (optional)
# -------------------------------------------------------------------
def test_background_worker_started_on_import():
    with patch('cache_manager.start_background_worker') as mock_start:
        # Reload the app module to trigger the call again
        import importlib
        import app
        importlib.reload(app)
        mock_start.assert_called_once()
