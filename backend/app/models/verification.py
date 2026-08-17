"""
VerificationResult and Anomaly models.

Handles data quality checks per AGENTS.md §10 and §13.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import AnomalySeverity, AnomalyType, SourceLevel


class VerificationResult(EntityBase):
    """Result of source verification for a standardized record."""

    record_id: str = Field(..., description="Reference to StandardizedRecord.id")
    source_level: SourceLevel = Field(..., description="Determined source level V0-V3")
    reason: str = Field(..., description="Explanation of verification result")
    verified_by: str = Field(default="system", description="Who/what performed verification")
    evidence_ids: list[str] = Field(default_factory=list, description="Supporting evidence document IDs")


class Anomaly(EntityBase):
    """A detected anomaly on a standardized record."""

    record_id: str = Field(..., description="Reference to StandardizedRecord.id")
    document_id: Optional[str] = Field(default=None, description="Related Document.id")
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly")
    severity: AnomalySeverity = Field(default=AnomalySeverity.WARNING, description="Severity level")
    description: str = Field(..., description="Human-readable description")
    is_resolved: bool = Field(default=False, description="Whether anomaly has been resolved")
    resolved_by: Optional[str] = Field(default=None, description="Who resolved it")
    resolved_at: Optional[str] = Field(default=None, description="Resolution timestamp")
