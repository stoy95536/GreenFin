"""
Shared test fixtures for GreenFin backend tests.

Test isolation contract:
  Every test runs against a temporary data directory. The override goes through
  core.storage.set_data_dir(), which the repository layer consults lazily on every
  access. This replaced an earlier monkeypatch of a module global, which was a no-op
  because the directory had been bound as a default argument at import time — the
  entire suite was writing into the real backend/data/ and wiping demo seed data.

  See backend/tests/test_regression_data_isolation.py for the guard tests.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.core.storage import set_data_dir  # noqa: E402


@pytest.fixture(scope="session")
def _session_data_dir(tmp_path_factory):
    """Create one temporary data directory for the whole test session."""
    return tmp_path_factory.mktemp("greenfin_test_data")


@pytest.fixture(autouse=True)
def test_data_dir(_session_data_dir):
    """
    Point the storage layer at the temporary directory for every test.

    autouse so no test can accidentally run against production data.
    Restores production on teardown.
    """
    set_data_dir(_session_data_dir)
    yield _session_data_dir
    set_data_dir(None)


@pytest.fixture()
def client(test_data_dir):
    """FastAPI test client bound to the isolated data directory."""
    from backend.app.main import app

    with TestClient(app) as c:
        yield c
