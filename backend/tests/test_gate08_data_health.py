"""
GATE-08 Tests: Data Health

Verifies priority-based determination:
- GRAY: no data / not applicable
- RED: critical anomalies, V0, invalid, missing required fields
- YELLOW: warnings, expiring soon, V1 only
- GREEN: valid data, no issues

Per AGENTS.md §12: RED ≠ rejected, GRAY ≠ poor.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    Anomaly, AnomalySeverity, AnomalyType,
    DataDomain, DataHealthStatus, RuleSet, SourceLevel,
    StandardizedRecord,
)
from backend.app.repositories import (
    get_anomaly_repo, get_data_health_repo, get_document_repo,
    get_rule_set_repo, get_standardized_record_repo,
)
from backend.app.services.data_health.calculate import (
    calculate_all_data_health,
    calculate_domain_health,
    get_farmer_data_health,
)


def _seed_rules():
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-dh", version="DH_TEST_V1", name="DH Test",
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
                "domain_required_fields": {
                    "IDENTITY": ["姓名"],
                    "CERTIFICATION": ["認證機構", "有效期限"],
                    "TRANSACTION": ["交易金額", "交易日期"],
                },
                "expiry_warning_days": 90,
                "critical_anomaly_types": ["EXPIRED", "VERIFICATION_FAILED"],
            },
        },
    ))


def _clear():
    get_standardized_record_repo().clear()
    get_document_repo().clear()
    get_anomaly_repo().clear()
    get_data_health_repo().clear()


class TestGrayStatus:
    """GRAY: no data provided."""

    def test_no_data_returns_gray(self, test_data_dir):
        _seed_rules()
        _clear()
        result = calculate_domain_health("farmer-gray", DataDomain.IDENTITY)
        assert result.status == DataHealthStatus.GRAY
        assert len(result.reasons) > 0
        assert len(result.actions) > 0

    def test_gray_for_each_empty_domain(self, test_data_dir):
        _seed_rules()
        _clear()
        results = calculate_all_data_health("farmer-all-gray")
        for r in results:
            assert r.status == DataHealthStatus.GRAY


class TestRedStatus:
    """RED: critical issues."""

    def test_critical_anomaly_triggers_red(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="dh-red-rec", document_id="dh-red-doc", farmer_id="farmer-red",
            domain=DataDomain.CERTIFICATION, record_type="test",
            source_level=SourceLevel.V2,
            data={"認證機構": "X", "有效期限": "2030-01-01"}, is_valid=True,
        ))
        anomaly_repo = get_anomaly_repo()
        anomaly_repo.create(Anomaly(
            id="dh-crit-anom", record_id="dh-red-rec",
            anomaly_type=AnomalyType.EXPIRED, severity=AnomalySeverity.CRITICAL,
            description="expired", is_resolved=False,
        ))
        result = calculate_domain_health("farmer-red", DataDomain.CERTIFICATION)
        assert result.status == DataHealthStatus.RED
        assert "重大異常" in result.reasons[0]

    def test_v0_record_triggers_red(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="dh-v0-rec", document_id="dh-v0-doc", farmer_id="farmer-v0red",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V0,
            data={"姓名": "X"}, is_valid=True,
        ))
        result = calculate_domain_health("farmer-v0red", DataDomain.IDENTITY)
        assert result.status == DataHealthStatus.RED
        assert any("V0" in r for r in result.reasons)

    def test_invalid_record_triggers_red(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="dh-inv-rec", document_id="dh-inv-doc", farmer_id="farmer-inv-red",
            domain=DataDomain.TRANSACTION, record_type="test",
            source_level=SourceLevel.V2,
            data={"交易金額": "100", "交易日期": "2026-01-01"}, is_valid=False,
        ))
        result = calculate_domain_health("farmer-inv-red", DataDomain.TRANSACTION)
        assert result.status == DataHealthStatus.RED

    def test_missing_required_field_triggers_red(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        # CERTIFICATION requires 認證機構 and 有效期限, only provide one
        rec_repo.create(StandardizedRecord(
            id="dh-miss-rec", document_id="dh-miss-doc", farmer_id="farmer-miss",
            domain=DataDomain.CERTIFICATION, record_type="test",
            source_level=SourceLevel.V2,
            data={"認證機構": "X"}, is_valid=True,  # Missing 有效期限
        ))
        result = calculate_domain_health("farmer-miss", DataDomain.CERTIFICATION)
        assert result.status == DataHealthStatus.RED
        assert any("必要欄位" in r for r in result.reasons)


class TestYellowStatus:
    """YELLOW: minor issues."""

    def test_warning_anomaly_triggers_yellow(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="dh-warn-rec", document_id="dh-warn-doc", farmer_id="farmer-yellow",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V2,
            data={"姓名": "Test"}, is_valid=True,
        ))
        anomaly_repo = get_anomaly_repo()
        anomaly_repo.create(Anomaly(
            id="dh-warn-anom", record_id="dh-warn-rec",
            anomaly_type=AnomalyType.OCR_LOW_CONFIDENCE, severity=AnomalySeverity.WARNING,
            description="low confidence", is_resolved=False,
        ))
        result = calculate_domain_health("farmer-yellow", DataDomain.IDENTITY)
        assert result.status == DataHealthStatus.YELLOW

    def test_v1_only_triggers_yellow(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="dh-v1-rec", document_id="dh-v1-doc", farmer_id="farmer-v1only",
            domain=DataDomain.GREEN_ACTION, record_type="test",
            source_level=SourceLevel.V1,
            data={"活動名稱": "Test"}, is_valid=True,
        ))
        result = calculate_domain_health("farmer-v1only", DataDomain.GREEN_ACTION)
        assert result.status == DataHealthStatus.YELLOW
        assert any("V1" in r for r in result.reasons)


class TestGreenStatus:
    """GREEN: valid data, no issues."""

    def test_good_data_returns_green(self, test_data_dir):
        _seed_rules()
        _clear()
        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="dh-green-rec", document_id="dh-green-doc", farmer_id="farmer-green",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V3,
            data={"姓名": "陳小農"}, is_valid=True,
        ))
        result = calculate_domain_health("farmer-green", DataDomain.IDENTITY)
        assert result.status == DataHealthStatus.GREEN
        assert any("可供參考" in r for r in result.reasons)


class TestCalculateAll:
    """Test full data health calculation."""

    def test_returns_all_domains(self, test_data_dir):
        _seed_rules()
        _clear()
        results = calculate_all_data_health("farmer-all-dh")
        assert len(results) == 7  # All 7 domains

    def test_persists_results(self, test_data_dir):
        _seed_rules()
        _clear()
        calculate_all_data_health("farmer-persist-dh")
        stored = get_farmer_data_health("farmer-persist-dh")
        assert len(stored) == 7

    def test_replaces_on_recalculate(self, test_data_dir):
        _seed_rules()
        _clear()
        calculate_all_data_health("farmer-replace-dh")
        calculate_all_data_health("farmer-replace-dh")
        stored = get_farmer_data_health("farmer-replace-dh")
        assert len(stored) == 7  # Still 7, not 14


class TestResultStructure:
    """Test DataHealthResult has required fields."""

    def test_has_status_reasons_actions(self, test_data_dir):
        _seed_rules()
        _clear()
        result = calculate_domain_health("farmer-struct", DataDomain.LOAN_PURPOSE)
        assert result.status is not None
        assert isinstance(result.reasons, list)
        assert isinstance(result.actions, list)
        assert result.rule_version == "DH_TEST_V1"
        assert result.calculated_at is not None
