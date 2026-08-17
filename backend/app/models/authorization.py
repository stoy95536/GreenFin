"""
Authorization, BankCase, and RuleSet models.

Authorization per AGENTS.md §17, RuleSet per §8.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import AuthorizationStatus


class RuleSet(EntityBase):
    """A versioned rule set used for calculations."""

    version: str = Field(..., description="Rule version identifier (e.g. GREENFIN_DEMO_V1)")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(default=None, description="What this rule set covers")
    config: dict = Field(default_factory=dict, description="Rule configuration data")
    is_active: bool = Field(default=True, description="Whether this is the current active version")


class Authorization(EntityBase):
    """Farmer's authorization for a bank to access data. Per AGENTS.md §17."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    institution_id: str = Field(..., description="Reference to BankInstitution.id")
    purpose: str = Field(..., description="Purpose of authorization")
    data_scope: list[str] = Field(default_factory=list, description="Data domains authorized")
    start_at: str = Field(..., description="Authorization start (ISO 8601)")
    expire_at: str = Field(..., description="Authorization expiry (ISO 8601)")
    status: AuthorizationStatus = Field(default=AuthorizationStatus.ACTIVE)
    revoked_at: Optional[str] = Field(default=None, description="Revocation timestamp if revoked")


class BankCase(EntityBase):
    """A bank's view of a farmer case, enabled by authorization."""

    authorization_id: str = Field(..., description="Reference to Authorization.id")
    institution_id: str = Field(..., description="Reference to BankInstitution.id")
    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    case_number: Optional[str] = Field(default=None, description="Bank internal case number")
    status: str = Field(default="open", description="Case status: open, reviewing, closed")
    notes: Optional[str] = Field(default=None, description="Bank reviewer notes")
