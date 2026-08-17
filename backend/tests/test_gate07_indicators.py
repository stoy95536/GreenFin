"""
GATE-07 Tests: Four Indicators

Verifies each indicator independently:
- Completeness: domain coverage weighted scoring
- Credibility: source level, anomalies, traceability
- Business Maturity: variety, volume, documents, transactions
- Green Maturity: experience, dimensions, V2/V3 ratio

Per AGENTS.md §4.2: indicators must NOT be combined into a single score.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    DataDomain, Document, DocumentStatus, ExperienceTransaction,
    GreenAction, GreenDimension, ActionLevel, RuleSet, SourceLevel,
    StandardizedRecord, VerificationResult, Anomaly, AnomalyType, AnomalySeverity,
)
from backend.app.repositories import (
    get_anomaly_repo, get_document_repo, get_experience_repo,
    get_green_action_repo, get_indicator_repo, get_rule_set_repo,
    get_standardized_record_repo, get_verification_repo,
)
from backend.app.services.indicators.calculate import (
    calculate_all_indicators,
    calculate_completeness,
    calculate_credibility,
    calculate_business_maturity,
    calculate_green_maturity,
    get_farmer_indicators,
)


def _seed_rules():
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-ind", version="IND_TEST_V1", name="Indicator Test",
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


def _clear_all():
    get_standardized_record_repo().clear()
    get_document_repo().clear()
    get_verification_repo().clear()
    get_anomaly_repo().clear()
    get_experience_repo().clear()
    get_green_action_repo().clear()
    get_indicator_repo().clear()


class TestCompleteness:
    """Test 資料完整度 indicator."""

    def test_no_data_low_score(self, test_data_dir):
        _seed_rules()
        _clear_all()
        result = calculate_completeness("farmer-empty")
        assert result.score == 0.0
        assert result.level == "L1"

    def test_full_data_high_score(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        # Create valid records for all 7 domains
        for i, domain in enumerate(DataDomain):
            rec_repo.create(StandardizedRecord(
                id=f"comp-rec-{i}", document_id=f"doc-{i}", farmer_id="farmer-full",
                domain=domain, record_type="test", source_level=SourceLevel.V2,
                data={"test": "data"}, is_valid=True,
            ))
        result = calculate_completeness("farmer-full")
        assert result.score == 100.0
        assert result.level == "L5"

    def test_partial_data_medium_score(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        # Only IDENTITY (weight 3) and TRANSACTION (weight 2) = 5/14 = 35.7%
        rec_repo.create(StandardizedRecord(
            id="comp-p1", document_id="d1", farmer_id="farmer-partial",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V2, data={}, is_valid=True,
        ))
        rec_repo.create(StandardizedRecord(
            id="comp-p2", document_id="d2", farmer_id="farmer-partial",
            domain=DataDomain.TRANSACTION, record_type="test",
            source_level=SourceLevel.V2, data={}, is_valid=True,
        ))
        result = calculate_completeness("farmer-partial")
        assert 30 <= result.score <= 40
        assert result.level == "L1"

    def test_invalid_records_not_counted(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="comp-inv", document_id="d-inv", farmer_id="farmer-inv",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V0, data={}, is_valid=False,
        ))
        result = calculate_completeness("farmer-inv")
        assert result.score == 0.0


class TestCredibility:
    """Test 資料可信度 indicator."""

    def test_no_records_zero(self, test_data_dir):
        _seed_rules()
        _clear_all()
        result = calculate_credibility("farmer-nocred")
        assert result.score == 0.0

    def test_v3_records_high_credibility(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="cred-v3", document_id="d-cred", farmer_id="farmer-cred",
            domain=DataDomain.CERTIFICATION, record_type="test",
            source_level=SourceLevel.V3, data={}, is_valid=True,
        ))
        result = calculate_credibility("farmer-cred")
        assert result.score >= 80  # V3=100 + traceability bonus

    def test_v0_records_low_credibility(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="cred-v0", document_id="d-c0", farmer_id="farmer-cred0",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V0, data={}, is_valid=True,
        ))
        result = calculate_credibility("farmer-cred0")
        assert result.score <= 20

    def test_anomalies_reduce_credibility(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="cred-anom", document_id="d-ca", farmer_id="farmer-anom-cred",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V3, data={}, is_valid=True,
        ))
        anomaly_repo = get_anomaly_repo()
        for i in range(3):
            anomaly_repo.create(Anomaly(
                id=f"anom-cred-{i}", record_id="cred-anom",
                anomaly_type=AnomalyType.EXPIRED, severity=AnomalySeverity.CRITICAL,
                description="test", is_resolved=False,
            ))
        result = calculate_credibility("farmer-anom-cred")
        # V3=100, but -15 from 3 anomalies + traceability bonus ~10 → ~95
        assert result.score < 100


class TestBusinessMaturity:
    """Test 經營成熟度 indicator."""

    def test_no_data_zero(self, test_data_dir):
        _seed_rules()
        _clear_all()
        result = calculate_business_maturity("farmer-nobiz")
        assert result.score == 0.0

    def test_multiple_domains_higher_score(self, test_data_dir):
        _seed_rules()
        _clear_all()
        rec_repo = get_standardized_record_repo()
        doc_repo = get_document_repo()
        for i, domain in enumerate([DataDomain.IDENTITY, DataDomain.TRANSACTION, DataDomain.CERTIFICATION]):
            rec_repo.create(StandardizedRecord(
                id=f"biz-{i}", document_id=f"biz-doc-{i}", farmer_id="farmer-biz",
                domain=domain, record_type="test",
                source_level=SourceLevel.V2, data={}, is_valid=True,
            ))
            doc_repo.create(Document(
                id=f"biz-doc-{i}", farmer_id="farmer-biz", filename=f"doc{i}.pdf",
                domain=domain, source_level=SourceLevel.V2, status=DocumentStatus.VERIFIED,
            ))
        result = calculate_business_maturity("farmer-biz")
        assert result.score > 20  # Has variety, volume, docs, and transactions


class TestGreenMaturity:
    """Test 綠色成熟度 indicator."""

    def test_no_green_data_zero(self, test_data_dir):
        _seed_rules()
        _clear_all()
        result = calculate_green_maturity("farmer-nogreen")
        assert result.score == 0.0

    def test_experience_contributes(self, test_data_dir):
        _seed_rules()
        _clear_all()
        exp_repo = get_experience_repo()
        exp_repo.create(ExperienceTransaction(
            id="green-txn-1", farmer_id="farmer-green", green_action_id="ga-g1",
            dimension=GreenDimension.REDUCTION, base_value=100,
            source_recognition_ratio=1.0, effective_value=100.0,
            rule_version="IND_TEST_V1", calculated_at="2026-08-17T10:00:00+08:00",
        ))
        result = calculate_green_maturity("farmer-green")
        assert result.score > 0
        assert result.details["total_experience"] == 100.0

    def test_multiple_dimensions_higher(self, test_data_dir):
        _seed_rules()
        _clear_all()
        exp_repo = get_experience_repo()
        for i, dim in enumerate([GreenDimension.REDUCTION, GreenDimension.CIRCULAR, GreenDimension.SEQUESTRATION]):
            exp_repo.create(ExperienceTransaction(
                id=f"green-multi-{i}", farmer_id="farmer-multi-green", green_action_id=f"ga-m{i}",
                dimension=dim, base_value=50,
                source_recognition_ratio=1.0, effective_value=50.0,
                rule_version="IND_TEST_V1", calculated_at="2026-08-17T10:00:00+08:00",
            ))
        result = calculate_green_maturity("farmer-multi-green")
        assert result.details["active_dimensions"] == 3
        assert result.score > 30  # 3 dims × 10 = 30 breadth + exp contribution


class TestCalculateAll:
    """Test orchestrated calculation of all 4 indicators."""

    def test_calculate_all_returns_four(self, test_data_dir):
        _seed_rules()
        _clear_all()
        results = calculate_all_indicators("farmer-all")
        assert len(results) == 4
        types = {r.indicator_type for r in results}
        assert types == {"completeness", "credibility", "business_maturity", "green_maturity"}

    def test_calculate_all_persists(self, test_data_dir):
        _seed_rules()
        _clear_all()
        calculate_all_indicators("farmer-persist")
        stored = get_farmer_indicators("farmer-persist")
        assert len(stored) == 4

    def test_recalculate_replaces_old(self, test_data_dir):
        _seed_rules()
        _clear_all()
        calculate_all_indicators("farmer-replace")
        calculate_all_indicators("farmer-replace")
        stored = get_farmer_indicators("farmer-replace")
        assert len(stored) == 4  # Still 4, not 8


class TestIndicatorIndependence:
    """Test that indicators are independent (not combined)."""

    def test_each_has_own_score(self, test_data_dir):
        _seed_rules()
        _clear_all()
        results = calculate_all_indicators("farmer-indep")
        for r in results:
            assert 0 <= r.score <= 100
            assert r.level in ("L1", "L2", "L3", "L4", "L5")

    def test_each_has_trace(self, test_data_dir):
        _seed_rules()
        _clear_all()
        results = calculate_all_indicators("farmer-trace")
        for r in results:
            assert r.rule_version == "IND_TEST_V1"
            assert r.calculated_at is not None
            assert r.calculation_trace != ""
