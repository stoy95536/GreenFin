"""
GATE-05 Tests: Rule Engine API Endpoints

Verifies:
- GET /api/rules — list versions
- GET /api/rules/active — get active config
- GET /api/rules/active/experience — experience rules
- GET /api/rules/active/indicators — indicator rules
- GET /api/rules/active/data-health — data health rules
- GET /api/rules/{version} — specific version
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import RuleSet
from backend.app.repositories import get_rule_set_repo


def _seed_rules():
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-api-test",
        version="GREENFIN_DEMO_V1",
        name="Demo V1",
        is_active=True,
        config={
            "experience": {
                "dimensions": ["減量", "增匯", "循環", "綠色治理"],
                "annual_limit_per_dimension": 250,
                "total_limit": 1000,
                "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
                "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
                "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400], "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
            },
            "indicators": {
                "completeness_weights": {"core_required": 3, "important_supporting": 2, "supplementary": 1},
                "credibility_factors": ["source_level"],
                "maturity_factors": ["record_period"],
                "green_maturity_factors": ["experience_value"],
                "level_thresholds": {"completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]]},
            },
            "data_health": {
                "priority_order": ["GRAY", "RED", "YELLOW", "GREEN"],
                "domain_required_fields": {"IDENTITY": ["姓名"]},
                "expiry_warning_days": 90,
                "critical_anomaly_types": ["EXPIRED"],
            },
        },
    ))


class TestRulesListEndpoint:
    """Test GET /api/rules."""

    def test_list_versions(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["versions"][0]["version"] == "GREENFIN_DEMO_V1"


class TestActiveRulesEndpoint:
    """Test GET /api/rules/active."""

    def test_get_active_rules(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules/active")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "GREENFIN_DEMO_V1"
        assert data["is_valid"] is True

    def test_get_experience_rules(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules/active/experience")
        assert response.status_code == 200
        data = response.json()
        assert data["total_limit"] == 1000
        assert data["base_values"]["BASIC"] == 20

    def test_get_indicator_rules(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules/active/indicators")
        assert response.status_code == 200
        data = response.json()
        assert "completeness_weights" in data

    def test_get_data_health_rules(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules/active/data-health")
        assert response.status_code == 200
        data = response.json()
        assert data["priority_order"] == ["GRAY", "RED", "YELLOW", "GREEN"]


class TestVersionEndpoint:
    """Test GET /api/rules/{version}."""

    def test_get_specific_version(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules/GREENFIN_DEMO_V1")
        assert response.status_code == 200
        assert response.json()["version"] == "GREENFIN_DEMO_V1"

    def test_nonexistent_version_404(self, client, test_data_dir):
        _seed_rules()
        response = client.get("/api/rules/NO_SUCH_VERSION")
        assert response.status_code == 404
