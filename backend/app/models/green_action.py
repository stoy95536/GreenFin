"""
GreenAction and ExperienceTransaction models.

Represents green activities and their experience value calculations.
Per RULES.md §3.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import ActionLevel, GreenDimension


class GreenAction(EntityBase):
    """A green action performed by a farmer, supported by evidence."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    dimension: GreenDimension = Field(..., description="Green dimension (減量/增匯/循環/綠色治理)")
    action_level: ActionLevel = Field(..., description="Action level (BASIC/SUSTAINED/CERTIFIED)")
    description: str = Field(..., description="Description of the green action")
    action_date: str = Field(..., description="Date the action occurred (ISO 8601)")
    evidence_record_ids: list[str] = Field(default_factory=list, description="Supporting StandardizedRecord IDs")
    is_active: bool = Field(default=True, description="Whether this action is currently valid")


class ExperienceTransaction(EntityBase):
    """A single experience value calculation record. Per RULES.md §3."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    green_action_id: str = Field(..., description="Reference to GreenAction.id")
    dimension: GreenDimension = Field(..., description="Green dimension")
    base_value: int = Field(..., description="Base experience value (20/50/100)")
    source_recognition_ratio: float = Field(..., ge=0.0, le=1.0, description="來源認列比例")
    effective_value: float = Field(..., description="= base_value × source_recognition_ratio")
    rule_version: str = Field(..., description="Rule version used for calculation")
    calculated_at: str = Field(..., description="Calculation timestamp")
    input_evidence_ids: list[str] = Field(default_factory=list, description="Evidence IDs used")
    calculation_trace: Optional[str] = Field(default=None, description="Explanation of calculation")
