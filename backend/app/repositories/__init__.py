"""
GreenFin Repositories.

JSON file-based repositories for all domain entities (ADR-0006).
Each repository provides CRUD operations on its respective JSON data file.

The active data directory is resolved lazily via core.storage.get_data_dir().
Import get_data_dir() rather than a DATA_DIR constant, so overrides always apply.
"""

from backend.app.core.storage import (
    PRODUCTION_DATA_DIR,
    get_data_dir,
    set_data_dir,
)
from backend.app.repositories.json_repository import JsonRepository
from backend.app.models import (
    AuditLog,
    Authorization,
    Anomaly,
    BankCase,
    BankInstitution,
    Crop,
    DataHealthResult,
    Document,
    DocumentField,
    ExperienceTransaction,
    Farm,
    FarmerProfile,
    GreenAction,
    IndicatorResult,
    RuleSet,
    StandardizedRecord,
    User,
    VerificationResult,
)


def get_user_repo() -> JsonRepository[User]:
    return JsonRepository(User, "users.json")


def get_farmer_repo() -> JsonRepository[FarmerProfile]:
    return JsonRepository(FarmerProfile, "farmers.json")


def get_bank_repo() -> JsonRepository[BankInstitution]:
    return JsonRepository(BankInstitution, "banks.json")


def get_farm_repo() -> JsonRepository[Farm]:
    return JsonRepository(Farm, "farms.json")


def get_crop_repo() -> JsonRepository[Crop]:
    return JsonRepository(Crop, "crops.json")


def get_document_repo() -> JsonRepository[Document]:
    return JsonRepository(Document, "documents.json")


def get_document_field_repo() -> JsonRepository[DocumentField]:
    return JsonRepository(DocumentField, "document_fields.json")


def get_standardized_record_repo() -> JsonRepository[StandardizedRecord]:
    return JsonRepository(StandardizedRecord, "standardized_records.json")


def get_verification_repo() -> JsonRepository[VerificationResult]:
    return JsonRepository(VerificationResult, "verification_results.json")


def get_anomaly_repo() -> JsonRepository[Anomaly]:
    return JsonRepository(Anomaly, "anomalies.json")


def get_green_action_repo() -> JsonRepository[GreenAction]:
    return JsonRepository(GreenAction, "green_actions.json")


def get_experience_repo() -> JsonRepository[ExperienceTransaction]:
    return JsonRepository(ExperienceTransaction, "experience_transactions.json")


def get_indicator_repo() -> JsonRepository[IndicatorResult]:
    return JsonRepository(IndicatorResult, "indicator_results.json")


def get_data_health_repo() -> JsonRepository[DataHealthResult]:
    return JsonRepository(DataHealthResult, "data_health_results.json")


def get_rule_set_repo() -> JsonRepository[RuleSet]:
    return JsonRepository(RuleSet, "rule_sets.json")


def get_authorization_repo() -> JsonRepository[Authorization]:
    return JsonRepository(Authorization, "authorizations.json")


def get_bank_case_repo() -> JsonRepository[BankCase]:
    return JsonRepository(BankCase, "bank_cases.json")


def get_audit_log_repo() -> JsonRepository[AuditLog]:
    return JsonRepository(AuditLog, "audit_logs.json")


__all__ = [
    "JsonRepository",
    "get_data_dir",
    "set_data_dir",
    "PRODUCTION_DATA_DIR",
    "get_user_repo",
    "get_farmer_repo",
    "get_bank_repo",
    "get_farm_repo",
    "get_crop_repo",
    "get_document_repo",
    "get_document_field_repo",
    "get_standardized_record_repo",
    "get_verification_repo",
    "get_anomaly_repo",
    "get_green_action_repo",
    "get_experience_repo",
    "get_indicator_repo",
    "get_data_health_repo",
    "get_rule_set_repo",
    "get_authorization_repo",
    "get_bank_case_repo",
    "get_audit_log_repo",
]
