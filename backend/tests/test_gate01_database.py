"""
GATE-01 Tests: Data Storage (JSON Repository)

Verifies:
- Data directory can be created
- JSON files can be read/written
- Repository basic operations work
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.repositories import get_user_repo
from backend.app.models import User, UserRole


def test_data_directory_accessible(test_data_dir):
    """Data directory should exist and be writable."""
    assert test_data_dir.exists()
    assert test_data_dir.is_dir()


def test_json_file_creation(test_data_dir):
    """Repository should create JSON file on init."""
    repo = get_user_repo()
    # The file should exist after repo init
    assert repo.file_path.exists()


def test_repository_basic_write_read(test_data_dir):
    """Repository should write and read a record."""
    repo = get_user_repo()
    repo.clear()
    user = User(id="test-1", username="test", display_name="Test", role=UserRole.FARMER)
    repo.create(user)
    result = repo.get_by_id("test-1")
    assert result is not None
    assert result.username == "test"
    repo.clear()


def test_repository_count(test_data_dir):
    """Repository count should reflect stored records."""
    repo = get_user_repo()
    repo.clear()
    assert repo.count() == 0
    user = User(id="test-c", username="counter", display_name="C", role=UserRole.FARMER)
    repo.create(user)
    assert repo.count() == 1
    repo.clear()
