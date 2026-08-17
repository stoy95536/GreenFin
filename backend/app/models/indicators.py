"""
IndicatorResult and DataHealthResult models.

Four Indicators per RULES.md §4, Data Health per RULES.md §5.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import DataDomain, DataHealthStatus


class IndicatorResult(EntityBase):
    """Result of one of the four analysis indicators."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    indicator_type: str = Field(
        ...,
        description="One of: completeness, credibility, business_maturity, green_maturity",
    )
    score: float = Field(..., ge=0, le=100, description="Indicator score (0-100)")
    level: str = Field(..., description="Level label (L1-L5)")
    details: dict = Field(default_factory=dict, description="Breakdown details")
    rule_version: str = Field(..., description="Rule version used")
    calculated_at: str = Field(..., description="Calculation timestamp")
    input_evidence_ids: list[str] = Field(default_factory=list, description="Evidence IDs used")
    calculation_trace: Optional[str] = Field(default=None, description="Explanation of calculation")


class DataHealthResult(EntityBase):
    """Data Health result for a specific domain. Per RULES.md §5."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    domain: DataDomain = Field(..., description="Data domain being assessed")
    status: DataHealthStatus = Field(..., description="GREEN/YELLOW/RED/GRAY")
    reasons: list[str] = Field(default_factory=list, description="Reasons for this status")
    actions: list[str] = Field(default_factory=list, description="Recommended actions")
    affected_evidence_ids: list[str] = Field(default_factory=list, description="Related evidence")
    rule_version: str = Field(..., description="Rule version used")
    calculated_at: str = Field(..., description="Calculation timestamp")
