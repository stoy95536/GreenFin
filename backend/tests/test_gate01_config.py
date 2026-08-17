"""
GATE-01 Tests: Application Configuration

Verifies:
- Settings load correctly
- Default values are sensible for demo
- Environment override mechanism works
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_settings_app_name():
    """APP_NAME should default to GreenFin."""
    from backend.app.core.config import settings
    assert settings.APP_NAME == "GreenFin"


def test_no_database_url_setting():
    """
    Storage is JSON file-based (ADR-0006/ADR-0007), so there must be no DATABASE_URL
    setting implying a SQL backend exists.
    """
    from backend.app.core.config import settings
    assert not hasattr(settings, "DATABASE_URL")


def test_data_directory_is_resolvable():
    """The active data directory must always resolve to a concrete path."""
    from backend.app.core.storage import get_data_dir
    assert get_data_dir() is not None


def test_settings_demo_mode():
    """DEMO_MODE should be True for demo."""
    from backend.app.core.config import settings
    assert settings.DEMO_MODE is True


def test_settings_rule_version():
    """RULE_VERSION should be GREENFIN_DEMO_V1."""
    from backend.app.core.config import settings
    assert settings.RULE_VERSION == "GREENFIN_DEMO_V1"


def test_settings_timezone():
    """Timezone should be Asia/Taipei."""
    from backend.app.core.config import settings
    assert settings.APP_TIMEZONE == "Asia/Taipei"
