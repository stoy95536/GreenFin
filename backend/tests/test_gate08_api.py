"""
GATE-08 Tests: Data Health API Endpoints

Verifies:
- GET /api/farmers/{id}/data-health
- POST /api/farmers/{id}/data-health/calculate
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import RuleSet
from backend.app.repositories import get_data_health_repo, get_rule_set_repo


def _seed():
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-dh-api", version="DH_API_V1", name="DH API",
        is_active=True,
        config={
            "experience": {
                "dimensions": ["減量", "增匯", "循環", "綠色治理"],
                "annual_limit_per_dimension": 250, "total_limit": 1000,
                "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
                "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
                "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                           "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
            },
            "data_health": {
                "priority_order": ["GRAY", "RED", "YELLOW", "GREEN"],
                "domain_required_fields": {"IDENTITY": ["姓名"]},
                "expiry_warning_days": 90,
                "critical_anomaly_types": ["EXPIRED"],
            },
        },
    ))
    get_data_health_repo().clear()


class TestGetDataHealth:
    """Test GET /api/farmers/{id}/data-health."""

    def test_empty_returns_structure(self, client, test_data_dir):
        _seed()
        response = client.get("/api/farmers/farmer-dh-api/data-health")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert "summary" in data
        assert "note" in data

    def test_after_calculate(self, client, test_data_dir):
        _seed()
        client.post("/api/farmers/farmer-dh-calc/data-health/calculate")
        response = client.get("/api/farmers/farmer-dh-calc/data-health")
        data = response.json()
        assert data["domain_count"] == 7
        assert data["summary"]["GRAY"] == 7  # No data = all GRAY


class TestCalculateDataHealth:
    """Test POST /api/farmers/{id}/data-health/calculate."""

    def test_calculate_returns_domains(self, client, test_data_dir):
        _seed()
        response = client.post("/api/farmers/farmer-dh-post/data-health/calculate")
        assert response.status_code == 200
        data = response.json()
        assert len(data["domains"]) == 7
        assert "summary" in data

    def test_note_about_red_gray(self, client, test_data_dir):
        _seed()
        response = client.get("/api/farmers/farmer-dh-note/data-health")
        data = response.json()
        assert "RED" in data["note"] or "不代表" in data["note"]
