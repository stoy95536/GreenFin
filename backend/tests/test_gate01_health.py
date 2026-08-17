"""
GATE-01 Tests: Backend Startup & Health Endpoint

Verifies:
- FastAPI app starts successfully
- /api/health returns 200
- Response contains required fields
- Data directory is reported as connected
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_health_endpoint_returns_200(client):
    """Health endpoint should return HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_has_required_fields(client):
    """Health response must include all expected fields."""
    response = client.get("/api/health")
    data = response.json()

    required_fields = [
        "status",
        "app_name",
        "environment",
        "demo_mode",
        "rule_version",
        "database",
        "timestamp",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_health_reports_healthy_status(client):
    """Health status should be 'healthy'."""
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_app_name_is_greenfin(client):
    """App name should be GreenFin."""
    response = client.get("/api/health")
    data = response.json()
    assert data["app_name"] == "GreenFin"


def test_health_database_connected(client):
    """Data storage should report as connected."""
    response = client.get("/api/health")
    data = response.json()
    assert data["database"] == "connected"


def test_health_rule_version(client):
    """Rule version should be GREENFIN_DEMO_V1."""
    response = client.get("/api/health")
    data = response.json()
    assert data["rule_version"] == "GREENFIN_DEMO_V1"


def test_health_demo_mode_enabled(client):
    """Demo mode should be enabled."""
    response = client.get("/api/health")
    data = response.json()
    assert data["demo_mode"] is True
