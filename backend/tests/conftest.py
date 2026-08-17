"""
Shared test fixtures for GreenFin backend tests.

Uses a temporary data directory for test isolation.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary data directory for all tests in this session."""
    data_dir = tmp_path_factory.mktemp("greenfin_test_data")
    return data_dir


@pytest.fixture(autouse=True)
def patch_data_dir(test_data_dir, monkeypatch):
    """Patch DATA_DIR to use temporary directory for test isolation."""
    import backend.app.repositories.json_repository as repo_module
    import backend.app.repositories as repos_init
    monkeypatch.setattr(repo_module, "DATA_DIR", test_data_dir)
    monkeypatch.setattr(repos_init, "DATA_DIR", test_data_dir)


@pytest.fixture()
def client(test_data_dir, monkeypatch):
    """Provide a FastAPI test client with patched data directory."""
    import backend.app.repositories.json_repository as repo_module
    import backend.app.repositories as repos_init
    monkeypatch.setattr(repo_module, "DATA_DIR", test_data_dir)
    monkeypatch.setattr(repos_init, "DATA_DIR", test_data_dir)

    from backend.app.main import app
    with TestClient(app) as c:
        yield c
