"""
GATE-13 Tests: Bank Information Package

Per DEVELOPMENT_PLAN.md verifies:
- Authorization
- Data correctness
- Rule version
- Evidence references
- Disclaimer
- Generation timestamp
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    Authorization, AuthorizationStatus, DataDomain, Document,
    DocumentStatus, ExperienceTransaction, FarmerProfile, Farm,
    GreenDimension, IndicatorResult, DataHealthResult, DataHealthStatus,
    RuleSet, SourceLevel, StandardizedRecord,
)
from backend.app.repositories import (
    get_authorization_repo, get_data_health_repo, get_document_repo,
    get_experience_repo, get_farmer_repo, get_farm_repo,
    get_indicator_repo, get_rule_set_repo, get_standardized_record_repo,
)
from backend.app.services.reports.package import (
    ReportError,
    generate_bank_information_package,
)


def _future(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _seed_report_scenario():
    """Full scenario for report generation."""
    for repo_fn in [get_rule_set_repo, get_farmer_repo, get_farm_repo,
                    get_document_repo, get_standardized_record_repo,
                    get_experience_repo, get_indicator_repo,
                    get_data_health_repo, get_authorization_repo]:
        repo_fn().clear()

    get_rule_set_repo().create(RuleSet(
        id="rs-rpt", version="RPT_V1", name="Report Test", is_active=True,
        config={"experience": {
            "dimensions": ["減量", "增匯", "循環", "綠色治理"],
            "annual_limit_per_dimension": 250, "total_limit": 1000,
            "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
            "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
            "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                       "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
        }},
    ))

    get_farmer_repo().create(FarmerProfile(
        id="farmer-rpt", user_id="user-rpt", real_name="報告測試小農",
    ))
    get_farm_repo().create(Farm(
        id="farm-rpt", farmer_id="farmer-rpt", name="報告農場", location="台南", area_hectares=2.0,
    ))

    get_document_repo().create(Document(
        id="doc-rpt", farmer_id="farmer-rpt", filename="cert.pdf",
        domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V3,
        status=DocumentStatus.VERIFIED,
    ))
    get_standardized_record_repo().create(StandardizedRecord(
        id="rec-rpt", document_id="doc-rpt", farmer_id="farmer-rpt",
        domain=DataDomain.CERTIFICATION, record_type="cert",
        source_level=SourceLevel.V3, data={"認證機構": "X", "有效期限": "2030-01-01"},
    ))

    get_experience_repo().create(ExperienceTransaction(
        id="exp-rpt", farmer_id="farmer-rpt", green_action_id="ga-rpt",
        dimension=GreenDimension.REDUCTION, base_value=100,
        source_recognition_ratio=1.0, effective_value=100.0,
        rule_version="RPT_V1", calculated_at="2026-08-17T10:00:00+08:00",
        input_evidence_ids=["rec-rpt"], calculation_trace="CERTIFIED(100) × V3(1.0) = 100",
    ))

    get_indicator_repo().create(IndicatorResult(
        id="ind-rpt", farmer_id="farmer-rpt", indicator_type="completeness",
        score=50.0, level="L2", rule_version="RPT_V1",
        calculated_at="2026-08-17T10:00:00+08:00", input_evidence_ids=["rec-rpt"],
    ))

    get_data_health_repo().create(DataHealthResult(
        id="dh-rpt", farmer_id="farmer-rpt", domain=DataDomain.CERTIFICATION,
        status=DataHealthStatus.GREEN, reasons=["OK"], actions=[],
        affected_evidence_ids=["rec-rpt"], rule_version="RPT_V1",
        calculated_at="2026-08-17T10:00:00+08:00",
    ))

    get_authorization_repo().create(Authorization(
        id="auth-rpt", farmer_id="farmer-rpt", institution_id="bank-rpt",
        purpose="Loan", data_scope=["CERTIFICATION"],
        start_at=_past(), expire_at=_future(),
        status=AuthorizationStatus.ACTIVE,
    ))


class TestPackageGeneration:
    """Test bank information package generation."""

    def test_generates_package(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["package_type"] == "BANK_INFORMATION_PACKAGE"

    def test_has_authorization(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["authorization"]["institution_id"] == "bank-rpt"
        assert pkg["authorization"]["farmer_id"] == "farmer-rpt"

    def test_has_farmer_profile(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["farmer"]["name"] == "報告測試小農"
        assert len(pkg["farmer"]["farms"]) == 1

    def test_has_experience(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["experience"]["total_experience"] == 100.0

    def test_has_indicators(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert len(pkg["indicators"]) >= 1
        assert pkg["indicators"][0]["rule_version"] == "RPT_V1"

    def test_has_data_health(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert len(pkg["data_health"]) >= 1
        assert pkg["data_health"][0]["status"] == "GREEN"

    def test_has_evidence_summary(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["evidence_summary"]["document_count"] == 1
        assert pkg["evidence_summary"]["record_count"] == 1

    def test_has_traceability(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["traceability"]["all_valid"] is True

    def test_has_disclaimer(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert "授信補充資訊" in pkg["disclaimer"]
        assert "DEMO" in pkg["disclaimer"]

    def test_has_timestamp(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        assert pkg["generated_at"] is not None
        assert "2026" in pkg["generated_at"]

    def test_has_rule_version_in_indicators(self, test_data_dir):
        _seed_report_scenario()
        pkg = generate_bank_information_package("farmer-rpt", "bank-rpt")
        for ind in pkg["indicators"]:
            assert "rule_version" in ind

    def test_unauthorized_raises(self, test_data_dir):
        _seed_report_scenario()
        with pytest.raises(ReportError, match="無有效授權"):
            generate_bank_information_package("farmer-rpt", "unauthorized-bank")

    def test_nonexistent_farmer_raises(self, test_data_dir):
        _seed_report_scenario()
        # Create auth for nonexistent farmer
        get_authorization_repo().create(Authorization(
            id="auth-ghost", farmer_id="ghost-farmer", institution_id="bank-rpt",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_past(), expire_at=_future(),
            status=AuthorizationStatus.ACTIVE,
        ))
        with pytest.raises(ReportError, match="不存在"):
            generate_bank_information_package("ghost-farmer", "bank-rpt")


class TestReportAPI:
    """Test GET /api/reports/bank-package/{institution_id}/{farmer_id}."""

    def test_api_returns_package(self, client, test_data_dir):
        _seed_report_scenario()
        response = client.get("/api/reports/bank-package/bank-rpt/farmer-rpt")
        assert response.status_code == 200
        data = response.json()
        assert data["package_type"] == "BANK_INFORMATION_PACKAGE"
        assert "disclaimer" in data

    def test_api_unauthorized_403(self, client, test_data_dir):
        _seed_report_scenario()
        response = client.get("/api/reports/bank-package/bad-bank/farmer-rpt")
        assert response.status_code == 403
