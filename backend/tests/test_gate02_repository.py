"""
GATE-02 Tests: JSON Repository CRUD Operations

Verifies:
- Create, read, update, delete
- Duplicate ID prevention
- find_by queries
- Relationship consistency (IDs reference existing entities)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import User, UserRole, FarmerProfile, Farm, Document, DataDomain
from backend.app.repositories import get_user_repo, get_farmer_repo, get_farm_repo


class TestRepositoryCRUD:
    """Test basic CRUD operations."""

    def test_create_and_get_by_id(self):
        repo = get_user_repo()
        repo.clear()
        user = User(id="crud-1", username="alice", display_name="Alice", role=UserRole.FARMER)
        repo.create(user)
        result = repo.get_by_id("crud-1")
        assert result is not None
        assert result.username == "alice"
        repo.clear()

    def test_create_duplicate_id_raises(self):
        repo = get_user_repo()
        repo.clear()
        user = User(id="dup-1", username="a", display_name="A", role=UserRole.FARMER)
        repo.create(user)
        with pytest.raises(ValueError, match="already exists"):
            repo.create(user)
        repo.clear()

    def test_get_by_id_not_found(self):
        repo = get_user_repo()
        repo.clear()
        assert repo.get_by_id("nonexistent") is None

    def test_get_all(self):
        repo = get_user_repo()
        repo.clear()
        repo.create(User(id="all-1", username="a", display_name="A", role=UserRole.FARMER))
        repo.create(User(id="all-2", username="b", display_name="B", role=UserRole.BANK))
        results = repo.get_all()
        assert len(results) == 2
        repo.clear()

    def test_update(self):
        repo = get_user_repo()
        repo.clear()
        user = User(id="upd-1", username="old", display_name="Old", role=UserRole.FARMER)
        repo.create(user)
        user.username = "new"
        repo.update(user)
        result = repo.get_by_id("upd-1")
        assert result.username == "new"
        assert result.updated_at is not None
        repo.clear()

    def test_update_nonexistent_raises(self):
        repo = get_user_repo()
        repo.clear()
        user = User(id="ghost", username="x", display_name="X", role=UserRole.FARMER)
        with pytest.raises(ValueError, match="not found"):
            repo.update(user)

    def test_delete(self):
        repo = get_user_repo()
        repo.clear()
        user = User(id="del-1", username="delete_me", display_name="D", role=UserRole.FARMER)
        repo.create(user)
        assert repo.delete("del-1") is True
        assert repo.get_by_id("del-1") is None
        repo.clear()

    def test_delete_nonexistent(self):
        repo = get_user_repo()
        repo.clear()
        assert repo.delete("no-such-id") is False

    def test_exists(self):
        repo = get_user_repo()
        repo.clear()
        repo.create(User(id="ex-1", username="e", display_name="E", role=UserRole.FARMER))
        assert repo.exists("ex-1") is True
        assert repo.exists("ex-999") is False
        repo.clear()

    def test_count(self):
        repo = get_user_repo()
        repo.clear()
        assert repo.count() == 0
        repo.create(User(id="cnt-1", username="c1", display_name="C1", role=UserRole.FARMER))
        repo.create(User(id="cnt-2", username="c2", display_name="C2", role=UserRole.FARMER))
        assert repo.count() == 2
        repo.clear()


class TestRepositoryQuery:
    """Test find_by and find_one_by."""

    def test_find_by_single_field(self):
        repo = get_user_repo()
        repo.clear()
        repo.create(User(id="q1", username="farmer1", display_name="F1", role=UserRole.FARMER))
        repo.create(User(id="q2", username="banker1", display_name="B1", role=UserRole.BANK))
        repo.create(User(id="q3", username="farmer2", display_name="F2", role=UserRole.FARMER))

        farmers = repo.find_by(role="farmer")
        assert len(farmers) == 2
        repo.clear()

    def test_find_by_multiple_fields(self):
        repo = get_user_repo()
        repo.clear()
        repo.create(User(id="mf1", username="a", display_name="A", role=UserRole.FARMER, is_active=True))
        repo.create(User(id="mf2", username="b", display_name="B", role=UserRole.FARMER, is_active=False))

        active_farmers = repo.find_by(role="farmer", is_active=True)
        assert len(active_farmers) == 1
        assert active_farmers[0].id == "mf1"
        repo.clear()

    def test_find_one_by(self):
        repo = get_user_repo()
        repo.clear()
        repo.create(User(id="fo1", username="unique", display_name="U", role=UserRole.ADMIN))
        result = repo.find_one_by(username="unique")
        assert result is not None
        assert result.id == "fo1"
        repo.clear()

    def test_find_one_by_not_found(self):
        repo = get_user_repo()
        repo.clear()
        assert repo.find_one_by(username="nobody") is None


class TestRepositoryRelationships:
    """Test that ID references between entities are consistent."""

    def test_farmer_references_user(self):
        user_repo = get_user_repo()
        farmer_repo = get_farmer_repo()
        user_repo.clear()
        farmer_repo.clear()

        user = User(id="rel-u1", username="farmer_user", display_name="FU", role=UserRole.FARMER)
        user_repo.create(user)

        farmer = FarmerProfile(id="rel-f1", user_id="rel-u1", real_name="Test Farmer")
        farmer_repo.create(farmer)

        # Verify relationship
        loaded_farmer = farmer_repo.get_by_id("rel-f1")
        assert loaded_farmer is not None
        referenced_user = user_repo.get_by_id(loaded_farmer.user_id)
        assert referenced_user is not None
        assert referenced_user.username == "farmer_user"

        user_repo.clear()
        farmer_repo.clear()

    def test_farm_references_farmer(self):
        farmer_repo = get_farmer_repo()
        farm_repo = get_farm_repo()
        farmer_repo.clear()
        farm_repo.clear()

        farmer = FarmerProfile(id="rel-f2", user_id="u-x", real_name="Farm Owner")
        farmer_repo.create(farmer)

        farm = Farm(id="rel-farm1", farmer_id="rel-f2", name="Test Farm")
        farm_repo.create(farm)

        loaded_farm = farm_repo.get_by_id("rel-farm1")
        assert loaded_farm.farmer_id == "rel-f2"
        assert farmer_repo.exists(loaded_farm.farmer_id)

        farmer_repo.clear()
        farm_repo.clear()
