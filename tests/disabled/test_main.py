import pytest

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_status_endpoint(client):
    """Test the detailed status endpoint."""
    response = client.get("/status")
    assert response.status_code == 200

    data = response.get_json()
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "dns_server" in data
    assert "docker_monitor" in data
    assert data["status"] == "running"


def test_main_status_page(client):
    """Test the main status page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Service is running" in response.data
    assert b"Joyride DNS" in response.data


def test_dns_records_endpoint(client):
    """Test the DNS records endpoint."""
    response = client.get("/dns/records")
    assert response.status_code == 200

    data = response.get_json()
    assert "records" in data
    assert "total_records" in data
    assert "status" in data
    assert data["status"] == "success"
    assert isinstance(data["records"], list)
    assert isinstance(data["total_records"], int)


def test_theme_toggle_elements(client):
    """Test that theme toggle elements are present in the status page"""
    response = client.get("/")
    assert response.status_code == 200

    html_content = response.get_data(as_text=True)

    # Check for theme toggle elements
    assert 'data-theme="dark"' in html_content
    assert 'id="theme-toggle-btn"' in html_content
    assert 'id="theme-icon"' in html_content
    assert 'class="theme-toggle"' in html_content

    # Check for JavaScript theme functionality
    assert "localStorage.getItem('theme')" in html_content
    assert "setAttribute('data-theme'" in html_content
