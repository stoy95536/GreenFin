"""
GATE-06 Tests: Experience Calculation

Verifies:
- Base value calculation (BASIC=20, SUSTAINED=50, CERTIFIED=100)
- Source recognition ratio (V3=1.0, V2=1.0, V1=0.5, V0=0.0)
- Dimension annual limit (250)
- Total limit (1000)
- Duplicate protection
- Level determination (L0-L5)
- Evidence traceability
- Rule version preserved
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    ActionLevel, GreenAction, GreenDimension, RuleSet,
    ExperienceTransaction, SourceLevel, StandardizedRecord,
    DataDomain, VerificationResult,
)
from backend.app.repositories import (
    get_experience_repo, get_green_action_repo, get_rule_set_repo,
    get_standardized_record_repo, get_verification_repo,
)
from backend.app.services.experience.calculate import (
    ExperienceError,
    calculate_experience,
    get_farmer_experience_summary,
    get_farmer_experience_history,
    recalculate_farmer_experience,
)


def _seed_rules():
    """Create rule set for experience tests."""
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-exp-test", version="TEST_EXP_V1", name="Exp Test",
        is_active=True,
        config={
            "experience": {
                "dimensions": ["減量", "增匯", "循環", "綠色治理"],
                "annual_limit_per_dimension": 250,
                "total_limit": 1000,
                "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
                "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
                "levels": {
                    "L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                    "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000],
                },
            },
        },
    ))


def _create_action(id, farmer_id="farmer-exp", dimension=GreenDimension.REDUCTION,
                   level=ActionLevel.BASIC, evidence_ids=None):
    """Helper to create a green action."""
    ga_repo = get_green_action_repo()
    if ga_repo.exists(id):
        ga_repo.delete(id)
    action = GreenAction(
        id=id, farmer_id=farmer_id, dimension=dimension,
        action_level=level, description="Test action",
        action_date="2026-06-01",
        evidence_record_ids=evidence_ids or [],
    )
    ga_repo.create(action)
    return action


class TestBaseValueCalculation:
    """Test base value from action level."""

    def test_basic_action_20(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-basic", level=ActionLevel.BASIC)
        txn = calculate_experience(action)
        assert txn.base_value == 20

    def test_sustained_action_50(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-sustained", level=ActionLevel.SUSTAINED)
        txn = calculate_experience(action)
        assert txn.base_value == 50

    def test_certified_action_100(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-certified", level=ActionLevel.CERTIFIED)
        txn = calculate_experience(action)
        assert txn.base_value == 100


class TestSourceRatio:
    """Test source recognition ratio."""

    def test_no_evidence_uses_v1_ratio(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-no-ev", evidence_ids=[])
        txn = calculate_experience(action)
        assert txn.source_recognition_ratio == 0.5
        assert txn.effective_value == 10.0  # 20 * 0.5

    def test_v3_evidence_full_ratio(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        get_standardized_record_repo().clear()
        get_verification_repo().clear()

        # Create record + verification at V3
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="rec-v3", document_id="doc-x", farmer_id="farmer-exp",
            domain=DataDomain.GREEN_ACTION, record_type="test",
            source_level=SourceLevel.V3, data={},
        ))
        ver_repo = get_verification_repo()
        ver_repo.create(VerificationResult(
            id="ver-v3", record_id="rec-v3",
            source_level=SourceLevel.V3, reason="V3 verified",
        ))

        action = _create_action("ga-v3", evidence_ids=["rec-v3"])
        txn = calculate_experience(action)
        assert txn.source_recognition_ratio == 1.0
        assert txn.effective_value == 20.0

    def test_v0_evidence_zero_ratio(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        get_standardized_record_repo().clear()
        get_verification_repo().clear()

        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="rec-v0", document_id="doc-y", farmer_id="farmer-exp",
            domain=DataDomain.GREEN_ACTION, record_type="test",
            source_level=SourceLevel.V0, data={},
        ))
        ver_repo = get_verification_repo()
        ver_repo.create(VerificationResult(
            id="ver-v0", record_id="rec-v0",
            source_level=SourceLevel.V0, reason="V0 failed",
        ))

        action = _create_action("ga-v0", evidence_ids=["rec-v0"])
        txn = calculate_experience(action)
        assert txn.source_recognition_ratio == 0.0
        assert txn.effective_value == 0.0


class TestDimensionLimit:
    """Test annual dimension limit (250)."""

    def test_within_limit(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-lim1", level=ActionLevel.CERTIFIED)
        txn = calculate_experience(action)
        assert txn.effective_value == 50.0  # 100 * 0.5 (no evidence = V1)

    def test_capped_at_dimension_limit(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        get_green_action_repo().clear()

        # Fill up with 5 CERTIFIED actions (each 50 with V1 ratio) = 250
        for i in range(5):
            a = _create_action(f"ga-fill-{i}", level=ActionLevel.CERTIFIED)
            calculate_experience(a)

        # 6th should be capped
        a6 = _create_action("ga-fill-6", level=ActionLevel.CERTIFIED)
        txn = calculate_experience(a6)
        assert txn.effective_value == 0.0  # Dimension full


class TestDuplicateProtection:
    """Test that same action can't be calculated twice."""

    def test_duplicate_raises(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-dup")
        calculate_experience(action)

        with pytest.raises(ExperienceError, match="已計算過"):
            calculate_experience(action)


class TestLevelDetermination:
    """Test experience level determination."""

    def test_zero_is_l0(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        summary = get_farmer_experience_summary("farmer-empty")
        assert summary["level"] == "L0"

    def test_l1_range(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        # Create a transaction manually for controlled testing
        exp_repo = get_experience_repo()
        exp_repo.create(ExperienceTransaction(
            id="txn-l1", farmer_id="farmer-lvl", green_action_id="ga-x",
            dimension=GreenDimension.REDUCTION, base_value=20,
            source_recognition_ratio=1.0, effective_value=100.0,
            rule_version="TEST_EXP_V1", calculated_at="2026-08-17T10:00:00+08:00",
        ))
        summary = get_farmer_experience_summary("farmer-lvl")
        assert summary["level"] == "L1"
        assert summary["total_experience"] == 100.0

    def test_l3_range(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        exp_repo = get_experience_repo()
        exp_repo.create(ExperienceTransaction(
            id="txn-l3", farmer_id="farmer-lvl3", green_action_id="ga-y",
            dimension=GreenDimension.CIRCULAR, base_value=100,
            source_recognition_ratio=1.0, effective_value=450.0,
            rule_version="TEST_EXP_V1", calculated_at="2026-08-17T10:00:00+08:00",
        ))
        summary = get_farmer_experience_summary("farmer-lvl3")
        assert summary["level"] == "L3"


class TestTraceability:
    """Test calculation trace and evidence preservation."""

    def test_trace_has_rule_version(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-trace")
        txn = calculate_experience(action)
        assert txn.rule_version == "TEST_EXP_V1"

    def test_trace_has_calculated_at(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-time")
        txn = calculate_experience(action)
        assert txn.calculated_at is not None
        assert "2026" in txn.calculated_at

    def test_trace_has_calculation_text(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        action = _create_action("ga-txt", level=ActionLevel.BASIC)
        txn = calculate_experience(action)
        assert "BASIC" in txn.calculation_trace
        assert "20" in txn.calculation_trace

    def test_trace_has_evidence_ids(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        get_standardized_record_repo().clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="rec-trace", document_id="d-t", farmer_id="farmer-exp",
            domain=DataDomain.GREEN_ACTION, record_type="test",
            source_level=SourceLevel.V2, data={},
        ))
        action = _create_action("ga-ev-trace", evidence_ids=["rec-trace"])
        txn = calculate_experience(action)
        assert "rec-trace" in txn.input_evidence_ids


class TestRecalculate:
    """Test recalculation from scratch."""

    def test_recalculate_clears_and_rebuilds(self, test_data_dir):
        _seed_rules()
        get_experience_repo().clear()
        get_green_action_repo().clear()

        # Create 2 actions
        _create_action("ga-rc1", level=ActionLevel.BASIC)
        _create_action("ga-rc2", level=ActionLevel.SUSTAINED,
                      dimension=GreenDimension.CIRCULAR)

        # Calculate first
        ga_repo = get_green_action_repo()
        calculate_experience(ga_repo.get_by_id("ga-rc1"))
        calculate_experience(ga_repo.get_by_id("ga-rc2"))

        # Recalculate
        summary = recalculate_farmer_experience("farmer-exp")
        assert summary["transaction_count"] == 2
        assert summary["total_experience"] > 0
