"""
Authorization Service.

Per AGENTS.md §17:
- Bank access must depend on explicit authorization
- Authorization includes: institution, purpose, data_scope, start_at, expire_at, status
- Expired or revoked → backend MUST deny bank access (not just frontend hide)

BANK can:
- View authorized cases
- View experience/indicators/data health
- View anomalies
- Trace evidence
- Generate bank information package

BANK cannot:
- Modify farmer evidence
- Modify GreenFin calculations
- Make lending decisions within GreenFin
"""

from datetime import datetime, timezone

from backend.app.models import Authorization, AuthorizationStatus
from backend.app.models.base import now_taipei
from backend.app.repositories import get_authorization_repo
from backend.app.services import audit


class AuthorizationError(Exception):
    """Authorization operation error."""
    pass


def grant_authorization(
    farmer_id: str,
    institution_id: str,
    purpose: str,
    data_scope: list[str],
    start_at: str,
    expire_at: str,
) -> Authorization:
    """
    Grant a new authorization from farmer to bank.

    Args:
        farmer_id: The farmer granting access.
        institution_id: The bank receiving access.
        purpose: Purpose of authorization.
        data_scope: List of data domain strings authorized.
        start_at: Start datetime (ISO 8601).
        expire_at: Expiry datetime (ISO 8601).

    Returns:
        Created Authorization entity.
    """
    auth_repo = get_authorization_repo()

    # Check for existing active authorization for same institution
    existing = auth_repo.find_by(
        farmer_id=farmer_id,
        institution_id=institution_id,
        status=AuthorizationStatus.ACTIVE.value,
    )
    if existing:
        raise AuthorizationError(
            f"此小農已有一筆對該機構的有效授權 (id: {existing[0].id})"
        )

    auth = Authorization(
        farmer_id=farmer_id,
        institution_id=institution_id,
        purpose=purpose,
        data_scope=data_scope,
        start_at=start_at,
        expire_at=expire_at,
        status=AuthorizationStatus.ACTIVE,
    )
    auth_repo.create(auth)

    audit.authorization_granted(
        authorization_id=auth.id,
        farmer_id=farmer_id,
        institution_id=institution_id,
        purpose=purpose,
        data_scope=data_scope,
    )

    return auth


def revoke_authorization(authorization_id: str) -> Authorization:
    """
    Revoke an existing authorization.

    Per AGENTS.md §17: revoked authorization → backend must deny access.
    """
    auth_repo = get_authorization_repo()
    auth = auth_repo.get_by_id(authorization_id)

    if not auth:
        raise AuthorizationError("授權紀錄不存在")

    if auth.status == AuthorizationStatus.REVOKED:
        raise AuthorizationError("此授權已被撤回")

    auth.status = AuthorizationStatus.REVOKED
    auth.revoked_at = now_taipei()
    auth_repo.update(auth)

    audit.authorization_revoked(
        authorization_id=auth.id,
        farmer_id=auth.farmer_id,
        institution_id=auth.institution_id,
    )

    return auth


def check_authorization(
    farmer_id: str,
    institution_id: str,
    required_scope: str | None = None,
) -> Authorization | None:
    """
    Check if a bank has valid (active + not expired) authorization for a farmer.

    Args:
        farmer_id: Farmer being accessed.
        institution_id: Bank attempting access.
        required_scope: Optional specific domain that must be in scope.

    Returns:
        The valid Authorization if access is granted, None otherwise.
    """
    auth_repo = get_authorization_repo()
    candidates = auth_repo.find_by(farmer_id=farmer_id, institution_id=institution_id)

    now = datetime.now(timezone.utc)

    for auth in candidates:
        # Must be active
        if auth.status != AuthorizationStatus.ACTIVE:
            continue

        # Must not be expired
        try:
            expire = datetime.fromisoformat(auth.expire_at)
            if expire.tzinfo is None:
                expire = expire.replace(tzinfo=timezone.utc)
            if expire < now:
                # Auto-expire
                auth.status = AuthorizationStatus.EXPIRED
                auth_repo.update(auth)
                continue
        except (ValueError, TypeError):
            continue

        # Must be within start time
        try:
            start = datetime.fromisoformat(auth.start_at)
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if start > now:
                continue
        except (ValueError, TypeError):
            pass

        # Check scope if required
        if required_scope and required_scope not in auth.data_scope:
            continue

        return auth

    return None


def get_farmer_authorizations(farmer_id: str) -> list[Authorization]:
    """Get all authorizations granted by a farmer."""
    auth_repo = get_authorization_repo()
    return auth_repo.find_by(farmer_id=farmer_id)


def get_institution_authorizations(institution_id: str) -> list[Authorization]:
    """Get all authorizations received by a bank."""
    auth_repo = get_authorization_repo()
    return auth_repo.find_by(institution_id=institution_id)
