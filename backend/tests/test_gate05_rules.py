"""
GATE-05 Tests: Rule Engine

Verifies:
- Rule loading from repository
- Active version selection
- Specific version selection
- Experience rules typed access
- Indicator rules typed access
- Data health rules typed access
- Calculation trace creation
- Config validation
- Historical preservation (no overwrite)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import RuleSet
from backend.app.repositories import get_rule_set_repo
from backend.app.rules.engine import (
    CalculationTrace,
    RuleEngine,
    RuleEngineError,
    get_active_engine,
    get_engine_for_version,
)


def _seed_rule_set():
    """Create a valid rule set for testing."""
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-test-v1",
        version="TEST_V1",
        name="Test Rules V1",
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
            "indicators": {
                "completeness_weights": {"core_required": 3, "important_supporting": 2, "supplementary": 1},
                "credibility_factors": ["source_level", "expiry"],
                "maturity_factors": ["record_period", "data_variety"],
                "green_maturity_factors": ["experience_value", "dimension_breadth"],
                "level_thresholds": {
                    "completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]],
                    "credibility": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]],
                },
            },
            "data_health": {
                "priority_order": ["GRAY", "RED", "YELLOW", "GREEN"],
                "domain_required_fields": {"IDENTITY": ["姓名"], "CERTIFICATION": ["認證機構", "有效期限"]},
                "expiry_warning_days": 90,
                "critical_anomaly_types": ["EXPIRED", "VERIFICATION_FAILED"],
            },
        },
    ))


class TestRuleLoading:
    """Test rule set loading and version selection."""

    def test_load_active_rule_set(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        assert engine.version == "TEST_V1"

    def test_load_specific_version(self, test_data_dir):
        _seed_rule_set()
        engine = get_engine_for_version("TEST_V1")
        assert engine.version == "TEST_V1"

    def test_load_nonexistent_version_raises(self, test_data_dir):
        _seed_rule_set()
        with pytest.raises(RuleEngineError):
            get_engine_for_version("NONEXISTENT_V99")

    def test_no_active_rule_raises(self, test_data_dir):
        repo = get_rule_set_repo()
        repo.clear()
        with pytest.raises(RuleEngineError, match="No active rule set"):
            get_active_engine()

    def test_rule_set_accessible(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        assert engine.rule_set is not None
        assert engine.rule_set.name == "Test Rules V1"

    def test_config_accessible(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        assert "experience" in engine.config


class TestExperienceRules:
    """Test typed experience rules access."""

    def test_dimensions(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_experience_rules()
        assert rules.dimensions == ["減量", "增匯", "循環", "綠色治理"]

    def test_annual_limit(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_experience_rules()
        assert rules.annual_limit_per_dimension == 250

    def test_total_limit(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_experience_rules()
        assert rules.total_limit == 1000

    def test_base_values(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_experience_rules()
        assert rules.base_values["BASIC"] == 20
        assert rules.base_values["SUSTAINED"] == 50
        assert rules.base_values["CERTIFIED"] == 100

    def test_source_ratios(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_experience_rules()
        assert rules.source_ratios["V3"] == 1.0
        assert rules.source_ratios["V0"] == 0.0

    def test_levels(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_experience_rules()
        assert rules.levels["L0"] == [0, 0]
        assert rules.levels["L5"] == [801, 1000]


class TestIndicatorRules:
    """Test typed indicator rules access."""

    def test_completeness_weights(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_indicator_rules()
        assert rules.completeness_weights["core_required"] == 3

    def test_credibility_factors(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_indicator_rules()
        assert "source_level" in rules.credibility_factors

    def test_level_thresholds(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_indicator_rules()
        assert "completeness" in rules.level_thresholds


class TestDataHealthRules:
    """Test typed data health rules access."""

    def test_priority_order(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_data_health_rules()
        assert rules.priority_order == ["GRAY", "RED", "YELLOW", "GREEN"]

    def test_domain_required_fields(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_data_health_rules()
        assert "IDENTITY" in rules.domain_required_fields

    def test_expiry_warning_days(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_data_health_rules()
        assert rules.expiry_warning_days == 90

    def test_critical_anomaly_types(self, test_data_dir):
        _seed_rule_set()
        rules = get_active_engine().get_data_health_rules()
        assert "EXPIRED" in rules.critical_anomaly_types


class TestCalculationTrace:
    """Test calculation trace creation."""

    def test_trace_has_version(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        trace = engine.create_trace(evidence_ids=["doc-1"], trace="test calc")
        assert trace.rule_version == "TEST_V1"

    def test_trace_has_timestamp(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        trace = engine.create_trace()
        assert trace.calculated_at is not None

    def test_trace_has_evidence_ids(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        trace = engine.create_trace(evidence_ids=["a", "b"])
        assert trace.input_evidence_ids == ["a", "b"]

    def test_trace_has_calculation_text(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        trace = engine.create_trace(trace="BASIC(20) × V2(1.0) = 20")
        assert "BASIC(20)" in trace.calculation_trace


class TestConfigValidation:
    """Test rule config validation."""

    def test_valid_config_no_errors(self, test_data_dir):
        _seed_rule_set()
        engine = get_active_engine()
        errors = engine.validate_config()
        assert errors == []

    def test_missing_experience_section(self, test_data_dir):
        repo = get_rule_set_repo()
        repo.clear()
        repo.create(RuleSet(
            id="rs-bad", version="BAD_V1", name="Bad",
            is_active=True, config={},
        ))
        engine = get_active_engine()
        errors = engine.validate_config()
        assert any("experience" in e for e in errors)

    def test_missing_base_values(self, test_data_dir):
        repo = get_rule_set_repo()
        repo.clear()
        repo.create(RuleSet(
            id="rs-bad2", version="BAD_V2", name="Bad2",
            is_active=True, config={"experience": {"total_limit": 1000, "source_ratios": {"V0":0,"V1":0.5,"V2":1,"V3":1}}},
        ))
        engine = get_active_engine()
        errors = engine.validate_config()
        assert any("base_values" in e for e in errors)


class TestHistoricalPreservation:
    """Test that multiple rule versions can coexist."""

    def test_multiple_versions_coexist(self, test_data_dir):
        repo = get_rule_set_repo()
        repo.clear()
        repo.create(RuleSet(
            id="rs-v1", version="V1", name="V1",
            is_active=False, config={"experience": {"total_limit": 500, "base_values": {"BASIC":10,"SUSTAINED":30,"CERTIFIED":60}, "source_ratios": {"V0":0,"V1":0.5,"V2":1,"V3":1}}},
        ))
        repo.create(RuleSet(
            id="rs-v2", version="V2", name="V2",
            is_active=True, config={"experience": {"total_limit": 1000, "base_values": {"BASIC":20,"SUSTAINED":50,"CERTIFIED":100}, "source_ratios": {"V0":0,"V1":0.5,"V2":1,"V3":1}}},
        ))

        engine_v1 = get_engine_for_version("V1")
        engine_v2 = get_engine_for_version("V2")

        assert engine_v1.get_experience_rules().total_limit == 500
        assert engine_v2.get_experience_rules().total_limit == 1000
