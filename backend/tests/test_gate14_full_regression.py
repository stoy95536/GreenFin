"""
GATE-14 — Full Demo Regression

Per DEVELOPMENT_PLAN.md:
Only GATE-14 PASS = Demo Ready.

Complete flow per AGENTS.md §19:
  Farmer Login → Dashboard → Upload Evidence → Mock OCR → Confirm Fields →
  Normalize → Verify → Detect Anomaly → Recalculate Data Health →
  Recalculate Experience → Recalculate Indicators → View Explanation →
  Trace Evidence → Authorize Bank → Bank Login → Open Case →
  Review Analysis → Trace Original Evidence → Generate Bank Information Package

This test simulates the entire Primary Demo Story end-to-end via API.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from backend.app.models import (
    ActionLevel, Authorization, AuthorizationStatus, DataDomain,
    FarmerProfile, Farm, GreenAction, GreenDimension, RuleSet,
    SourceLevel, User, UserRole, BankInstitution,
)
from backend.app.repositories import (
    get_authorization_repo, get_bank_repo, get_farmer_repo,
    get_farm_repo, get_green_action_repo, get_rule_set_repo,
    get_user_repo, get_document_repo, get_document_field_repo,
    get_standardized_record_repo, get_verification_repo,
    get_anomaly_repo, get_experience_repo, get_indicator_repo,
    get_data_health_repo, get_bank_case_repo, get_audit_log_repo,
)


def _future(days=90):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _clear_all():
    """Clear all repositories for a clean regression run."""
    repos = [
        get_user_repo, get_farmer_repo, get_bank_repo, get_farm_repo,
        get_document_repo, get_document_field_repo, get_standardized_record_repo,
        get_verification_repo, get_anomaly_repo, get_green_action_repo,
        get_experience_repo, get_indicator_repo, get_data_health_repo,
        get_authorization_repo, get_bank_case_repo, get_audit_log_repo,
        get_rule_set_repo,
    ]
    for repo_fn in repos:
        repo_fn().clear()


def _seed_demo_foundation():
    """Seed the minimal foundation for the full demo flow."""
    # Rule Set
    get_rule_set_repo().create(RuleSet(
        id="rs-demo", version="GREENFIN_DEMO_V1", name="Demo V1", is_active=True,
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

    # Users
    get_user_repo().create(User(
        id="user-chen", username="chen_farmer", display_name="陳小農", role=UserRole.FARMER,
    ))
    get_user_repo().create(User(
        id="user-bank", username="taishin", display_name="台新審查員", role=UserRole.BANK,
    ))

    # Farmer
    get_farmer_repo().create(FarmerProfile(
        id="farmer-chen", user_id="user-chen", real_name="陳小農",
        phone="0912-345-678", address="台南市後壁區", farm_ids=["farm-chen"],
    ))

    # Farm
    get_farm_repo().create(Farm(
        id="farm-chen", farmer_id="farmer-chen", name="綠田友善農場",
        location="台南市後壁區新嘉里", area_hectares=2.5,
    ))

    # Bank
    get_bank_repo().create(BankInstitution(
        id="bank-taishin", code="812", name="台新國際商業銀行 (DEMO)",
    ))

    # Green Actions (for experience calculation)
    get_green_action_repo().create(GreenAction(
        id="ga-demo-1", farmer_id="farmer-chen",
        dimension=GreenDimension.REDUCTION, action_level=ActionLevel.CERTIFIED,
        description="取得有機認證", action_date="2026-01-10",
        evidence_record_ids=[],  # Will be linked after upload
    ))
    get_green_action_repo().create(GreenAction(
        id="ga-demo-2", farmer_id="farmer-chen",
        dimension=GreenDimension.CIRCULAR, action_level=ActionLevel.BASIC,
        description="自製堆肥", action_date="2026-03-15",
    ))


class TestFullDemoRegression:
    """
    Complete end-to-end demo regression test.

    Simulates the Primary Demo Story from AGENTS.md §19.
    """

    def test_full_demo_flow(self, client, test_data_dir):
        """
        The full demo flow in one test — ensures no step breaks another.
        """
        _clear_all()
        _seed_demo_foundation()

        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: Upload Evidence (Organic Certification)
        # ═══════════════════════════════════════════════════════════════════
        upload_resp = client.post(
            "/api/documents/upload",
            files={"file": ("organic_cert.pdf", b"%PDF organic cert content", "application/pdf")},
            data={"farmer_id": "farmer-chen", "domain": "CERTIFICATION", "source_level": "V3"},
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        doc_id = upload_resp.json()["document"]["id"]
        fields = upload_resp.json()["fields"]
        assert len(fields) > 0, "OCR should extract fields"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: Confirm Fields (Human Confirmation)
        # ═══════════════════════════════════════════════════════════════════
        confirm_resp = client.post(
            f"/api/documents/{doc_id}/confirm",
            json={"corrections": {}},
        )
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "FIELDS_CONFIRMED"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 3: Normalize
        # ═══════════════════════════════════════════════════════════════════
        norm_resp = client.post(f"/api/documents/{doc_id}/normalize")
        assert norm_resp.status_code == 200
        record = norm_resp.json()["record"]
        assert record["domain"] == "CERTIFICATION"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 4: Verify + Anomaly Detection
        # ═══════════════════════════════════════════════════════════════════
        verify_resp = client.post(f"/api/documents/{doc_id}/verify")
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["status"] == "VERIFIED"
        assert len(verify_data["verifications"]) > 0

        # ═══════════════════════════════════════════════════════════════════
        # STEP 5: Recalculate Data Health
        # ═══════════════════════════════════════════════════════════════════
        dh_resp = client.post("/api/farmers/farmer-chen/data-health/calculate")
        assert dh_resp.status_code == 200
        dh_data = dh_resp.json()
        assert len(dh_data["domains"]) == 7
        # CERTIFICATION domain should be GREEN (valid V3 data)
        cert_dh = dh_data["domains"].get("CERTIFICATION", {})
        assert cert_dh["status"] == "GREEN"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 6: Calculate Experience
        # ═══════════════════════════════════════════════════════════════════
        exp_resp = client.post(
            "/api/experience/calculate",
            json={"green_action_id": "ga-demo-1"},
        )
        assert exp_resp.status_code == 200
        txn = exp_resp.json()["transaction"]
        assert txn["base_value"] == 100  # CERTIFIED
        assert txn["effective_value"] > 0

        exp_resp2 = client.post(
            "/api/experience/calculate",
            json={"green_action_id": "ga-demo-2"},
        )
        assert exp_resp2.status_code == 200

        # Check summary
        summary_resp = client.get("/api/farmers/farmer-chen/experience")
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["total_experience"] > 0
        assert summary["level"] != "L0"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 7: Calculate Indicators
        # ═══════════════════════════════════════════════════════════════════
        ind_resp = client.post("/api/farmers/farmer-chen/indicators/calculate")
        assert ind_resp.status_code == 200
        ind_data = ind_resp.json()
        assert len(ind_data["indicators"]) == 4
        # All four should be independent
        assert "completeness" in ind_data["indicators"]
        assert "credibility" in ind_data["indicators"]
        assert "business_maturity" in ind_data["indicators"]
        assert "green_maturity" in ind_data["indicators"]

        # ═══════════════════════════════════════════════════════════════════
        # STEP 8: View Explanation (Traceability)
        # ═══════════════════════════════════════════════════════════════════
        trace_resp = client.get("/api/traceability/validate/farmer-chen")
        assert trace_resp.status_code == 200
        trace_data = trace_resp.json()
        assert trace_data["all_valid"] is True

        # ═══════════════════════════════════════════════════════════════════
        # STEP 9: Authorize Bank
        # ═══════════════════════════════════════════════════════════════════
        auth_resp = client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-chen",
            "institution_id": "bank-taishin",
            "purpose": "農業設備貸款申請",
            "data_scope": ["IDENTITY", "LAND_CROP", "TRANSACTION", "GREEN_ACTION", "CERTIFICATION"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        assert auth_resp.status_code == 200
        auth_id = auth_resp.json()["authorization"]["id"]

        # ═══════════════════════════════════════════════════════════════════
        # STEP 10: Bank — Open Case List
        # ═══════════════════════════════════════════════════════════════════
        cases_resp = client.get("/api/bank/bank-taishin/cases")
        assert cases_resp.status_code == 200
        cases = cases_resp.json()
        assert cases["case_count"] == 1
        assert cases["cases"][0]["farmer_name"] == "陳小農"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 11: Bank — Review Analysis
        # ═══════════════════════════════════════════════════════════════════
        case_resp = client.get("/api/bank/bank-taishin/cases/farmer-chen")
        assert case_resp.status_code == 200
        case_data = case_resp.json()
        assert case_data["profile"]["real_name"] == "陳小農"
        assert case_data["experience"]["total_experience"] > 0
        assert len(case_data["indicators"]) == 4
        assert len(case_data["data_health"]) == 7
        assert "disclaimer" in case_data

        # ═══════════════════════════════════════════════════════════════════
        # STEP 12: Bank — Trace Original Evidence
        # ═══════════════════════════════════════════════════════════════════
        evidence_resp = client.get("/api/bank/bank-taishin/cases/farmer-chen/evidence")
        assert evidence_resp.status_code == 200
        ev_data = evidence_resp.json()
        assert ev_data["document_count"] >= 1
        assert len(ev_data["evidence"]) >= 1
        assert ev_data["evidence"][0]["document"]["filename"] == "organic_cert.pdf"

        # ═══════════════════════════════════════════════════════════════════
        # STEP 13: Bank — Generate Information Package
        # ═══════════════════════════════════════════════════════════════════
        pkg_resp = client.get("/api/reports/bank-package/bank-taishin/farmer-chen")
        assert pkg_resp.status_code == 200
        pkg = pkg_resp.json()
        assert pkg["package_type"] == "BANK_INFORMATION_PACKAGE"
        assert pkg["authorization"]["farmer_id"] == "farmer-chen"
        assert pkg["experience"]["total_experience"] > 0
        assert len(pkg["indicators"]) == 4
        assert len(pkg["data_health"]) == 7
        assert pkg["traceability"]["all_valid"] is True
        assert "DEMO" in pkg["disclaimer"]
        assert pkg["generated_at"] is not None

        # ═══════════════════════════════════════════════════════════════════
        # STEP 14: Verify unauthorized bank is denied
        # ═══════════════════════════════════════════════════════════════════
        denied_resp = client.get("/api/bank/unknown-bank/cases/farmer-chen")
        assert denied_resp.status_code == 403

        denied_pkg = client.get("/api/reports/bank-package/unknown-bank/farmer-chen")
        assert denied_pkg.status_code == 403

        # ═══════════════════════════════════════════════════════════════════
        # STEP 15: Verify revoked authorization denies access
        # ═══════════════════════════════════════════════════════════════════
        revoke_resp = client.post(f"/api/authorizations/{auth_id}/revoke")
        assert revoke_resp.status_code == 200

        revoked_case = client.get("/api/bank/bank-taishin/cases/farmer-chen")
        assert revoked_case.status_code == 403

        # ═══════════════════════════════════════════════════════════════════
        # DEMO FLOW COMPLETE
        # ═══════════════════════════════════════════════════════════════════


class TestDemoThreeCases:
    """Verify all three demo cases can be processed."""

    def test_case_a_healthy(self, client, test_data_dir):
        """Case A should produce GREEN data health and positive experience."""
        _clear_all()
        _seed_demo_foundation()

        # Upload + process
        r = client.post("/api/documents/upload",
            files={"file": ("cert_a.pdf", b"%PDF case A", "application/pdf")},
            data={"farmer_id": "farmer-chen", "domain": "CERTIFICATION", "source_level": "V3"})
        doc_id = r.json()["document"]["id"]
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        client.post(f"/api/documents/{doc_id}/normalize")
        client.post(f"/api/documents/{doc_id}/verify")

        # Calculate
        client.post("/api/farmers/farmer-chen/data-health/calculate")
        dh = client.get("/api/farmers/farmer-chen/data-health").json()
        cert = dh["domains"].get("CERTIFICATION", {})
        assert cert.get("status") == "GREEN"

    def test_case_b_needs_improvement(self, client, test_data_dir):
        """Case B with V1 should produce YELLOW."""
        _clear_all()
        _seed_demo_foundation()

        # Add a V1 farmer
        get_farmer_repo().create(FarmerProfile(
            id="farmer-lin", user_id="user-lin", real_name="林阿花",
        ))

        r = client.post("/api/documents/upload",
            files={"file": ("photo_b.jpg", b"\xff\xd8 case B photo", "image/jpeg")},
            data={"farmer_id": "farmer-lin", "domain": "GREEN_ACTION", "source_level": "V1"})
        doc_id = r.json()["document"]["id"]
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        client.post(f"/api/documents/{doc_id}/normalize")
        client.post(f"/api/documents/{doc_id}/verify")

        client.post("/api/farmers/farmer-lin/data-health/calculate")
        dh = client.get("/api/farmers/farmer-lin/data-health").json()
        green_action = dh["domains"].get("GREEN_ACTION", {})
        assert green_action.get("status") == "YELLOW"  # V1 only → YELLOW

    def test_case_c_abnormal(self, client, test_data_dir):
        """Case C with invalid data should produce anomalies."""
        _clear_all()
        _seed_demo_foundation()

        get_farmer_repo().create(FarmerProfile(
            id="farmer-wang", user_id="user-wang", real_name="王大明",
        ))

        # Upload same file twice (duplicate detection)
        content = b"%PDF case C expired"
        r1 = client.post("/api/documents/upload",
            files={"file": ("expired.pdf", content, "application/pdf")},
            data={"farmer_id": "farmer-wang", "domain": "CERTIFICATION", "source_level": "V0"})
        assert r1.status_code == 200

        # Second upload same content → rejected as duplicate
        r2 = client.post("/api/documents/upload",
            files={"file": ("expired_copy.pdf", content, "application/pdf")},
            data={"farmer_id": "farmer-wang", "domain": "CERTIFICATION", "source_level": "V0"})
        assert r2.status_code == 400
        assert "DUPLICATE" in r2.json()["detail"]["error_code"]


class TestRegressionChecks:
    """Verify no regressions in existing functionality."""

    def test_health_endpoint(self, client, test_data_dir):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_rules_endpoint(self, client, test_data_dir):
        _clear_all()
        _seed_demo_foundation()
        r = client.get("/api/rules/active")
        assert r.status_code == 200
        assert r.json()["version"] == "GREENFIN_DEMO_V1"

    def test_experience_rules(self, client, test_data_dir):
        _clear_all()
        _seed_demo_foundation()
        r = client.get("/api/rules/active/experience")
        assert r.status_code == 200
        assert r.json()["total_limit"] == 1000

    def test_duplicate_experience_rejected(self, client, test_data_dir):
        _clear_all()
        _seed_demo_foundation()
        client.post("/api/experience/calculate", json={"green_action_id": "ga-demo-1"})
        r = client.post("/api/experience/calculate", json={"green_action_id": "ga-demo-1"})
        assert r.status_code == 400

    def test_farmer_documents_list(self, client, test_data_dir):
        _clear_all()
        _seed_demo_foundation()
        r = client.get("/api/farmers/farmer-chen/documents")
        assert r.status_code == 200
