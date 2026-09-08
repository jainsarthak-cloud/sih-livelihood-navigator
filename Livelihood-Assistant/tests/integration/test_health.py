"""Integration test for GET /v1/health."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health check returns 200 and valid JSON."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Livelihood-Assistant-AI"
    assert "version" in data
    assert "environment" in data
    assert "services" in data
    assert data["services"]["api"] == "online"


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns 200 with service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["health"] == "/v1/health"


def test_openapi_endpoint_is_available_for_runtime_integration(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/v1/health" in response.json()["paths"]
