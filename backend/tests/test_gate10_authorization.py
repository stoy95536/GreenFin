"""
GATE-10 Tests: Authorization

Security tests per AGENTS.md §17:
- authorized bank → allowed
- unauthorized bank → denied
- expired authorization → denied
- revoked authorization → denied
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import Authorization, AuthorizationStatus, RuleSet
from backend.app.repositories import get_authorization_repo, get_rule_set_repo
from backend.app.services.authorization.service import (
    AuthorizationError,
    check_authorization,
    get_farmer_authorizations,
    grant_authorization,
    revoke_authorization,
)
from backend.app.services.authorization.guard import require_bank_authorization
from fastapi import HTTPException


def _seed_rules():
    repo = get_rule_set_repo()
    repo.clear()
    repo.create(RuleSet(
        id="rs-auth", version="AUTH_V1", name="Auth Test", is_active=True,
        config={"experience": {
            "dimensions": ["減量", "增匯", "循環", "綠色治理"],
            "annual_limit_per_dimension": 250, "total_limit": 1000,
            "base_values": {"BASIC": 20, "SUSTAINED": 50, "CERTIFIED": 100},
            "source_ratios": {"V3": 1.0, "V2": 1.0, "V1": 0.5, "V0": 0.0},
            "levels": {"L0": [0, 0], "L1": [1, 200], "L2": [201, 400],
                       "L3": [401, 600], "L4": [601, 800], "L5": [801, 1000]},
        }},
    ))


def _clear():
    get_authorization_repo().clear()


def _future(days=30):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past(days=30):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _now():
    return datetime.now(timezone.utc).isoformat()


class TestGrantAuthorization:
    """Test granting authorization."""

    def test_grant_creates_authorization(self, test_data_dir):
        _clear()
        auth = grant_authorization(
            farmer_id="farmer-g", institution_id="bank-g",
            purpose="Loan", data_scope=["IDENTITY", "TRANSACTION"],
            start_at=_now(), expire_at=_future(),
        )
        assert auth.id is not None
        assert auth.status == AuthorizationStatus.ACTIVE

    def test_grant_duplicate_raises(self, test_data_dir):
        _clear()
        grant_authorization(
            farmer_id="farmer-dup", institution_id="bank-dup",
            purpose="Loan", data_scope=["IDENTITY"],
            start_at=_now(), expire_at=_future(),
        )
        with pytest.raises(AuthorizationError, match="已有"):
            grant_authorization(
                farmer_id="farmer-dup", institution_id="bank-dup",
                purpose="Another", data_scope=["TRANSACTION"],
                start_at=_now(), expire_at=_future(),
            )

    def test_grant_persists(self, test_data_dir):
        _clear()
        auth = grant_authorization(
            farmer_id="farmer-per", institution_id="bank-per",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_now(), expire_at=_future(),
        )
        repo = get_authorization_repo()
        loaded = repo.get_by_id(auth.id)
        assert loaded is not None
        assert loaded.farmer_id == "farmer-per"


class TestRevokeAuthorization:
    """Test revoking authorization."""

    def test_revoke_changes_status(self, test_data_dir):
        _clear()
        auth = grant_authorization(
            farmer_id="farmer-rev", institution_id="bank-rev",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_now(), expire_at=_future(),
        )
        revoked = revoke_authorization(auth.id)
        assert revoked.status == AuthorizationStatus.REVOKED
        assert revoked.revoked_at is not None

    def test_revoke_nonexistent_raises(self, test_data_dir):
        _clear()
        with pytest.raises(AuthorizationError, match="不存在"):
            revoke_authorization("nonexistent-id")

    def test_revoke_already_revoked_raises(self, test_data_dir):
        _clear()
        auth = grant_authorization(
            farmer_id="farmer-rr", institution_id="bank-rr",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_now(), expire_at=_future(),
        )
        revoke_authorization(auth.id)
        with pytest.raises(AuthorizationError, match="已被撤回"):
            revoke_authorization(auth.id)


class TestCheckAuthorization:
    """Test authorization checking logic."""

    def test_valid_authorization_returns_auth(self, test_data_dir):
        _clear()
        grant_authorization(
            farmer_id="farmer-chk", institution_id="bank-chk",
            purpose="Test", data_scope=["IDENTITY", "TRANSACTION"],
            start_at=_past(1), expire_at=_future(30),
        )
        result = check_authorization("farmer-chk", "bank-chk")
        assert result is not None
        assert result.status == AuthorizationStatus.ACTIVE

    def test_unauthorized_bank_returns_none(self, test_data_dir):
        _clear()
        result = check_authorization("farmer-x", "bank-unknown")
        assert result is None

    def test_expired_authorization_returns_none(self, test_data_dir):
        _clear()
        repo = get_authorization_repo()
        repo.create(Authorization(
            id="auth-expired", farmer_id="farmer-exp", institution_id="bank-exp",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_past(60), expire_at=_past(1),  # Already expired
            status=AuthorizationStatus.ACTIVE,
        ))
        result = check_authorization("farmer-exp", "bank-exp")
        assert result is None

    def test_revoked_authorization_returns_none(self, test_data_dir):
        _clear()
        auth = grant_authorization(
            farmer_id="farmer-rvk", institution_id="bank-rvk",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_past(1), expire_at=_future(30),
        )
        revoke_authorization(auth.id)
        result = check_authorization("farmer-rvk", "bank-rvk")
        assert result is None

    def test_scope_check_passes(self, test_data_dir):
        _clear()
        grant_authorization(
            farmer_id="farmer-scp", institution_id="bank-scp",
            purpose="Test", data_scope=["IDENTITY", "GREEN_ACTION"],
            start_at=_past(1), expire_at=_future(30),
        )
        result = check_authorization("farmer-scp", "bank-scp", required_scope="IDENTITY")
        assert result is not None

    def test_scope_check_fails(self, test_data_dir):
        _clear()
        grant_authorization(
            farmer_id="farmer-scf", institution_id="bank-scf",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_past(1), expire_at=_future(30),
        )
        result = check_authorization("farmer-scf", "bank-scf", required_scope="TRANSACTION")
        assert result is None


class TestBankAccessGuard:
    """Test the access guard raises 403 when unauthorized."""

    def test_authorized_passes(self, test_data_dir):
        _clear()
        grant_authorization(
            farmer_id="farmer-guard", institution_id="bank-guard",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_past(1), expire_at=_future(30),
        )
        # Should not raise
        require_bank_authorization("farmer-guard", "bank-guard")

    def test_unauthorized_raises_403(self, test_data_dir):
        _clear()
        with pytest.raises(HTTPException) as exc_info:
            require_bank_authorization("farmer-no", "bank-no")
        assert exc_info.value.status_code == 403

    def test_expired_raises_403(self, test_data_dir):
        _clear()
        repo = get_authorization_repo()
        repo.create(Authorization(
            id="auth-guard-exp", farmer_id="farmer-ge", institution_id="bank-ge",
            purpose="Test", data_scope=["IDENTITY"],
            start_at=_past(60), expire_at=_past(1),
            status=AuthorizationStatus.ACTIVE,
        ))
        with pytest.raises(HTTPException) as exc_info:
            require_bank_authorization("farmer-ge", "bank-ge")
        assert exc_info.value.status_code == 403
