"""
GATE-10 Tests: Authorization API Endpoints

Verifies:
- POST /api/authorizations/grant
- POST /api/authorizations/{id}/revoke
- GET /api/farmers/{id}/authorizations
- GET /api/banks/{id}/authorizations
- POST /api/authorizations/check
- GET /api/bank/{id}/farmer/{id}/data (with access guard)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import RuleSet
from backend.app.repositories import get_authorization_repo, get_rule_set_repo


def _seed():
    get_authorization_repo().clear()
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-auth-api", version="AUTH_API_V1", name="Auth API", is_active=True,
        config={"experience": {
            "dimensions": ["減量", "增匯", "循環", "綠色治理"],
            "annual_limit_per_dimension": 250, "total_limit": 1000,
            "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
            "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
            "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                       "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
        }},
    ))


def _future(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


class TestGrantEndpoint:
    """Test POST /api/authorizations/grant."""

    def test_grant_success(self, client, test_data_dir):
        _seed()
        response = client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-api-g",
            "institution_id": "bank-api-g",
            "purpose": "Loan application",
            "data_scope": ["IDENTITY", "TRANSACTION"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        assert response.status_code == 200
        assert response.json()["authorization"]["status"] == "ACTIVE"

    def test_grant_duplicate_400(self, client, test_data_dir):
        _seed()
        payload = {
            "farmer_id": "farmer-api-dup",
            "institution_id": "bank-api-dup",
            "purpose": "Test",
            "data_scope": ["IDENTITY"],
            "start_at": _past(),
            "expire_at": _future(),
        }
        client.post("/api/authorizations/grant", json=payload)
        response = client.post("/api/authorizations/grant", json=payload)
        assert response.status_code == 400


class TestRevokeEndpoint:
    """Test POST /api/authorizations/{id}/revoke."""

    def test_revoke_success(self, client, test_data_dir):
        _seed()
        resp = client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-api-rev",
            "institution_id": "bank-api-rev",
            "purpose": "Test",
            "data_scope": ["IDENTITY"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        auth_id = resp.json()["authorization"]["id"]
        response = client.post(f"/api/authorizations/{auth_id}/revoke")
        assert response.status_code == 200
        assert response.json()["authorization"]["status"] == "REVOKED"


class TestListEndpoints:
    """Test GET listing endpoints."""

    def test_farmer_authorizations(self, client, test_data_dir):
        _seed()
        client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-list",
            "institution_id": "bank-list",
            "purpose": "Test",
            "data_scope": ["IDENTITY"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        response = client.get("/api/farmers/farmer-list/authorizations")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_bank_authorizations(self, client, test_data_dir):
        _seed()
        client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-bank-list",
            "institution_id": "bank-blist",
            "purpose": "Test",
            "data_scope": ["IDENTITY"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        response = client.get("/api/banks/bank-blist/authorizations")
        assert response.status_code == 200
        assert response.json()["count"] == 1


class TestCheckEndpoint:
    """Test POST /api/authorizations/check."""

    def test_check_authorized(self, client, test_data_dir):
        _seed()
        client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-check",
            "institution_id": "bank-check",
            "purpose": "Test",
            "data_scope": ["IDENTITY"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        response = client.post("/api/authorizations/check", json={
            "institution_id": "bank-check",
            "farmer_id": "farmer-check",
        })
        assert response.status_code == 200
        assert response.json()["authorized"] is True

    def test_check_unauthorized(self, client, test_data_dir):
        _seed()
        response = client.post("/api/authorizations/check", json={
            "institution_id": "unknown-bank",
            "farmer_id": "unknown-farmer",
        })
        assert response.status_code == 200
        assert response.json()["authorized"] is False


class TestBankAccessEndpoint:
    """Test GET /api/bank/{id}/farmer/{id}/data — access guard enforcement."""

    def test_authorized_bank_gets_data(self, client, test_data_dir):
        _seed()
        client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-access",
            "institution_id": "bank-access",
            "purpose": "Test",
            "data_scope": ["IDENTITY", "TRANSACTION"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        response = client.get("/api/bank/bank-access/farmer/farmer-access/data")
        assert response.status_code == 200
        data = response.json()
        assert data["authorized"] is True
        assert "experience" in data
        assert "indicators" in data
        assert "data_health" in data

    def test_unauthorized_bank_gets_403(self, client, test_data_dir):
        _seed()
        response = client.get("/api/bank/unknown-bank/farmer/unknown-farmer/data")
        assert response.status_code == 403

    def test_revoked_authorization_gets_403(self, client, test_data_dir):
        _seed()
        resp = client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-revoked",
            "institution_id": "bank-revoked",
            "purpose": "Test",
            "data_scope": ["IDENTITY"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        auth_id = resp.json()["authorization"]["id"]
        client.post(f"/api/authorizations/{auth_id}/revoke")

        response = client.get("/api/bank/bank-revoked/farmer/farmer-revoked/data")
        assert response.status_code == 403
