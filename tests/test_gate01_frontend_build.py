"""
GATE-01 Tests: Frontend Build Verification

Verifies:
- package.json exists and is valid JSON
- Required source files exist
- dist/ directory was produced by vite build
- dist/index.html exists
"""

import json
from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parents[1] / "frontend"


def test_package_json_exists():
    """frontend/package.json must exist."""
    assert (FRONTEND_ROOT / "package.json").exists()


def test_package_json_is_valid():
    """frontend/package.json must be valid JSON with name field."""
    pkg = json.loads((FRONTEND_ROOT / "package.json").read_text(encoding="utf-8"))
    assert pkg["name"] == "greenfin-frontend"
    assert "build" in pkg.get("scripts", {})


def test_source_files_exist():
    """Key source files must exist."""
    required = [
        "src/main.tsx",
        "src/App.tsx",
        "src/index.css",
        "index.html",
        "vite.config.ts",
        "tsconfig.json",
        "tailwind.config.js",
    ]
    for f in required:
        assert (FRONTEND_ROOT / f).exists(), f"Missing: {f}"


def test_dist_directory_exists():
    """dist/ should exist after build."""
    assert (FRONTEND_ROOT / "dist").is_dir()


def test_dist_index_html_exists():
    """dist/index.html should exist after build."""
    index = FRONTEND_ROOT / "dist" / "index.html"
    assert index.exists()
    content = index.read_text(encoding="utf-8")
    assert "GreenFin" in content


def test_dist_has_assets():
    """dist/assets/ should contain bundled JS/CSS."""
    assets = FRONTEND_ROOT / "dist" / "assets"
    assert assets.is_dir()
    files = list(assets.iterdir())
    assert len(files) > 0
