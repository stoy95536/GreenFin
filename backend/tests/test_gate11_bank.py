"""
GATE-11 Tests: Bank Workflow API

Verifies:
- GET /api/bank/{id}/cases — list authorized cases
- GET /api/bank/{id}/cases/{farmer_id} — case detail (guarded)
- GET /api/bank/{id}/cases/{farmer_id}/evidence — evidence chain (guarded)
- GET /api/bank/{id}/cases/{farmer_id}/trace/{record_id} — single record trace
- Unauthorized bank → 403
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    Authorization, AuthorizationStatus, DataDomain, Document, DocumentStatus,
    FarmerProfile, Farm, RuleSet, SourceLevel, StandardizedRecord,
)
from backend.app.repositories import (
    get_authorization_repo, get_document_repo, get_farmer_repo,
    get_farm_repo, get_rule_set_repo, get_standardized_record_repo,
)


def _future(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _seed_bank_scenario():
    """Set up a complete bank scenario with authorization and farmer data."""
    get_authorization_repo().clear()
    get_farmer_repo().clear()
    get_farm_repo().clear()
    get_document_repo().clear()
    get_standardized_record_repo().clear()

    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-bank", version="BANK_V1", name="Bank Test", is_active=True,
        config={"experience": {
            "dimensions": ["減量", "增匯", "循環", "綠色治理"],
            "annual_limit_per_dimension": 250, "total_limit": 1000,
            "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
            "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
            "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                       "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
        }},
    ))

    # Farmer
    get_farmer_repo().create(FarmerProfile(
        id="farmer-bank-test", user_id="user-bt", real_name="測試小農",
    ))
    get_farm_repo().create(Farm(
        id="farm-bank-test", farmer_id="farmer-bank-test", name="測試農場",
    ))

    # Document + Record
    get_document_repo().create(Document(
        id="doc-bt", farmer_id="farmer-bank-test", filename="test.pdf",
        domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V2,
        status=DocumentStatus.VERIFIED,
    ))
    get_standardized_record_repo().create(StandardizedRecord(
        id="rec-bt", document_id="doc-bt", farmer_id="farmer-bank-test",
        domain=DataDomain.CERTIFICATION, record_type="test",
        source_level=SourceLevel.V2, data={"認證機構": "Test", "有效期限": "2030-01-01"},
    ))

    # Authorization
    get_authorization_repo().create(Authorization(
        id="auth-bt", farmer_id="farmer-bank-test", institution_id="bank-test",
        purpose="Test loan", data_scope=["IDENTITY", "CERTIFICATION"],
        start_at=_past(), expire_at=_future(),
        status=AuthorizationStatus.ACTIVE,
    ))


class TestBankCaseList:
    """Test GET /api/bank/{id}/cases."""

    def test_returns_authorized_cases(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/bank-test/cases")
        assert response.status_code == 200
        data = response.json()
        assert data["case_count"] == 1
        assert data["cases"][0]["farmer_name"] == "測試小農"

    def test_empty_for_unknown_bank(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/unknown-bank/cases")
        assert response.status_code == 200
        assert response.json()["case_count"] == 0


class TestBankCaseDetail:
    """Test GET /api/bank/{id}/cases/{farmer_id}."""

    def test_authorized_gets_full_detail(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/bank-test/cases/farmer-bank-test")
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["real_name"] == "測試小農"
        assert "experience" in data
        assert "indicators" in data
        assert "data_health" in data
        assert "anomalies" in data
        assert "disclaimer" in data

    def test_unauthorized_gets_403(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/unauthorized-bank/cases/farmer-bank-test")
        assert response.status_code == 403


class TestBankEvidence:
    """Test GET /api/bank/{id}/cases/{farmer_id}/evidence."""

    def test_authorized_gets_evidence(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/bank-test/cases/farmer-bank-test/evidence")
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] == 1
        assert data["record_count"] == 1
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["document"]["filename"] == "test.pdf"

    def test_unauthorized_gets_403(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/other-bank/cases/farmer-bank-test/evidence")
        assert response.status_code == 403


class TestBankTrace:
    """Test GET /api/bank/{id}/cases/{farmer_id}/trace/{record_id}."""

    def test_trace_record(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/bank-test/cases/farmer-bank-test/trace/rec-bt")
        assert response.status_code == 200
        data = response.json()
        assert data["trace"]["record"]["id"] == "rec-bt"
        assert data["trace"]["document"]["filename"] == "test.pdf"
        assert "lineage" in data

    def test_trace_nonexistent_record_404(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/bank-test/cases/farmer-bank-test/trace/no-such-rec")
        assert response.status_code == 404

    def test_trace_unauthorized_403(self, client, test_data_dir):
        _seed_bank_scenario()
        response = client.get("/api/bank/bad-bank/cases/farmer-bank-test/trace/rec-bt")
        assert response.status_code == 403
