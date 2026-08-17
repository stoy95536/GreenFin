"""
Bank Access Guard.

Per AGENTS.md §17:
- Backend MUST deny bank access when authorization is expired or revoked.
- Cannot rely on frontend hiding alone.

This module provides a reusable dependency for bank-facing endpoints.
"""

from fastapi import HTTPException

from backend.app.services.authorization.service import check_authorization


def require_bank_authorization(
    farmer_id: str,
    institution_id: str,
    required_scope: str | None = None,
) -> None:
    """
    Enforce bank authorization. Raises 403 if not authorized.

    Use this in any bank-facing endpoint before returning farmer data.

    Args:
        farmer_id: Farmer whose data is being accessed.
        institution_id: Bank attempting access.
        required_scope: Optional domain scope requirement.

    Raises:
        HTTPException 403 if not authorized.
    """
    auth = check_authorization(farmer_id, institution_id, required_scope)
    if auth is None:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "存取被拒絕：無有效授權或授權已過期/撤回",
                "farmer_id": farmer_id,
                "institution_id": institution_id,
                "required_scope": required_scope,
            },
        )
