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


def test_json_file_created_on_first_write(test_data_dir):
    """
    Repository creates its JSON file on first write, not on construction.

    Construction is intentionally side-effect free so that resolving a repository
    never touches the filesystem (and never creates files in the wrong directory).
    """
    repo = get_user_repo()
    repo.clear()
    assert repo.file_path.exists()


def test_reads_work_before_file_exists(test_data_dir):
    """Reading a repository whose file does not exist yet returns empty, not an error."""
    repo = get_user_repo()
    if repo.file_path.exists():
        repo.file_path.unlink()
    assert repo.get_all() == []
    assert repo.count() == 0


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
