"""
GreenFin Domain Models.

All entity models are Pydantic BaseModel subclasses.
Storage is JSON file-based (see ADR-0006).
"""

from backend.app.models.enums import (
    ActionLevel,
    AnomalySeverity,
    AnomalyType,
    AuditEventType,
    AuthorizationStatus,
    DataDomain,
    DataHealthStatus,
    DocumentStatus,
    ExperienceLevel,
    GreenDimension,
    SourceLevel,
    UserRole,
)
from backend.app.models.base import EntityBase
from backend.app.models.user import User, FarmerProfile, BankInstitution
from backend.app.models.farm import Farm, Crop
from backend.app.models.document import Document, DocumentField, StandardizedRecord
from backend.app.models.verification import VerificationResult, Anomaly
from backend.app.models.green_action import GreenAction, ExperienceTransaction
from backend.app.models.indicators import IndicatorResult, DataHealthResult
from backend.app.models.authorization import RuleSet, Authorization, BankCase
from backend.app.models.audit import AuditLog

__all__ = [
    # Enums
    "ActionLevel",
    "AnomalySeverity",
    "AnomalyType",
    "AuditEventType",
    "AuthorizationStatus",
    "DataDomain",
    "DataHealthStatus",
    "DocumentStatus",
    "ExperienceLevel",
    "GreenDimension",
    "SourceLevel",
    "UserRole",
    # Base
    "EntityBase",
    # Entities
    "User",
    "FarmerProfile",
    "BankInstitution",
    "Farm",
    "Crop",
    "Document",
    "DocumentField",
    "StandardizedRecord",
    "VerificationResult",
    "Anomaly",
    "GreenAction",
    "ExperienceTransaction",
    "IndicatorResult",
    "DataHealthResult",
    "RuleSet",
    "Authorization",
    "BankCase",
    "AuditLog",
]
