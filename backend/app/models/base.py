"""
GreenFin Base Model.

Shared base class for all domain entities with common fields.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def generate_id() -> str:
    """Generate a unique ID for entities."""
    return str(uuid4())


def now_taipei() -> str:
    """Generate ISO 8601 timestamp in UTC (display as Asia/Taipei in frontend)."""
    return datetime.now(timezone.utc).isoformat()


class EntityBase(BaseModel):
    """Base class for all GreenFin entities."""

    id: str = Field(default_factory=generate_id, description="Unique entity ID")
    created_at: str = Field(default_factory=now_taipei, description="Creation timestamp (ISO 8601)")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = now_taipei()
