"""
Regression Tests: Test Data Isolation

Bug found in architecture review (2026-08-17):
  JsonRepository.__init__ bound DATA_DIR as a mutable default argument, which is
  evaluated at import time. conftest's monkeypatch of the module global was a
  no-op, so the entire test suite read and wrote the REAL backend/data/ directory,
  destroying demo seed data on every run.

Reproduced before fix:
  BEFORE tests -> ['GREENFIN_DEMO_V1']
  AFTER  tests -> ['V1', 'V2']

These tests must fail if that regression is ever reintroduced.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.core.storage import PRODUCTION_DATA_DIR, get_data_dir
from backend.app.repositories import get_rule_set_repo, get_user_repo


class TestDataDirIsolation:
    """The active data directory during tests must never be the production one."""

    def test_active_data_dir_is_not_production(self, test_data_dir):
        active = get_data_dir().resolve()
        production = PRODUCTION_DATA_DIR.resolve()
        assert active != production, (
            f"Tests are using the production data directory ({active}). "
            "Seed data would be destroyed."
        )

    def test_active_data_dir_is_the_fixture_dir(self, test_data_dir):
        assert get_data_dir().resolve() == Path(test_data_dir).resolve()

    def test_repository_file_path_is_outside_production(self, test_data_dir):
        repo = get_user_repo()
        production = PRODUCTION_DATA_DIR.resolve()
        assert production not in repo.file_path.resolve().parents, (
            f"Repository is writing into production: {repo.file_path}"
        )

    def test_no_default_argument_binding(self):
        """
        Root cause guard: data_dir must NOT be bound to a concrete path as a
        default argument, otherwise runtime overrides silently stop working.
        """
        from backend.app.repositories.json_repository import JsonRepository

        defaults = JsonRepository.__init__.__defaults__ or ()
        for value in defaults:
            assert not isinstance(value, Path), (
                "JsonRepository.__init__ has a Path bound as a default argument. "
                "This freezes the data directory at import time. Resolve it lazily."
            )


class TestWritesDoNotEscapeFixture:
    """Actual writes must land in the fixture directory, not production."""

    def test_write_lands_in_fixture_dir(self, test_data_dir):
        repo = get_rule_set_repo()
        repo.clear()
        assert repo.file_path.exists()
        assert Path(test_data_dir).resolve() in repo.file_path.resolve().parents

    def test_production_rule_sets_untouched(self, test_data_dir):
        """
        Writing during a test must not modify the production rule_sets.json.
        """
        production_file = PRODUCTION_DATA_DIR / "rule_sets.json"
        before = production_file.read_bytes() if production_file.exists() else None

        repo = get_rule_set_repo()
        repo.clear()

        after = production_file.read_bytes() if production_file.exists() else None
        assert before == after, "Production rule_sets.json was modified by a test"
