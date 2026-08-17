"""
Document Pipeline API Endpoints.

Handles:
- POST /api/documents/upload — upload a new document
- GET /api/documents/{document_id} — get document details
- GET /api/documents/{document_id}/fields — get extracted fields
- POST /api/documents/{document_id}/confirm — confirm fields (with optional corrections)
- POST /api/documents/{document_id}/normalize — normalize confirmed fields
- GET /api/farmers/{farmer_id}/documents — list farmer's documents
"""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.models import DataDomain, SourceLevel
from backend.app.repositories import (
    get_document_field_repo,
    get_document_repo,
    get_standardized_record_repo,
)
from backend.app.services.documents.extraction import (
    confirm_fields,
    normalize_document,
    run_ocr,
)
from backend.app.services.documents.upload import UploadError, upload_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def api_upload_document(
    file: UploadFile = File(...),
    farmer_id: str = Form(...),
    domain: str = Form(...),
    source_level: str = Form(default="V1"),
    upload_note: Optional[str] = Form(default=None),
):
    """
    Upload a document and trigger OCR extraction.

    Returns document with extracted fields.
    """
    # Read file content
    content = await file.read()

    # Validate domain enum
    try:
        data_domain = DataDomain(domain)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無效的資料領域: {domain}。有效值: {[d.value for d in DataDomain]}",
        )

    # Validate source level
    try:
        src_level = SourceLevel(source_level)
    except ValueError:
        src_level = SourceLevel.V1

    # Upload document
    try:
        document = upload_document(
            content=content,
            filename=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            farmer_id=farmer_id,
            domain=data_domain,
            source_level=src_level,
            upload_note=upload_note,
        )
    except UploadError as e:
        raise HTTPException(
            status_code=400,
            detail={"message": str(e), "error_code": e.error_code},
        )

    # Run OCR
    fields = run_ocr(document, content)

    return {
        "document": document.model_dump(),
        "fields": [f.model_dump() for f in fields],
        "message": "文件上傳成功，OCR 已完成",
    }


@router.get("/{document_id}")
def api_get_document(document_id: str):
    """Get document details by ID."""
    doc_repo = get_document_repo()
    document = doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文件不存在")
    return document.model_dump()


@router.get("/{document_id}/fields")
def api_get_document_fields(document_id: str):
    """Get all extracted fields for a document."""
    doc_repo = get_document_repo()
    if not doc_repo.exists(document_id):
        raise HTTPException(status_code=404, detail="文件不存在")

    field_repo = get_document_field_repo()
    fields = field_repo.find_by(document_id=document_id)
    return {"document_id": document_id, "fields": [f.model_dump() for f in fields]}


class ConfirmFieldsRequest(BaseModel):
    """Request body for field confirmation."""
    corrections: dict[str, str] = {}  # {field_id: corrected_value}


@router.post("/{document_id}/confirm")
def api_confirm_fields(document_id: str, request: ConfirmFieldsRequest):
    """
    Confirm extracted fields with optional human corrections.

    Per AGENTS.md §14: OCR → Human Confirmation → Normalized Fields.
    """
    doc_repo = get_document_repo()
    if not doc_repo.exists(document_id):
        raise HTTPException(status_code=404, detail="文件不存在")

    fields = confirm_fields(document_id, corrections=request.corrections)
    return {
        "document_id": document_id,
        "status": "FIELDS_CONFIRMED",
        "fields": [f.model_dump() for f in fields],
        "message": "欄位已確認",
    }


@router.post("/{document_id}/normalize")
def api_normalize_document(document_id: str):
    """
    Normalize confirmed fields into a StandardizedRecord.

    Must be called after confirm.
    """
    doc_repo = get_document_repo()
    document = doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文件不存在")

    if document.status.value not in ("FIELDS_CONFIRMED", "OCR_COMPLETED"):
        raise HTTPException(
            status_code=400,
            detail=f"文件狀態不正確: {document.status.value}。需先確認欄位。",
        )

    record = normalize_document(document_id)
    if not record:
        raise HTTPException(status_code=500, detail="標準化失敗")

    return {
        "document_id": document_id,
        "record": record.model_dump(),
        "message": "文件已標準化",
    }


@router.get("/{document_id}/record")
def api_get_document_record(document_id: str):
    """Get the standardized record produced from a document."""
    rec_repo = get_standardized_record_repo()
    records = rec_repo.find_by(document_id=document_id)
    if not records:
        raise HTTPException(status_code=404, detail="尚未產生標準化紀錄")
    return records[0].model_dump()


# ─── Farmer Documents ─────────────────────────────────────────────────────────

farmer_router = APIRouter(prefix="/farmers", tags=["farmers"])


@farmer_router.get("/{farmer_id}/documents")
def api_get_farmer_documents(farmer_id: str):
    """List all documents for a farmer."""
    doc_repo = get_document_repo()
    documents = doc_repo.find_by(farmer_id=farmer_id)
    return {
        "farmer_id": farmer_id,
        "count": len(documents),
        "documents": [d.model_dump() for d in documents],
    }
