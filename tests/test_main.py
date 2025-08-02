import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'service' in data
    assert 'version' in data
    assert 'environment' in data
    assert 'timestamp' in data


def test_status_endpoint(client):
    """Test the detailed status endpoint."""
    response = client.get('/status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'service' in data
    assert 'system' in data
    assert data['status'] == 'running'


def test_main_status_page(client):
    """Test the main status page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Service is running' in response.data
    assert b'Flask Status Service' in response.data
