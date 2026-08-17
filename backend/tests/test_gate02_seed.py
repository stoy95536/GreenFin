"""
GATE-02 Tests: Seed Data Verification

Verifies:
- Seed data can be loaded
- Three demo cases exist (A, B, C)
- Entity counts match expected
- Relationships between seed data are valid
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.repositories import (
    get_user_repo, get_farmer_repo, get_farm_repo, get_crop_repo,
    get_document_repo, get_anomaly_repo, get_green_action_repo,
    get_experience_repo, get_indicator_repo, get_data_health_repo,
    get_authorization_repo, get_bank_case_repo, get_rule_set_repo,
)
from backend.app.seed.seed_data import seed_all


def _run_seed():
    """Helper to run seed in test data dir."""
    seed_all()


class TestSeedDataPopulation:
    """Test that seed data is populated correctly."""

    def test_seed_creates_users(self):
        _run_seed()
        repo = get_user_repo()
        assert repo.count() == 4  # 3 farmers + 1 bank

    def test_seed_creates_farmers(self):
        _run_seed()
        repo = get_farmer_repo()
        assert repo.count() == 3

    def test_seed_creates_farms(self):
        _run_seed()
        repo = get_farm_repo()
        assert repo.count() == 3

    def test_seed_creates_crops(self):
        _run_seed()
        repo = get_crop_repo()
        assert repo.count() == 3

    def test_seed_creates_documents(self):
        _run_seed()
        repo = get_document_repo()
        assert repo.count() == 5

    def test_seed_creates_anomalies(self):
        _run_seed()
        repo = get_anomaly_repo()
        assert repo.count() == 3

    def test_seed_creates_green_actions(self):
        _run_seed()
        repo = get_green_action_repo()
        assert repo.count() == 4

    def test_seed_creates_experience_transactions(self):
        _run_seed()
        repo = get_experience_repo()
        assert repo.count() == 4

    def test_seed_creates_indicator_results(self):
        _run_seed()
        repo = get_indicator_repo()
        assert repo.count() == 12  # 4 indicators × 3 farmers

    def test_seed_creates_data_health_results(self):
        _run_seed()
        repo = get_data_health_repo()
        assert repo.count() == 18  # 6 domains × 3 farmers

    def test_seed_creates_authorization(self):
        _run_seed()
        repo = get_authorization_repo()
        assert repo.count() == 1

    def test_seed_creates_bank_case(self):
        _run_seed()
        repo = get_bank_case_repo()
        assert repo.count() == 1

    def test_seed_creates_rule_set(self):
        _run_seed()
        repo = get_rule_set_repo()
        assert repo.count() == 1
        rs = repo.get_all()[0]
        assert rs.version == "GREENFIN_DEMO_V1"


class TestSeedDataCases:
    """Verify 3 demo cases per AGENTS.md §18."""

    def test_case_a_healthy_farmer(self):
        _run_seed()
        farmer_repo = get_farmer_repo()
        farmer = farmer_repo.get_by_id("farmer-a-chen")
        assert farmer is not None
        assert farmer.real_name == "陳小農"

    def test_case_a_green_data_health(self):
        _run_seed()
        dh_repo = get_data_health_repo()
        results = dh_repo.find_by(farmer_id="farmer-a-chen")
        green_count = sum(1 for r in results if r.status.value == "GREEN")
        assert green_count >= 4  # Most domains should be GREEN

    def test_case_b_needs_improvement(self):
        _run_seed()
        farmer_repo = get_farmer_repo()
        farmer = farmer_repo.get_by_id("farmer-b-lin")
        assert farmer is not None
        assert farmer.real_name == "林阿花"

    def test_case_b_yellow_data_health(self):
        _run_seed()
        dh_repo = get_data_health_repo()
        results = dh_repo.find_by(farmer_id="farmer-b-lin")
        yellow_count = sum(1 for r in results if r.status.value == "YELLOW")
        assert yellow_count >= 2  # Several domains should be YELLOW

    def test_case_c_abnormal(self):
        _run_seed()
        farmer_repo = get_farmer_repo()
        farmer = farmer_repo.get_by_id("farmer-c-wang")
        assert farmer is not None
        assert farmer.real_name == "王大明"

    def test_case_c_red_data_health(self):
        _run_seed()
        dh_repo = get_data_health_repo()
        results = dh_repo.find_by(farmer_id="farmer-c-wang")
        red_count = sum(1 for r in results if r.status.value == "RED")
        assert red_count >= 3  # Multiple domains should be RED

    def test_case_c_has_anomalies(self):
        _run_seed()
        anomaly_repo = get_anomaly_repo()
        all_anomalies = anomaly_repo.get_all()
        # All anomalies should be from Case C
        assert len(all_anomalies) == 3
