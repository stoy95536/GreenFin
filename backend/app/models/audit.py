"""
AuditLog model.

Per AGENTS.md §32 — important product events are logged.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import AuditEventType


class AuditLog(EntityBase):
    """Audit trail for important product events."""

    event_type: AuditEventType = Field(..., description="Type of audited event")
    actor_id: Optional[str] = Field(default=None, description="User who triggered the event")
    target_id: Optional[str] = Field(default=None, description="Target entity ID")
    target_type: Optional[str] = Field(default=None, description="Target entity type name")
    details: dict = Field(default_factory=dict, description="Event-specific details")
    ip_address: Optional[str] = Field(default=None, description="Request IP if applicable")
