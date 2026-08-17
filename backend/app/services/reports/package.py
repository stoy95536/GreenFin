"""
Bank Information Package Generation.

Per DEVELOPMENT_PLAN.md GATE-13:
- Authorization check
- Data correctness
- Rule version
- Evidence references
- Disclaimer
- Generation timestamp

Per AGENTS.md §17: Bank can generate 授信補充資料包.
This is the final output that a bank reviewer can download/view.
"""

from datetime import datetime, timezone

from backend.app.models import AuthorizationStatus
from backend.app.models.base import now_taipei
from backend.app.repositories import (
    get_anomaly_repo,
    get_authorization_repo,
    get_document_repo,
    get_farmer_repo,
    get_farm_repo,
    get_standardized_record_repo,
    get_verification_repo,
)
from backend.app.services import audit
from backend.app.services.authorization.service import check_authorization
from backend.app.services.experience.calculate import get_farmer_experience_summary
from backend.app.services.indicators.calculate import get_farmer_indicators
from backend.app.services.data_health.calculate import get_farmer_data_health
from backend.app.services.traceability import validate_farmer_traceability


class ReportError(Exception):
    """Report generation error."""
    pass


def generate_bank_information_package(
    farmer_id: str,
    institution_id: str,
) -> dict:
    """
    Generate the Bank Information Package (授信補充資料包).

    This is the primary deliverable for the bank — a structured, traceable,
    explainable data package that summarizes the farmer's green profile.

    Verifies:
    1. Authorization is valid
    2. Farmer data exists
    3. All calculations are traceable

    Returns a comprehensive JSON package.

    Raises:
        ReportError: If authorization invalid or data incomplete.
    """
    # Step 1: Verify authorization
    auth = check_authorization(farmer_id, institution_id)
    if not auth:
        raise ReportError("無有效授權：無法產生授信補充資料包")

    # Step 2: Gather farmer profile
    farmer_repo = get_farmer_repo()
    farm_repo = get_farm_repo()
    farmer = farmer_repo.get_by_id(farmer_id)
    if not farmer:
        raise ReportError(f"小農資料不存在: {farmer_id}")

    farms = farm_repo.find_by(farmer_id=farmer_id)

    # Step 3: Gather analysis results
    experience = get_farmer_experience_summary(farmer_id)
    indicators = get_farmer_indicators(farmer_id)
    data_health = get_farmer_data_health(farmer_id)

    # Step 4: Gather evidence summary
    doc_repo = get_document_repo()
    rec_repo = get_standardized_record_repo()
    ver_repo = get_verification_repo()
    anomaly_repo = get_anomaly_repo()

    documents = doc_repo.find_by(farmer_id=farmer_id)
    records = rec_repo.find_by(farmer_id=farmer_id)
    record_ids = {r.id for r in records}

    all_anomalies = anomaly_repo.get_all()
    farmer_anomalies = [a for a in all_anomalies if a.record_id in record_ids]

    # Step 5: Validate traceability
    traceability = validate_farmer_traceability(farmer_id)

    # Step 6: Build package
    generated_at = now_taipei()

    audit.report_generated(
        institution_id=institution_id,
        farmer_id=farmer_id,
        package_type="BANK_INFORMATION_PACKAGE",
    )

    package = {
        # Metadata
        "package_type": "BANK_INFORMATION_PACKAGE",
        "version": "1.0",
        "generated_at": generated_at,
        "demo_mode": True,

        # Authorization
        "authorization": {
            "id": auth.id,
            "institution_id": institution_id,
            "farmer_id": farmer_id,
            "purpose": auth.purpose,
            "data_scope": auth.data_scope,
            "start_at": auth.start_at,
            "expire_at": auth.expire_at,
        },

        # Farmer Profile
        "farmer": {
            "id": farmer.id,
            "name": farmer.real_name,
            "farms": [{"name": f.name, "location": f.location, "area": f.area_hectares} for f in farms],
        },

        # Experience
        "experience": experience,

        # Indicators (independent, not combined)
        "indicators": [
            {
                "type": i.indicator_type,
                "score": i.score,
                "level": i.level,
                "rule_version": i.rule_version,
                "calculated_at": i.calculated_at,
                "calculation_trace": i.calculation_trace,
            }
            for i in indicators
        ],

        # Data Health
        "data_health": [
            {
                "domain": d.domain.value,
                "status": d.status.value,
                "reasons": d.reasons,
                "actions": d.actions,
                "rule_version": d.rule_version,
            }
            for d in data_health
        ],

        # Evidence Summary
        "evidence_summary": {
            "document_count": len(documents),
            "record_count": len(records),
            "anomaly_count": len(farmer_anomalies),
            "unresolved_anomalies": len([a for a in farmer_anomalies if not a.is_resolved]),
        },

        # Traceability
        "traceability": {
            "all_valid": traceability["all_valid"],
            "experience_chain_count": len(traceability["experience_traces"]),
            "indicator_chain_count": len(traceability["indicator_traces"]),
            "data_health_chain_count": len(traceability["data_health_traces"]),
        },

        # Disclaimer (required per AGENTS.md)
        "disclaimer": (
            "本資料包為 GreenFin 平台產生之授信補充資訊，僅供金融機構參考。"
            "所有經驗值、分析指標與 Data Health 均非信用評分、核貸建議或違約預測。"
            "最終授信決定仍由金融機構依 KYC、聯徵、還款能力、用途、擔保／信保、"
            "財務資料及內部政策完成判斷。"
            "本資料包為 DEMO / SIMULATED，不代表已商轉或被正式採用。"
        ),
    }

    return package
