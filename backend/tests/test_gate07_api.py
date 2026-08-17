"""
GATE-07 Tests: Indicators API Endpoints

Verifies:
- GET /api/farmers/{id}/indicators
- POST /api/farmers/{id}/indicators/calculate
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import RuleSet
from backend.app.repositories import get_indicator_repo, get_rule_set_repo


def _seed():
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-ind-api", version="IND_API_V1", name="Ind API",
        is_active=True,
        config={"experience": {
            "dimensions": ["減量", "增匯", "循環", "綠色治理"],
            "annual_limit_per_dimension": 250, "total_limit": 1000,
            "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
            "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
            "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                       "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
        }},
    ))
    get_indicator_repo().clear()


class TestGetIndicators:
    """Test GET /api/farmers/{id}/indicators."""

    def test_empty_indicators(self, client, test_data_dir):
        _seed()
        response = client.get("/api/farmers/farmer-ind-api/indicators")
        assert response.status_code == 200
        data = response.json()
        assert data["indicator_count"] == 0

    def test_after_calculate(self, client, test_data_dir):
        _seed()
        client.post("/api/farmers/farmer-ind-api/indicators/calculate")
        response = client.get("/api/farmers/farmer-ind-api/indicators")
        assert response.status_code == 200
        data = response.json()
        assert data["indicator_count"] == 4
        assert "completeness" in data["indicators"]
        assert "credibility" in data["indicators"]
        assert "business_maturity" in data["indicators"]
        assert "green_maturity" in data["indicators"]


class TestCalculateIndicators:
    """Test POST /api/farmers/{id}/indicators/calculate."""

    def test_calculate_returns_four(self, client, test_data_dir):
        _seed()
        response = client.post("/api/farmers/farmer-calc/indicators/calculate")
        assert response.status_code == 200
        data = response.json()
        assert len(data["indicators"]) == 4
        assert data["rule_version"] == "IND_API_V1"

    def test_calculate_has_traces(self, client, test_data_dir):
        _seed()
        response = client.post("/api/farmers/farmer-trace-api/indicators/calculate")
        data = response.json()
        for ind_type, ind_data in data["indicators"].items():
            assert "calculation_trace" in ind_data
            assert "score" in ind_data
            assert "level" in ind_data

    def test_note_about_independence(self, client, test_data_dir):
        _seed()
        client.post("/api/farmers/farmer-note/indicators/calculate")
        response = client.get("/api/farmers/farmer-note/indicators")
        data = response.json()
        assert "不得" in data["note"] or "獨立" in data["note"]
