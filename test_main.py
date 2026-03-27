import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200

def test_cors_headers():
    """Test that CORS headers are present"""
    response = client.options("/health")
    assert response.status_code == 200
    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers
