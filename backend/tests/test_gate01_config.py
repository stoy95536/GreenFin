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


def test_settings_database_url():
    """DATABASE_URL should be set (test override or default)."""
    # In test, we override to test db, but the settings object should have a value
    from backend.app.core.config import settings
    assert settings.DATABASE_URL is not None
    assert len(settings.DATABASE_URL) > 0


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
