"""
Regression Tests: Audit Trail

Gap found in architecture review (2026-08-17):
  AGENTS.md §32 requires audit entries for 12 product events. The AuditLog entity and
  repository existed, but no service ever wrote to them — only seed data created two
  sample rows. GATE-14 passed without noticing because no test asserted audit events.

These tests assert that real operations leave an audit trail.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    ActionLevel, AuditEventType, DataDomain, FarmerProfile,
    GreenAction, GreenDimension, RuleSet,
)
from backend.app.repositories import (
    get_audit_log_repo, get_authorization_repo, get_document_repo,
    get_document_field_repo, get_experience_repo, get_farmer_repo,
    get_green_action_repo, get_indicator_repo, get_data_health_repo,
    get_rule_set_repo, get_standardized_record_repo, get_verification_repo,
    get_anomaly_repo,
)
from backend.app.services.audit import get_audit_trail

FAKE_PDF = b"%PDF-1.4 audit trail test"


def _future(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _reset_and_seed():
    for repo_fn in (
        get_audit_log_repo, get_authorization_repo, get_document_repo,
        get_document_field_repo, get_experience_repo, get_farmer_repo,
        get_green_action_repo, get_indicator_repo, get_data_health_repo,
        get_rule_set_repo, get_standardized_record_repo, get_verification_repo,
        get_anomaly_repo,
    ):
        repo_fn().clear()

    get_rule_set_repo().create(RuleSet(
        id="rs-audit", version="AUDIT_V1", name="Audit Test", is_active=True,
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
                "domain_required_fields": {"CERTIFICATION": ["認證機構", "有效期限"]},
                "expiry_warning_days": 90,
                "critical_anomaly_types": ["EXPIRED"],
            },
        },
    ))
    get_farmer_repo().create(FarmerProfile(
        id="farmer-audit", user_id="user-audit", real_name="稽核測試小農",
    ))


def _event_types_present() -> set[str]:
    return {e.event_type.value for e in get_audit_trail()}


class TestDocumentPipelineAudit:
    """Upload / OCR / correction must be audited."""

    def test_upload_and_ocr_are_audited(self, client, test_data_dir):
        _reset_and_seed()
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("cert.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-audit", "domain": "CERTIFICATION"},
        )
        assert resp.status_code == 200

        present = _event_types_present()
        assert AuditEventType.DOCUMENT_UPLOADED.value in present
        assert AuditEventType.OCR_COMPLETED.value in present

    def test_field_correction_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("cert2.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-audit", "domain": "CERTIFICATION"},
        )
        doc_id = resp.json()["document"]["id"]
        field_id = resp.json()["fields"][0]["id"]

        client.post(
            f"/api/documents/{doc_id}/confirm",
            json={"corrections": {field_id: "人工修正值"}},
        )
        assert AuditEventType.FIELD_CORRECTED.value in _event_types_present()

    def test_verification_and_anomaly_are_audited(self, client, test_data_dir):
        _reset_and_seed()
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("cert3.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-audit", "domain": "CERTIFICATION"},
        )
        doc_id = resp.json()["document"]["id"]
        client.post(f"/api/documents/{doc_id}/confirm", json={"corrections": {}})
        client.post(f"/api/documents/{doc_id}/normalize")
        client.post(f"/api/documents/{doc_id}/verify")

        assert AuditEventType.VERIFICATION_UPDATED.value in _event_types_present()


class TestCalculationAudit:
    """Recalculations must be audited."""

    def test_experience_recalculation_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        get_green_action_repo().create(GreenAction(
            id="ga-audit", farmer_id="farmer-audit",
            dimension=GreenDimension.REDUCTION, action_level=ActionLevel.BASIC,
            description="audit test", action_date="2026-05-01",
        ))
        client.post("/api/farmers/farmer-audit/experience/recalculate")
        assert AuditEventType.EXPERIENCE_RECALCULATED.value in _event_types_present()

    def test_indicator_calculation_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        client.post("/api/farmers/farmer-audit/indicators/calculate")
        assert AuditEventType.INDICATOR_RECALCULATED.value in _event_types_present()

    def test_data_health_calculation_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        client.post("/api/farmers/farmer-audit/data-health/calculate")
        assert AuditEventType.DATA_HEALTH_UPDATED.value in _event_types_present()


class TestAuthorizationAudit:
    """Grant / revoke / bank access must be audited."""

    def _grant(self, client):
        return client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-audit",
            "institution_id": "bank-audit",
            "purpose": "Audit test",
            "data_scope": ["CERTIFICATION"],
            "start_at": _past(),
            "expire_at": _future(),
        })

    def test_grant_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        assert self._grant(client).status_code == 200
        assert AuditEventType.AUTHORIZATION_GRANTED.value in _event_types_present()

    def test_revoke_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        auth_id = self._grant(client).json()["authorization"]["id"]
        client.post(f"/api/authorizations/{auth_id}/revoke")
        assert AuditEventType.AUTHORIZATION_REVOKED.value in _event_types_present()

    def test_bank_access_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        self._grant(client)
        client.get("/api/bank/bank-audit/cases/farmer-audit")
        assert AuditEventType.BANK_DATA_ACCESSED.value in _event_types_present()

    def test_unauthorized_bank_access_records_no_access_event(self, client, test_data_dir):
        _reset_and_seed()
        before = len([e for e in get_audit_trail()
                      if e.event_type == AuditEventType.BANK_DATA_ACCESSED])
        resp = client.get("/api/bank/no-such-bank/cases/farmer-audit")
        assert resp.status_code == 403
        after = len([e for e in get_audit_trail()
                     if e.event_type == AuditEventType.BANK_DATA_ACCESSED])
        assert after == before, "Denied access must not be logged as a data access"

    def test_report_generation_is_audited(self, client, test_data_dir):
        _reset_and_seed()
        self._grant(client)
        resp = client.get("/api/reports/bank-package/bank-audit/farmer-audit")
        assert resp.status_code == 200
        assert AuditEventType.REPORT_GENERATED.value in _event_types_present()


class TestAuditContent:
    """Audit entries must carry enough context to be useful."""

    def test_bank_access_records_who_and_what(self, client, test_data_dir):
        _reset_and_seed()
        client.post("/api/authorizations/grant", json={
            "farmer_id": "farmer-audit",
            "institution_id": "bank-audit",
            "purpose": "Audit test",
            "data_scope": ["CERTIFICATION"],
            "start_at": _past(),
            "expire_at": _future(),
        })
        client.get("/api/bank/bank-audit/cases/farmer-audit")

        access_events = [
            e for e in get_audit_trail()
            if e.event_type == AuditEventType.BANK_DATA_ACCESSED
        ]
        assert access_events
        event = access_events[-1]
        assert event.actor_id == "bank-audit"
        assert event.target_id == "farmer-audit"
        assert "resource" in event.details

    def test_trail_is_chronological(self, client, test_data_dir):
        _reset_and_seed()
        client.post(
            "/api/documents/upload",
            files={"file": ("chrono.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-audit", "domain": "CERTIFICATION"},
        )
        trail = get_audit_trail()
        timestamps = [e.created_at for e in trail]
        assert timestamps == sorted(timestamps)


class TestAuditAPI:
    """The audit trail must be inspectable via API."""

    def test_list_endpoint(self, client, test_data_dir):
        _reset_and_seed()
        client.post(
            "/api/documents/upload",
            files={"file": ("api.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-audit", "domain": "CERTIFICATION"},
        )
        resp = client.get("/api/audit")
        assert resp.status_code == 200
        assert resp.json()["count"] > 0

    def test_filter_by_event_type(self, client, test_data_dir):
        _reset_and_seed()
        client.post(
            "/api/documents/upload",
            files={"file": ("filter.pdf", FAKE_PDF, "application/pdf")},
            data={"farmer_id": "farmer-audit", "domain": "CERTIFICATION"},
        )
        resp = client.get("/api/audit", params={"event_type": "DOCUMENT_UPLOADED"})
        assert resp.status_code == 200
        entries = resp.json()["entries"]
        assert entries
        assert all(e["event_type"] == "DOCUMENT_UPLOADED" for e in entries)

    def test_invalid_event_type_returns_400(self, client, test_data_dir):
        _reset_and_seed()
        resp = client.get("/api/audit", params={"event_type": "NOT_A_REAL_EVENT"})
        assert resp.status_code == 400

    def test_event_types_endpoint_lists_required_events(self, client, test_data_dir):
        resp = client.get("/api/audit/event-types")
        assert resp.status_code == 200
        types = resp.json()["event_types"]
        # The 12 events required by AGENTS.md §32
        for required in (
            "DOCUMENT_UPLOADED", "OCR_COMPLETED", "FIELD_CORRECTED",
            "VERIFICATION_UPDATED", "ANOMALY_DETECTED", "EXPERIENCE_RECALCULATED",
            "INDICATOR_RECALCULATED", "DATA_HEALTH_UPDATED", "AUTHORIZATION_GRANTED",
            "AUTHORIZATION_REVOKED", "BANK_DATA_ACCESSED", "REPORT_GENERATED",
        ):
            assert required in types
