"""
GATE-06 Tests: Experience API Endpoints

Verifies:
- POST /api/experience/calculate
- GET /api/farmers/{id}/experience
- GET /api/farmers/{id}/experience/history
- POST /api/farmers/{id}/experience/recalculate
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    ActionLevel, GreenAction, GreenDimension, RuleSet,
)
from backend.app.repositories import (
    get_experience_repo, get_green_action_repo, get_rule_set_repo,
)


def _seed(test_data_dir):
    """Set up rules and a green action for API testing."""
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-api-exp", version="API_EXP_V1", name="API Exp",
        is_active=True,
        config={
            "experience": {
                "dimensions": ["減量", "增匯", "循環", "綠色治理"],
                "annual_limit_per_dimension": 250,
                "total_limit": 1000,
                "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
                "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
                "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                           "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
            },
        },
    ))

    ga_repo = get_green_action_repo()
    ga_repo.clear()
    ga_repo.create(GreenAction(
        id="ga-api-1", farmer_id="farmer-api-exp",
        dimension=GreenDimension.REDUCTION, action_level=ActionLevel.SUSTAINED,
        description="API test action", action_date="2026-06-01",
    ))
    ga_repo.create(GreenAction(
        id="ga-api-2", farmer_id="farmer-api-exp",
        dimension=GreenDimension.CIRCULAR, action_level=ActionLevel.BASIC,
        description="API test action 2", action_date="2026-06-15",
    ))

    get_experience_repo().clear()


class TestCalculateEndpoint:
    """Test POST /api/experience/calculate."""

    def test_calculate_success(self, client, test_data_dir):
        _seed(test_data_dir)
        response = client.post(
            "/api/experience/calculate",
            json={"green_action_id": "ga-api-1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "transaction" in data
        assert data["transaction"]["base_value"] == 50
        assert data["transaction"]["dimension"] == "減量"

    def test_calculate_nonexistent_action(self, client, test_data_dir):
        _seed(test_data_dir)
        response = client.post(
            "/api/experience/calculate",
            json={"green_action_id": "nonexistent"},
        )
        assert response.status_code == 404

    def test_calculate_duplicate_rejected(self, client, test_data_dir):
        _seed(test_data_dir)
        client.post("/api/experience/calculate", json={"green_action_id": "ga-api-1"})
        response = client.post(
            "/api/experience/calculate",
            json={"green_action_id": "ga-api-1"},
        )
        assert response.status_code == 400
        assert "已計算過" in response.json()["detail"]


class TestSummaryEndpoint:
    """Test GET /api/farmers/{id}/experience."""

    def test_summary_empty(self, client, test_data_dir):
        _seed(test_data_dir)
        response = client.get("/api/farmers/farmer-api-exp/experience")
        assert response.status_code == 200
        data = response.json()
        assert data["total_experience"] == 0
        assert data["level"] == "L0"

    def test_summary_after_calculation(self, client, test_data_dir):
        _seed(test_data_dir)
        client.post("/api/experience/calculate", json={"green_action_id": "ga-api-1"})
        response = client.get("/api/farmers/farmer-api-exp/experience")
        data = response.json()
        assert data["total_experience"] > 0
        assert data["transaction_count"] == 1
        assert data["rule_version"] == "API_EXP_V1"


class TestHistoryEndpoint:
    """Test GET /api/farmers/{id}/experience/history."""

    def test_history(self, client, test_data_dir):
        _seed(test_data_dir)
        client.post("/api/experience/calculate", json={"green_action_id": "ga-api-1"})
        client.post("/api/experience/calculate", json={"green_action_id": "ga-api-2"})
        response = client.get("/api/farmers/farmer-api-exp/experience/history")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2


class TestRecalculateEndpoint:
    """Test POST /api/farmers/{id}/experience/recalculate."""

    def test_recalculate(self, client, test_data_dir):
        _seed(test_data_dir)
        response = client.post("/api/farmers/farmer-api-exp/experience/recalculate")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["transaction_count"] == 2
        assert data["summary"]["total_experience"] > 0
