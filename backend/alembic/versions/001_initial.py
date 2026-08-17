"""Initial migration — empty schema baseline.

Revision ID: 001
Revises: None
Create Date: 2026-08-17

GATE-01: Establishes migration framework. No tables yet (GATE-02 adds models).
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """GATE-01: baseline — no tables to create yet."""
    pass


def downgrade() -> None:
    """GATE-01: baseline — nothing to remove."""
    pass
