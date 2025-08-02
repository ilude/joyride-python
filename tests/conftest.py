"""Test configuration and fixtures."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Set testing environment before importing app
os.environ["TESTING"] = "true"

# Create comprehensive Docker mock
docker_mock = MagicMock()
docker_mock.from_env.return_value = MagicMock()

# Mock docker.errors submodule
errors_mock = MagicMock()
errors_mock.DockerException = Exception
docker_mock.errors = errors_mock

# Mock docker.models submodule
models_mock = MagicMock()
docker_mock.models = models_mock

# Add the mock to sys.modules
sys.modules["docker"] = docker_mock
sys.modules["docker.errors"] = errors_mock
sys.modules["docker.models"] = models_mock


@pytest.fixture(scope="session", autouse=True)
def mock_docker():
    """Mock Docker client for all tests."""
    with patch("docker.from_env") as mock_docker_from_env:
        mock_client = MagicMock()
        mock_docker_from_env.return_value = mock_client
        yield mock_client


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    # Import app after setting environment and mocks
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
