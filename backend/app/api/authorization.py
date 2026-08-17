"""
Authorization API Endpoints.

Handles:
- POST /api/authorizations/grant — farmer grants bank access
- GET /api/farmers/{id}/authorizations — farmer's granted authorizations
- GET /api/banks/{id}/authorizations — bank's received authorizations
- POST /api/authorizations/{id}/revoke — revoke authorization
- GET /api/authorizations/{id}/check — check if authorization is valid
- GET /api/bank/{institution_id}/farmers/{farmer_id}/access — bank checks own access
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.authorization.service import (
    AuthorizationError,
    check_authorization,
    get_farmer_authorizations,
    get_institution_authorizations,
    grant_authorization,
    revoke_authorization,
)
from backend.app.services.authorization.guard import require_bank_authorization

router = APIRouter(tags=["authorization"])


class GrantRequest(BaseModel):
    """Request to grant authorization."""
    farmer_id: str
    institution_id: str
    purpose: str
    data_scope: list[str]
    start_at: str
    expire_at: str


@router.post("/authorizations/grant")
def api_grant_authorization(request: GrantRequest):
    """
    Farmer grants authorization for a bank to access their data.

    Per AGENTS.md §17: authorization includes institution, purpose, scope, start, expiry.
    """
    try:
        auth = grant_authorization(
            farmer_id=request.farmer_id,
            institution_id=request.institution_id,
            purpose=request.purpose,
            data_scope=request.data_scope,
            start_at=request.start_at,
            expire_at=request.expire_at,
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "authorization": auth.model_dump(),
        "message": "授權已建立",
    }


@router.post("/authorizations/{authorization_id}/revoke")
def api_revoke_authorization(authorization_id: str):
    """
    Revoke an existing authorization.

    After revocation, bank can no longer access farmer data.
    """
    try:
        auth = revoke_authorization(authorization_id)
    except AuthorizationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "authorization": auth.model_dump(),
        "message": "授權已撤回",
    }


@router.get("/farmers/{farmer_id}/authorizations")
def api_get_farmer_authorizations(farmer_id: str):
    """Get all authorizations granted by a farmer."""
    auths = get_farmer_authorizations(farmer_id)
    return {
        "farmer_id": farmer_id,
        "count": len(auths),
        "authorizations": [a.model_dump() for a in auths],
    }


@router.get("/banks/{institution_id}/authorizations")
def api_get_bank_authorizations(institution_id: str):
    """Get all authorizations received by a bank."""
    auths = get_institution_authorizations(institution_id)
    return {
        "institution_id": institution_id,
        "count": len(auths),
        "authorizations": [a.model_dump() for a in auths],
    }


class AccessCheckRequest(BaseModel):
    """Check if bank has access to farmer data."""
    institution_id: str
    farmer_id: str
    required_scope: Optional[str] = None


@router.post("/authorizations/check")
def api_check_authorization(request: AccessCheckRequest):
    """
    Check if a bank has valid authorization to access a farmer's data.

    Returns the authorization details if valid, or denied status.
    """
    auth = check_authorization(
        farmer_id=request.farmer_id,
        institution_id=request.institution_id,
        required_scope=request.required_scope,
    )

    if auth:
        return {
            "authorized": True,
            "authorization": auth.model_dump(),
        }
    else:
        return {
            "authorized": False,
            "message": "無有效授權",
        }


@router.get("/bank/{institution_id}/farmer/{farmer_id}/data")
def api_bank_access_farmer_data(institution_id: str, farmer_id: str):
    """
    Bank endpoint to access farmer data — enforced by authorization guard.

    This demonstrates the access control: only authorized banks can see data.
    """
    # Enforce authorization
    require_bank_authorization(farmer_id, institution_id)

    # If we get here, access is authorized — return summary
    from backend.app.services.experience.calculate import get_farmer_experience_summary
    from backend.app.services.indicators.calculate import get_farmer_indicators
    from backend.app.services.data_health.calculate import get_farmer_data_health

    experience = get_farmer_experience_summary(farmer_id)
    indicators = get_farmer_indicators(farmer_id)
    data_health = get_farmer_data_health(farmer_id)

    return {
        "authorized": True,
        "farmer_id": farmer_id,
        "institution_id": institution_id,
        "experience": experience,
        "indicators": [i.model_dump() for i in indicators],
        "data_health": [d.model_dump() for d in data_health],
        "note": "此為授信補充資訊，最終授信仍由金融機構依內部政策完成判斷",
    }
