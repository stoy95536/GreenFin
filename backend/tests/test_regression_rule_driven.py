"""
Regression Tests: Indicators must be rule-driven

Bug found in architecture review (2026-08-17):
  indicators/calculate.py hardcoded its tier weights and L1-L5 thresholds while still
  stamping every IndicatorResult with rule_version. Editing the rule set changed what
  /api/rules/active/indicators reported but did NOT change any score, so the recorded
  provenance was misleading and AGENTS.md §6/§7/§8 were violated.

These tests change ONLY the rule config and assert the resulting scores change.
If someone reintroduces hardcoded constants, these fail.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    DataDomain, RuleSet, SourceLevel, StandardizedRecord,
)
from backend.app.repositories import (
    get_anomaly_repo, get_document_repo, get_experience_repo,
    get_green_action_repo, get_indicator_repo, get_rule_set_repo,
    get_standardized_record_repo,
)
from backend.app.services.indicators.calculate import (
    calculate_completeness,
    calculate_credibility,
)

FARMER = "farmer-rule-driven"


def _install_rules(indicators_config: dict) -> None:
    """Install a rule set with the given indicators config as the active version."""
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-driven", version="DRIVEN_V1", name="Rule Driven Test", is_active=True,
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
            "indicators": indicators_config,
        },
    ))


def _reset_data() -> None:
    for repo_fn in (
        get_standardized_record_repo, get_document_repo, get_anomaly_repo,
        get_experience_repo, get_green_action_repo, get_indicator_repo,
    ):
        repo_fn().clear()


def _add_record(record_id: str, domain: DataDomain, source_level=SourceLevel.V2) -> None:
    get_standardized_record_repo().create(StandardizedRecord(
        id=record_id, document_id=f"doc-{record_id}", farmer_id=FARMER,
        domain=domain, record_type="test", source_level=source_level,
        data={"x": "y"}, is_valid=True,
    ))


class TestCompletenessIsRuleDriven:
    """Changing tier weights / domain tiers must change the completeness score."""

    def test_domain_tier_change_changes_score(self, test_data_dir):
        _reset_data()
        _add_record("r1", DataDomain.IDENTITY)

        # Config A: IDENTITY is core (weight 3) out of total 3+1 = 4 → 75%
        _install_rules({
            "completeness": {
                "tier_weights": {"core_required": 3, "supplementary": 1},
                "domain_tiers": {
                    "IDENTITY": "core_required",
                    "LOAN_PURPOSE": "supplementary",
                },
            },
            "level_thresholds": {"completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]]},
        })
        score_a = calculate_completeness(FARMER).score

        # Config B: IDENTITY demoted to supplementary (weight 1) out of 1+3 = 4 → 25%
        _install_rules({
            "completeness": {
                "tier_weights": {"core_required": 3, "supplementary": 1},
                "domain_tiers": {
                    "IDENTITY": "supplementary",
                    "LOAN_PURPOSE": "core_required",
                },
            },
            "level_thresholds": {"completeness": [[0, 39], [40, 59], [60, 79], [80, 94], [95, 100]]},
        })
        score_b = calculate_completeness(FARMER).score

        assert score_a == 75.0, f"expected 75.0 from config A, got {score_a}"
        assert score_b == 25.0, f"expected 25.0 from config B, got {score_b}"
        assert score_a != score_b, "Completeness ignored the rule config"

    def test_level_thresholds_change_level(self, test_data_dir):
        _reset_data()
        _add_record("r-lvl", DataDomain.IDENTITY)

        base_completeness = {
            "tier_weights": {"core_required": 1},
            "domain_tiers": {"IDENTITY": "core_required"},
        }

        # Full coverage → 100%. Bands where 100 lands in the 5th band → L5
        _install_rules({
            "completeness": base_completeness,
            "level_thresholds": {"completeness": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]]},
        })
        assert calculate_completeness(FARMER).level == "L5"

        # Same score, but now every band starts at 0 except a very high L5
        _install_rules({
            "completeness": base_completeness,
            "level_thresholds": {"completeness": [[0, 100], [101, 102], [103, 104], [105, 106], [107, 108]]},
        })
        assert calculate_completeness(FARMER).level == "L1", (
            "Level ignored the configured thresholds"
        )


class TestCredibilityIsRuleDriven:
    """Changing source-level scores must change the credibility score."""

    def test_source_level_scores_change_score(self, test_data_dir):
        _reset_data()
        _add_record("r-cred", DataDomain.CERTIFICATION, source_level=SourceLevel.V2)

        common_bands = {"credibility": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]]}

        # V2 worth 67, no anomalies, full traceability bonus 10 → 77
        _install_rules({
            "credibility": {
                "source_level_scores": {"V0": 0, "V1": 33, "V2": 67, "V3": 100},
                "anomaly_penalty_per": 5,
                "anomaly_penalty_max": 30,
                "traceability_bonus_max": 10,
            },
            "level_thresholds": common_bands,
        })
        score_high = calculate_credibility(FARMER).score

        # Same data, but V2 now worth only 10 → 20
        _install_rules({
            "credibility": {
                "source_level_scores": {"V0": 0, "V1": 5, "V2": 10, "V3": 20},
                "anomaly_penalty_per": 5,
                "anomaly_penalty_max": 30,
                "traceability_bonus_max": 10,
            },
            "level_thresholds": common_bands,
        })
        score_low = calculate_credibility(FARMER).score

        assert score_high > score_low, (
            f"Credibility ignored source_level_scores (high={score_high}, low={score_low})"
        )
        assert score_high == 77.0
        assert score_low == 20.0

    def test_traceability_bonus_cap_is_respected(self, test_data_dir):
        _reset_data()
        _add_record("r-bonus", DataDomain.IDENTITY, source_level=SourceLevel.V0)

        _install_rules({
            "credibility": {
                "source_level_scores": {"V0": 0, "V1": 33, "V2": 67, "V3": 100},
                "anomaly_penalty_per": 5,
                "anomaly_penalty_max": 30,
                "traceability_bonus_max": 42,
            },
            "level_thresholds": {"credibility": [[0, 19], [20, 39], [40, 59], [60, 79], [80, 100]]},
        })
        # V0 = 0, full traceability → exactly the configured bonus cap
        assert calculate_credibility(FARMER).score == 42.0


class TestRuleVersionIsHonest:
    """The stamped rule_version must be the version that actually produced the score."""

    def test_stamped_version_matches_active(self, test_data_dir):
        _reset_data()
        _add_record("r-ver", DataDomain.IDENTITY)
        _install_rules({
            "completeness": {
                "tier_weights": {"core_required": 1},
                "domain_tiers": {"IDENTITY": "core_required"},
            },
        })
        result = calculate_completeness(FARMER)
        assert result.rule_version == "DRIVEN_V1"
        assert "DRIVEN_V1" in result.calculation_trace
