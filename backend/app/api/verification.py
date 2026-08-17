"""
Verification & Anomaly Detection API Endpoints.

Handles:
- POST /api/documents/{id}/verify — run verification + anomaly detection
- GET /api/farmers/{id}/anomalies — list farmer's anomalies
- GET /api/farmers/{id}/review-queue — unresolved anomalies
- POST /api/anomalies/{id}/resolve — mark anomaly as resolved
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.repositories import (
    get_anomaly_repo,
    get_document_repo,
    get_standardized_record_repo,
    get_verification_repo,
)
from backend.app.services.anomaly.detect import (
    detect_document_anomalies,
    get_review_queue,
)
from backend.app.services.verification.verify import verify_document_records
from backend.app.models.base import now_taipei

router = APIRouter(tags=["verification"])


@router.post("/documents/{document_id}/verify")
def api_verify_document(document_id: str):
    """
    Run verification and anomaly detection on a document's records.

    Must be called after normalization (document has StandardizedRecords).
    """
    doc_repo = get_document_repo()
    document = doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文件不存在")

    rec_repo = get_standardized_record_repo()
    records = rec_repo.find_by(document_id=document_id)
    if not records:
        raise HTTPException(
            status_code=400,
            detail="此文件尚未產生標準化紀錄，請先完成標準化",
        )

    # Run verification
    verifications = verify_document_records(document_id)

    # Run anomaly detection
    anomalies = detect_document_anomalies(document_id)

    # Update document status to VERIFIED
    from backend.app.models import DocumentStatus
    document.status = DocumentStatus.VERIFIED
    doc_repo.update(document)

    return {
        "document_id": document_id,
        "status": "VERIFIED",
        "verifications": [v.model_dump() for v in verifications],
        "anomalies": [a.model_dump() for a in anomalies],
        "anomaly_count": len(anomalies),
        "message": f"核驗完成。發現 {len(anomalies)} 個異常。",
    }


@router.get("/farmers/{farmer_id}/anomalies")
def api_get_farmer_anomalies(farmer_id: str):
    """Get all anomalies for a farmer's records."""
    review_queue = get_review_queue(farmer_id)
    # Also get resolved ones
    anomaly_repo = get_anomaly_repo()
    all_anomalies = anomaly_repo.get_all()

    rec_repo = get_standardized_record_repo()
    farmer_records = rec_repo.find_by(farmer_id=farmer_id)
    farmer_record_ids = {r.id for r in farmer_records}

    farmer_anomalies = [a for a in all_anomalies if a.record_id in farmer_record_ids]

    return {
        "farmer_id": farmer_id,
        "total": len(farmer_anomalies),
        "unresolved": len([a for a in farmer_anomalies if not a.is_resolved]),
        "anomalies": [a.model_dump() for a in farmer_anomalies],
    }


@router.get("/farmers/{farmer_id}/review-queue")
def api_get_review_queue(farmer_id: str):
    """Get unresolved anomalies requiring human review."""
    queue = get_review_queue(farmer_id)
    return {
        "farmer_id": farmer_id,
        "count": len(queue),
        "items": [a.model_dump() for a in queue],
    }


class ResolveRequest(BaseModel):
    """Request to resolve an anomaly."""
    resolved_by: str = "reviewer"
    notes: Optional[str] = None


@router.post("/anomalies/{anomaly_id}/resolve")
def api_resolve_anomaly(anomaly_id: str, request: ResolveRequest):
    """Mark an anomaly as resolved (human review complete)."""
    anomaly_repo = get_anomaly_repo()
    anomaly = anomaly_repo.get_by_id(anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="異常紀錄不存在")

    if anomaly.is_resolved:
        raise HTTPException(status_code=400, detail="此異常已解決")

    anomaly.is_resolved = True
    anomaly.resolved_by = request.resolved_by
    anomaly.resolved_at = now_taipei()
    anomaly_repo.update(anomaly)

    return {
        "anomaly_id": anomaly_id,
        "status": "resolved",
        "resolved_by": request.resolved_by,
        "message": "異常已標記為已解決",
    }
