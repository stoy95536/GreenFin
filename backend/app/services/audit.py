"""
Audit Trail Service.

Per AGENTS.md §32, important product events must produce an AuditLog entry.
Previously the AuditLog entity and repository existed but nothing ever wrote to them —
only seed data created two sample rows — so the audit trail was declared but absent.

Design:
- One helper per event family, so call sites read declaratively.
- Recording is best-effort: an audit failure must never break the business operation
  it is describing. Failures are swallowed and surfaced via the returned value being
  None, because losing a document upload to protect a log line is the wrong trade.
- Timestamps come from EntityBase (created_at), so ordering is preserved without a
  separate field.
"""

from typing import Optional

from backend.app.models import AuditEventType, AuditLog
from backend.app.repositories import get_audit_log_repo


def record_event(
    event_type: AuditEventType,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    target_type: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Write an audit entry. Returns the entry, or None if recording failed.

    Never raises: audit recording must not break the operation being audited.
    """
    try:
        entry = AuditLog(
            event_type=event_type,
            actor_id=actor_id,
            target_id=target_id,
            target_type=target_type,
            details=details or {},
            ip_address=ip_address,
        )
        return get_audit_log_repo().create(entry)
    except Exception:
        return None


# ─── Document pipeline events ─────────────────────────────────────────────────


def document_uploaded(document_id: str, farmer_id: str, filename: str, domain: str):
    return record_event(
        AuditEventType.DOCUMENT_UPLOADED,
        actor_id=farmer_id,
        target_id=document_id,
        target_type="Document",
        details={"filename": filename, "domain": domain},
    )


def ocr_completed(document_id: str, farmer_id: str, field_count: int, provider: str):
    return record_event(
        AuditEventType.OCR_COMPLETED,
        actor_id=farmer_id,
        target_id=document_id,
        target_type="Document",
        details={"field_count": field_count, "provider": provider},
    )


def field_corrected(document_id: str, field_ids: list[str], actor_id: Optional[str] = None):
    return record_event(
        AuditEventType.FIELD_CORRECTED,
        actor_id=actor_id,
        target_id=document_id,
        target_type="Document",
        details={"corrected_field_ids": field_ids, "count": len(field_ids)},
    )


def verification_updated(record_id: str, source_level: str, reason: str):
    return record_event(
        AuditEventType.VERIFICATION_UPDATED,
        target_id=record_id,
        target_type="StandardizedRecord",
        details={"source_level": source_level, "reason": reason},
    )


def anomaly_detected(record_id: str, anomaly_type: str, severity: str, description: str):
    return record_event(
        AuditEventType.ANOMALY_DETECTED,
        target_id=record_id,
        target_type="StandardizedRecord",
        details={
            "anomaly_type": anomaly_type,
            "severity": severity,
            "description": description,
        },
    )


# ─── Calculation events ───────────────────────────────────────────────────────


def experience_recalculated(farmer_id: str, total: float, rule_version: str, transaction_count: int):
    return record_event(
        AuditEventType.EXPERIENCE_RECALCULATED,
        actor_id=farmer_id,
        target_id=farmer_id,
        target_type="FarmerProfile",
        details={
            "total_experience": total,
            "rule_version": rule_version,
            "transaction_count": transaction_count,
        },
    )


def indicator_recalculated(farmer_id: str, rule_version: str, scores: dict):
    return record_event(
        AuditEventType.INDICATOR_RECALCULATED,
        actor_id=farmer_id,
        target_id=farmer_id,
        target_type="FarmerProfile",
        details={"rule_version": rule_version, "scores": scores},
    )


def data_health_updated(farmer_id: str, rule_version: str, summary: dict):
    return record_event(
        AuditEventType.DATA_HEALTH_UPDATED,
        actor_id=farmer_id,
        target_id=farmer_id,
        target_type="FarmerProfile",
        details={"rule_version": rule_version, "status_summary": summary},
    )


# ─── Authorization & bank events ──────────────────────────────────────────────


def authorization_granted(authorization_id: str, farmer_id: str, institution_id: str, purpose: str, data_scope: list[str]):
    return record_event(
        AuditEventType.AUTHORIZATION_GRANTED,
        actor_id=farmer_id,
        target_id=authorization_id,
        target_type="Authorization",
        details={
            "institution_id": institution_id,
            "purpose": purpose,
            "data_scope": data_scope,
        },
    )


def authorization_revoked(authorization_id: str, farmer_id: str, institution_id: str):
    return record_event(
        AuditEventType.AUTHORIZATION_REVOKED,
        actor_id=farmer_id,
        target_id=authorization_id,
        target_type="Authorization",
        details={"institution_id": institution_id},
    )


def bank_data_accessed(institution_id: str, farmer_id: str, resource: str):
    """
    Record that a bank read farmer data.

    This is the event a farmer would ask about ("who looked at my data?"), so it
    records the accessing institution and exactly which resource was read.
    """
    return record_event(
        AuditEventType.BANK_DATA_ACCESSED,
        actor_id=institution_id,
        target_id=farmer_id,
        target_type="FarmerProfile",
        details={"resource": resource},
    )


def report_generated(institution_id: str, farmer_id: str, package_type: str):
    return record_event(
        AuditEventType.REPORT_GENERATED,
        actor_id=institution_id,
        target_id=farmer_id,
        target_type="FarmerProfile",
        details={"package_type": package_type},
    )


# ─── Query helpers ────────────────────────────────────────────────────────────


def get_audit_trail(target_id: Optional[str] = None, event_type: Optional[AuditEventType] = None) -> list[AuditLog]:
    """
    Retrieve audit entries, optionally filtered by target and/or event type.

    Returned oldest-first so the trail reads chronologically.
    """
    repo = get_audit_log_repo()

    criteria = {}
    if target_id is not None:
        criteria["target_id"] = target_id
    if event_type is not None:
        criteria["event_type"] = event_type.value

    entries = repo.find_by(**criteria) if criteria else repo.get_all()
    return sorted(entries, key=lambda e: e.created_at)
