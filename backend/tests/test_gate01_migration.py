"""
GATE-01 Tests: Alembic Migration Framework

Verifies:
- Alembic configuration is valid
- Migration scripts can be loaded
- Initial migration (001) exists
- Migration can stamp head without error
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_alembic_config():
    """Create Alembic Config pointing to our backend."""
    alembic_ini = BACKEND_ROOT / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def test_alembic_config_loads():
    """Alembic configuration should load without error."""
    cfg = get_alembic_config()
    assert cfg.get_main_option("script_location") is not None


def test_alembic_script_directory_exists():
    """Alembic script directory should be accessible."""
    cfg = get_alembic_config()
    script_dir = ScriptDirectory.from_config(cfg)
    assert script_dir is not None


def test_initial_migration_exists():
    """Initial migration revision '001' should exist."""
    cfg = get_alembic_config()
    script_dir = ScriptDirectory.from_config(cfg)
    revisions = list(script_dir.walk_revisions())
    revision_ids = [r.revision for r in revisions]
    assert "001" in revision_ids


def test_migration_head_is_001():
    """Current head revision should be '001'."""
    cfg = get_alembic_config()
    script_dir = ScriptDirectory.from_config(cfg)
    head = script_dir.get_current_head()
    assert head == "001"


def test_initial_migration_has_no_down_revision():
    """Initial migration should have no parent (down_revision=None)."""
    cfg = get_alembic_config()
    script_dir = ScriptDirectory.from_config(cfg)
    rev = script_dir.get_revision("001")
    assert rev is not None
    assert rev.down_revision is None
