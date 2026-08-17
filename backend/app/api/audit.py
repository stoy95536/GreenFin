"""
Audit Trail API Endpoints.

Per AGENTS.md §32 the audit trail must exist and be inspectable.
Exposing it lets a farmer answer "who accessed my data, and when?".
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.models import AuditEventType
from backend.app.services.audit import get_audit_trail

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def api_get_audit_log(
    target_id: Optional[str] = Query(default=None, description="Filter by target entity ID"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Get audit entries, newest last, optionally filtered.
    """
    parsed_event: Optional[AuditEventType] = None
    if event_type:
        try:
            parsed_event = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"無效的事件類型: {event_type}。有效值: {[e.value for e in AuditEventType]}",
            )

    entries = get_audit_trail(target_id=target_id, event_type=parsed_event)

    return {
        "count": len(entries),
        "returned": min(len(entries), limit),
        "entries": [e.model_dump() for e in entries[-limit:]],
    }


@router.get("/event-types")
def api_get_event_types():
    """List the audited event types required by AGENTS.md §32."""
    return {"event_types": [e.value for e in AuditEventType]}
