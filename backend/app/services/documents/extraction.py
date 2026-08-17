"""
Field Extraction and Normalization Service.

Processes OCR results into DocumentFields and StandardizedRecords.

Pipeline:
  Document → OCR → DocumentFields → Human Confirmation → Normalization → StandardizedRecord
"""

import re
from typing import Optional

from backend.app.models import (
    DataDomain,
    Document,
    DocumentField,
    DocumentStatus,
    SourceLevel,
    StandardizedRecord,
)
from backend.app.repositories import (
    get_document_field_repo,
    get_document_repo,
    get_standardized_record_repo,
)
from backend.app.services.ocr.provider import OCRResult, get_ocr_provider


def run_ocr(document: Document, content: bytes) -> list[DocumentField]:
    """
    Run OCR on a document and create DocumentField records.

    Args:
        document: The Document entity.
        content: File bytes for OCR processing.

    Returns:
        List of created DocumentField entities.
    """
    provider = get_ocr_provider()
    result: OCRResult = provider.extract(
        content=content,
        filename=document.filename,
        mime_type=document.mime_type or "application/octet-stream",
        domain=document.domain,
    )

    if not result.success:
        return []

    field_repo = get_document_field_repo()
    created_fields = []

    for ocr_field in result.fields:
        doc_field = DocumentField(
            document_id=document.id,
            field_name=ocr_field.field_name,
            raw_value=ocr_field.raw_value,
            normalized_value=None,  # Normalization happens after confirmation
            confidence=ocr_field.confidence,
            source="ocr",
            manually_corrected=False,
        )
        field_repo.create(doc_field)
        created_fields.append(doc_field)

    # Update document status
    doc_repo = get_document_repo()
    document.status = DocumentStatus.OCR_COMPLETED
    doc_repo.update(document)

    return created_fields


def confirm_fields(document_id: str, corrections: Optional[dict[str, str]] = None) -> list[DocumentField]:
    """
    Confirm extracted fields, optionally applying human corrections.

    Args:
        document_id: Document to confirm fields for.
        corrections: Dict of {field_id: corrected_value} for human corrections.

    Returns:
        Updated list of DocumentFields.
    """
    field_repo = get_document_field_repo()
    fields = field_repo.find_by(document_id=document_id)

    corrections = corrections or {}

    for field in fields:
        if field.id in corrections:
            field.raw_value = corrections[field.id]
            field.manually_corrected = True
            field_repo.update(field)

    # Update document status
    doc_repo = get_document_repo()
    document = doc_repo.get_by_id(document_id)
    if document:
        document.status = DocumentStatus.FIELDS_CONFIRMED
        doc_repo.update(document)

    return field_repo.find_by(document_id=document_id)


def normalize_value(field_name: str, raw_value: str) -> str:
    """
    Normalize a raw OCR value based on field type.

    Handles:
    - Dates: various formats → ISO 8601 (YYYY-MM-DD)
    - Amounts: NT$xxx,xxx → numeric string
    - General text: strip whitespace
    """
    if not raw_value:
        return ""

    value = raw_value.strip()

    # Date normalization: YYYY/MM/DD or YYYY.MM.DD → YYYY-MM-DD
    date_match = re.match(r"(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})", value)
    if date_match:
        y, m, d = date_match.groups()
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

    # Amount normalization: NT$xxx,xxx or $xxx → numeric
    amount_match = re.match(r"(?:NT\$?|＄|\$)\s*([\d,]+(?:\.\d+)?)", value)
    if amount_match:
        return amount_match.group(1).replace(",", "")

    # Area normalization: x.x 公頃 → keep number
    area_match = re.match(r"([\d.]+)\s*公頃", value)
    if area_match:
        return area_match.group(1)

    # Default: strip and return
    return value


def normalize_document(document_id: str) -> Optional[StandardizedRecord]:
    """
    Normalize confirmed fields into a StandardizedRecord.

    Args:
        document_id: Document to normalize.

    Returns:
        Created StandardizedRecord, or None if document not found.
    """
    doc_repo = get_document_repo()
    document = doc_repo.get_by_id(document_id)
    if not document:
        return None

    field_repo = get_document_field_repo()
    fields = field_repo.find_by(document_id=document_id)

    # Normalize each field
    normalized_data = {}
    for field in fields:
        raw = field.raw_value or ""
        normalized = normalize_value(field.field_name, raw)
        field.normalized_value = normalized
        field_repo.update(field)
        normalized_data[field.field_name] = normalized

    # Create standardized record
    record_type = _infer_record_type(document.domain)
    record = StandardizedRecord(
        document_id=document_id,
        farmer_id=document.farmer_id,
        domain=document.domain,
        record_type=record_type,
        data=normalized_data,
        source_level=document.source_level,
        is_valid=True,
    )

    rec_repo = get_standardized_record_repo()
    rec_repo.create(record)

    # Update document status
    document.status = DocumentStatus.NORMALIZED
    doc_repo.update(document)

    return record


def _infer_record_type(domain: DataDomain) -> str:
    """Infer record type from data domain."""
    mapping = {
        DataDomain.IDENTITY: "identity_record",
        DataDomain.LAND_CROP: "land_crop_record",
        DataDomain.TRANSACTION: "transaction_record",
        DataDomain.INPUT_EQUIPMENT: "equipment_record",
        DataDomain.GREEN_ACTION: "green_activity_record",
        DataDomain.CERTIFICATION: "certification_record",
        DataDomain.LOAN_PURPOSE: "loan_purpose_record",
    }
    return mapping.get(domain, "general_record")
