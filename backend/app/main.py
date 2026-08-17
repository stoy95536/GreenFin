"""
GreenFin Backend Application Entry Point.

FastAPI application with CORS, health endpoint, and lifecycle management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.documents import router as documents_router, farmer_router
from backend.app.api.verification import router as verification_router
from backend.app.api.rules import router as rules_router
from backend.app.api.experience import router as experience_router
from backend.app.api.indicators import router as indicators_router
from backend.app.api.data_health import router as data_health_router
from backend.app.api.authorization import router as authorization_router
from backend.app.api.bank import router as bank_router
from backend.app.api.traceability import router as traceability_router
from backend.app.api.reports import router as reports_router
from backend.app.api.audit import router as audit_router
from backend.app.api.auth import router as auth_router
from backend.app.api.green_actions import router as green_actions_router
from backend.app.core.config import settings
from backend.app.core.storage import get_data_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Startup: ensure the active data directory exists
    get_data_dir().mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: nothing to clean up for JSON storage


app = FastAPI(
    title=settings.APP_NAME,
    description="綠色履歷資料治理與授信補充資訊平台 — Demo API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(farmer_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(experience_router, prefix="/api")
app.include_router(indicators_router, prefix="/api")
app.include_router(data_health_router, prefix="/api")
app.include_router(authorization_router, prefix="/api")
app.include_router(bank_router, prefix="/api")
app.include_router(traceability_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(green_actions_router, prefix="/api")
