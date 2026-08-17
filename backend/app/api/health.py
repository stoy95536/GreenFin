"""
Health check endpoint.

Verifies the application is running and the data storage is accessible.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.core.storage import get_data_dir
from backend.app.repositories import get_farmer_repo

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Returns application health status including data directory accessibility.
    """
    data_status = "connected"
    data_files = 0
    farmers_count = 0

    try:
        data_dir = get_data_dir()
        if not data_dir.exists():
            data_status = "error: data directory not found"
        else:
            data_files = len(list(data_dir.glob("*.json")))
            farmers_count = get_farmer_repo().count()
    except Exception as e:
        data_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "demo_mode": settings.DEMO_MODE,
        "rule_version": settings.RULE_VERSION,
        "database": data_status,
        "data_files": data_files,
        "farmers_count": farmers_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
