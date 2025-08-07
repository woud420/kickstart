"""Tests for main application module."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "{{SERVICE_NAME}} is running"


def test_health_endpoint():
    """Test the health endpoint returns correct response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "{{SERVICE_NAME}}"
    assert data["version"] == "0.1.0"


def test_health_endpoint_structure():
    """Test the health endpoint returns expected structure."""
    response = client.get("/health")
    data = response.json()
    
    required_fields = ["status", "service", "version"]
    for field in required_fields:
        assert field in data
