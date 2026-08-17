"""
Bank Workflow API Endpoints.

Per AGENTS.md §17, bank can:
- View authorized cases
- View experience/indicators/data health
- View anomalies
- Trace evidence
- Generate bank information package

Bank CANNOT:
- Modify farmer evidence
- Modify GreenFin calculations
- Make lending decisions within GreenFin
"""

from fastapi import APIRouter, HTTPException

from backend.app.models import AuthorizationStatus
from backend.app.repositories import (
    get_authorization_repo,
    get_bank_case_repo,
    get_bank_repo,
    get_document_repo,
    get_document_field_repo,
    get_farmer_repo,
    get_farm_repo,
    get_standardized_record_repo,
    get_verification_repo,
    get_anomaly_repo,
)
from backend.app.services import audit
from backend.app.services.authorization.guard import require_bank_authorization
from backend.app.services.experience.calculate import get_farmer_experience_summary
from backend.app.services.indicators.calculate import get_farmer_indicators
from backend.app.services.data_health.calculate import get_farmer_data_health

router = APIRouter(prefix="/bank", tags=["bank"])


@router.get("/{institution_id}/cases")
def api_get_bank_cases(institution_id: str):
    """
    Get all authorized cases for a bank.

    Returns list of farmers that have granted this bank active authorization.
    """
    auth_repo = get_authorization_repo()
    farmer_repo = get_farmer_repo()

    all_auths = auth_repo.find_by(institution_id=institution_id)
    active_auths = [a for a in all_auths if a.status == AuthorizationStatus.ACTIVE]

    cases = []
    for auth in active_auths:
        farmer = farmer_repo.get_by_id(auth.farmer_id)
        cases.append({
            "authorization_id": auth.id,
            "farmer_id": auth.farmer_id,
            "farmer_name": farmer.real_name if farmer else "Unknown",
            "purpose": auth.purpose,
            "data_scope": auth.data_scope,
            "start_at": auth.start_at,
            "expire_at": auth.expire_at,
        })

    return {
        "institution_id": institution_id,
        "case_count": len(cases),
        "cases": cases,
    }


@router.get("/{institution_id}/cases/{farmer_id}")
def api_get_case_detail(institution_id: str, farmer_id: str):
    """
    Get full case detail for a bank — includes experience, indicators, data health.

    Enforced by authorization guard.
    """
    require_bank_authorization(farmer_id, institution_id)
    audit.bank_data_accessed(institution_id, farmer_id, resource="case_detail")

    farmer_repo = get_farmer_repo()
    farm_repo = get_farm_repo()
    farmer = farmer_repo.get_by_id(farmer_id)

    # Farmer profile
    profile = None
    farms = []
    if farmer:
        profile = farmer.model_dump()
        farms = [f.model_dump() for f in farm_repo.find_by(farmer_id=farmer_id)]

    # Analysis
    experience = get_farmer_experience_summary(farmer_id)
    indicators = get_farmer_indicators(farmer_id)
    data_health = get_farmer_data_health(farmer_id)

    # Anomalies
    anomaly_repo = get_anomaly_repo()
    rec_repo = get_standardized_record_repo()
    records = rec_repo.find_by(farmer_id=farmer_id)
    record_ids = {r.id for r in records}
    all_anomalies = anomaly_repo.get_all()
    farmer_anomalies = [a for a in all_anomalies if a.record_id in record_ids]

    return {
        "institution_id": institution_id,
        "farmer_id": farmer_id,
        "profile": profile,
        "farms": farms,
        "experience": experience,
        "indicators": [i.model_dump() for i in indicators],
        "data_health": [d.model_dump() for d in data_health],
        "anomalies": {
            "total": len(farmer_anomalies),
            "unresolved": len([a for a in farmer_anomalies if not a.is_resolved]),
            "items": [a.model_dump() for a in farmer_anomalies],
        },
        "disclaimer": "此為授信補充資訊，最終授信仍由金融機構依 KYC、聯徵、還款能力、用途、擔保及內部政策完成判斷。",
    }


@router.get("/{institution_id}/cases/{farmer_id}/evidence")
def api_get_case_evidence(institution_id: str, farmer_id: str):
    """
    Get all evidence (documents + records) for a case.

    Allows bank to trace results back to original documents.
    """
    require_bank_authorization(farmer_id, institution_id)
    audit.bank_data_accessed(institution_id, farmer_id, resource="evidence_chain")

    doc_repo = get_document_repo()
    field_repo = get_document_field_repo()
    rec_repo = get_standardized_record_repo()
    ver_repo = get_verification_repo()

    documents = doc_repo.find_by(farmer_id=farmer_id)
    records = rec_repo.find_by(farmer_id=farmer_id)

    evidence_chain = []
    for doc in documents:
        fields = field_repo.find_by(document_id=doc.id)
        doc_records = rec_repo.find_by(document_id=doc.id)
        verifications = []
        for r in doc_records:
            vers = ver_repo.find_by(record_id=r.id)
            verifications.extend(vers)

        evidence_chain.append({
            "document": doc.model_dump(),
            "fields": [f.model_dump() for f in fields],
            "records": [r.model_dump() for r in doc_records],
            "verifications": [v.model_dump() for v in verifications],
        })

    return {
        "institution_id": institution_id,
        "farmer_id": farmer_id,
        "document_count": len(documents),
        "record_count": len(records),
        "evidence": evidence_chain,
    }


@router.get("/{institution_id}/cases/{farmer_id}/trace/{record_id}")
def api_trace_record(institution_id: str, farmer_id: str, record_id: str):
    """
    Trace a single record back to its original document and verification.

    Per AGENTS.md §6: Result → Calculation → Rule → Record → Evidence → Document
    """
    require_bank_authorization(farmer_id, institution_id)
    audit.bank_data_accessed(institution_id, farmer_id, resource=f"trace:{record_id}")

    rec_repo = get_standardized_record_repo()
    record = rec_repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="紀錄不存在")

    doc_repo = get_document_repo()
    field_repo = get_document_field_repo()
    ver_repo = get_verification_repo()

    document = doc_repo.get_by_id(record.document_id)
    fields = field_repo.find_by(document_id=record.document_id) if document else []
    verifications = ver_repo.find_by(record_id=record_id)

    return {
        "trace": {
            "record": record.model_dump(),
            "document": document.model_dump() if document else None,
            "fields": [f.model_dump() for f in fields],
            "verifications": [v.model_dump() for v in verifications],
        },
        "lineage": "Result → StandardizedRecord → DocumentFields → OriginalDocument",
    }
