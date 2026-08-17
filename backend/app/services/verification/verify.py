"""
Verification Service.

Determines source level (V0-V3) for a StandardizedRecord based on:
- Document source level
- Field confidence from OCR
- Expiry status
- Anomaly presence

Per AGENTS.md §10:
  V3 = 官方／合作系統直接核驗
  V2 = 可查核第三方文件
  V1 = 自行提交且部分佐證
  V0 = 無法使用或確認異常

Each VerificationResult must preserve reason.
"""

from datetime import date, datetime

from backend.app.models import (
    Document,
    SourceLevel,
    StandardizedRecord,
    VerificationResult,
)
from backend.app.repositories import (
    get_document_field_repo,
    get_document_repo,
    get_standardized_record_repo,
    get_verification_repo,
)


def verify_record(record: StandardizedRecord) -> VerificationResult:
    """
    Verify a standardized record and determine its source level.

    Logic:
    1. Start with the document's declared source level
    2. Downgrade if data quality issues found:
       - Low OCR confidence → V1 at best
       - Expired data → V0
       - Missing critical data → V0
    3. Create and persist VerificationResult

    Args:
        record: The StandardizedRecord to verify.

    Returns:
        Created VerificationResult.
    """
    doc_repo = get_document_repo()
    field_repo = get_document_field_repo()
    ver_repo = get_verification_repo()

    document = doc_repo.get_by_id(record.document_id)
    if not document:
        # No source document — cannot verify
        result = VerificationResult(
            record_id=record.id,
            source_level=SourceLevel.V0,
            reason="來源文件不存在，無法核驗 (DEMO)",
            verified_by="system",
            evidence_ids=[],
        )
        ver_repo.create(result)
        return result

    # Start with document's declared source level
    determined_level = document.source_level
    reasons = []

    # Check 1: OCR confidence — if any field below 0.5, cap at V1
    fields = field_repo.find_by(document_id=document.id)
    low_confidence_fields = [f for f in fields if f.confidence is not None and f.confidence < 0.5]
    if low_confidence_fields:
        if determined_level in (SourceLevel.V3, SourceLevel.V2):
            determined_level = SourceLevel.V1
        reasons.append(f"OCR 信心度不足的欄位: {len(low_confidence_fields)} 個 (< 0.5)")

    # Check 2: Expiry — look for date fields that are in the past
    expiry_value = record.data.get("有效期限") or record.data.get("expiry")
    if expiry_value:
        try:
            expiry_date = _parse_date(expiry_value)
            if expiry_date and expiry_date < date.today():
                determined_level = SourceLevel.V0
                reasons.append(f"文件已過期: {expiry_value}")
        except (ValueError, TypeError):
            pass

    # Check 3: Record not valid → V0
    if not record.is_valid:
        determined_level = SourceLevel.V0
        reasons.append("紀錄已標記為無效")

    # If no issues, provide positive reason
    if not reasons:
        level_descriptions = {
            SourceLevel.V3: "官方／合作系統直接核驗 (DEMO SIMULATED)",
            SourceLevel.V2: "可查核第三方文件 (DEMO SIMULATED)",
            SourceLevel.V1: "自行提交且部分佐證 (DEMO SIMULATED)",
            SourceLevel.V0: "無法使用或確認異常 (DEMO SIMULATED)",
        }
        reasons.append(level_descriptions.get(determined_level, ""))

    # Update record's source level
    rec_repo = get_standardized_record_repo()
    record.source_level = determined_level
    rec_repo.update(record)

    # Create verification result
    result = VerificationResult(
        record_id=record.id,
        source_level=determined_level,
        reason="; ".join(reasons),
        verified_by="system",
        evidence_ids=[document.id],
    )
    ver_repo.create(result)

    return result


def verify_document_records(document_id: str) -> list[VerificationResult]:
    """
    Verify all standardized records produced from a document.

    Returns list of verification results.
    """
    rec_repo = get_standardized_record_repo()
    records = rec_repo.find_by(document_id=document_id)

    results = []
    for record in records:
        result = verify_record(record)
        results.append(result)

    return results


def _parse_date(value: str) -> date | None:
    """Try to parse a date string in various formats."""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
