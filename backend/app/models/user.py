"""
User and FarmerProfile models.
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import UserRole


class User(EntityBase):
    """System user account."""

    username: str = Field(..., description="Login username")
    display_name: str = Field(..., description="Display name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(default=True, description="Account active status")


class FarmerProfile(EntityBase):
    """Farmer identity and settings, linked to a User."""

    user_id: str = Field(..., description="Reference to User.id")
    real_name: str = Field(..., description="Real name (e.g. 陳小農)")
    id_number_masked: Optional[str] = Field(default=None, description="Masked ID number")
    phone: Optional[str] = Field(default=None, description="Contact phone")
    address: Optional[str] = Field(default=None, description="Address")
    farm_ids: list[str] = Field(default_factory=list, description="List of Farm IDs owned")


class BankInstitution(EntityBase):
    """Financial institution."""

    code: str = Field(..., description="Institution code")
    name: str = Field(..., description="Institution name (e.g. 台新銀行)")
    contact_email: Optional[str] = Field(default=None, description="Contact email")
