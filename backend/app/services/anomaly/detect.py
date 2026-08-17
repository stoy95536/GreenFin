"""
Anomaly Detection Service.

Detects anomalies on StandardizedRecords per AGENTS.md §13.

Required anomaly types:
- DUPLICATE
- EXPIRED
- FUTURE_DATE
- CONFLICT
- INVALID_FORMAT
- OCR_LOW_CONFIDENCE
- MISSING_REQUIRED_FIELD
- VERIFICATION_FAILED

Anomaly data must not be deleted — goes to Review Queue.
"""

from typing import Optional

from backend.app.core.dates import is_expired, parse_date, years_from_now
from backend.app.models import (
    Anomaly,
    AnomalySeverity,
    AnomalyType,
    DataDomain,
    Document,
    SourceLevel,
    StandardizedRecord,
)
from backend.app.repositories import (
    get_anomaly_repo,
    get_document_field_repo,
    get_document_repo,
    get_standardized_record_repo,
)
from backend.app.rules import get_active_engine
from backend.app.services import audit

# Date-bearing field names, used for expiry / format checks.
EXPIRY_FIELD_NAMES = ("有效期限", "expiry", "到期日")
EVENT_DATE_FIELD_NAMES = ("交易日期", "執行日期", "購入日期", "登記日期", "action_date")

# A date more than this many years ahead is treated as a data-entry error.
FUTURE_DATE_TOLERANCE_YEARS = 5

# OCR confidence below this is considered unreliable.
OCR_LOW_CONFIDENCE_THRESHOLD = 0.5


def _required_fields_for(domain: DataDomain) -> list[str]:
    """
    Required fields for a domain, read from the active rule set.

    Single source of truth: this previously duplicated the rule config in a module
    constant, so editing the rule set changed Data Health but not anomaly detection.
    """
    rules = get_active_engine().get_data_health_rules()
    return rules.domain_required_fields.get(domain.value, [])


def detect_anomalies(record: StandardizedRecord) -> list[Anomaly]:
    """
    Run all anomaly detection checks on a standardized record.

    Creates and persists Anomaly records for each issue found.

    Args:
        record: The StandardizedRecord to check.

    Returns:
        List of detected Anomaly entities.
    """
    anomalies: list[Anomaly] = []
    anomaly_repo = get_anomaly_repo()

    doc_repo = get_document_repo()
    document = doc_repo.get_by_id(record.document_id)

    # 1. EXPIRED — check date fields for past expiry
    expired = _check_expired(record)
    if expired:
        anomalies.append(expired)

    # 2. FUTURE_DATE — check for dates unreasonably in the future
    future = _check_future_date(record)
    if future:
        anomalies.append(future)

    # 3. DUPLICATE — check for same-hash documents
    duplicate = _check_duplicate(record, document)
    if duplicate:
        anomalies.append(duplicate)

    # 4. OCR_LOW_CONFIDENCE — check field confidence
    low_conf = _check_ocr_low_confidence(record)
    if low_conf:
        anomalies.append(low_conf)

    # 5. MISSING_REQUIRED_FIELD — check domain-required fields
    missing = _check_missing_required(record)
    if missing:
        anomalies.append(missing)

    # 6. VERIFICATION_FAILED — V0 source level
    ver_fail = _check_verification_failed(record)
    if ver_fail:
        anomalies.append(ver_fail)

    # 7. CONFLICT — check for contradictory data across records
    conflict = _check_conflict(record)
    if conflict:
        anomalies.append(conflict)

    # 8. INVALID_FORMAT — check for unparseable critical fields
    invalid_fmt = _check_invalid_format(record)
    if invalid_fmt:
        anomalies.append(invalid_fmt)

    # Persist all anomalies and record each detection in the audit trail
    for anomaly in anomalies:
        anomaly_repo.create(anomaly)
        audit.anomaly_detected(
            record_id=anomaly.record_id,
            anomaly_type=anomaly.anomaly_type.value,
            severity=anomaly.severity.value,
            description=anomaly.description,
        )

    return anomalies


def detect_document_anomalies(document_id: str) -> list[Anomaly]:
    """
    Run anomaly detection on all records from a document.
    """
    rec_repo = get_standardized_record_repo()
    records = rec_repo.find_by(document_id=document_id)

    all_anomalies = []
    for record in records:
        anomalies = detect_anomalies(record)
        all_anomalies.extend(anomalies)

    return all_anomalies


def get_review_queue(farmer_id: str) -> list[Anomaly]:
    """
    Get unresolved anomalies for a farmer (review queue).

    Per AGENTS.md §13: anomalous data must not be deleted, should go to review queue.
    """
    anomaly_repo = get_anomaly_repo()
    all_anomalies = anomaly_repo.get_all()

    # Filter by farmer's records
    rec_repo = get_standardized_record_repo()
    farmer_records = rec_repo.find_by(farmer_id=farmer_id)
    farmer_record_ids = {r.id for r in farmer_records}

    return [
        a for a in all_anomalies
        if a.record_id in farmer_record_ids and not a.is_resolved
    ]


# ─── Individual Check Functions ───────────────────────────────────────────────


def _check_expired(record: StandardizedRecord) -> Optional[Anomaly]:
    """Check for expired dates in record data."""
    for field_name in EXPIRY_FIELD_NAMES:
        value = record.data.get(field_name)
        if is_expired(value):
            return Anomaly(
                record_id=record.id,
                document_id=record.document_id,
                anomaly_type=AnomalyType.EXPIRED,
                severity=AnomalySeverity.CRITICAL,
                description=f"資料已過期: {field_name} = {value} (已早於今日)",
            )
    return None


def _check_future_date(record: StandardizedRecord) -> Optional[Anomaly]:
    """Check for dates unreasonably far in the future (data-entry error)."""
    for field_name in EVENT_DATE_FIELD_NAMES:
        value = record.data.get(field_name)
        years_ahead = years_from_now(value)
        if years_ahead is not None and years_ahead > FUTURE_DATE_TOLERANCE_YEARS:
            return Anomaly(
                record_id=record.id,
                document_id=record.document_id,
                anomaly_type=AnomalyType.FUTURE_DATE,
                severity=AnomalySeverity.WARNING,
                description=f"日期異常偏向未來: {field_name} = {value}",
            )
    return None


def _check_duplicate(record: StandardizedRecord, document: Optional[Document]) -> Optional[Anomaly]:
    """Check for duplicate documents (same hash, different record)."""
    if not document or not document.file_hash:
        return None

    doc_repo = get_document_repo()
    same_hash_docs = doc_repo.find_by(file_hash=document.file_hash)

    if len(same_hash_docs) > 1:
        other_ids = [d.id for d in same_hash_docs if d.id != document.id]
        return Anomaly(
            record_id=record.id,
            document_id=document.id,
            anomaly_type=AnomalyType.DUPLICATE,
            severity=AnomalySeverity.WARNING,
            description=f"與其他文件 hash 相同，疑似重複: {other_ids}",
        )
    return None


def _check_ocr_low_confidence(record: StandardizedRecord) -> Optional[Anomaly]:
    """Check for fields with very low OCR confidence (< 0.5)."""
    field_repo = get_document_field_repo()
    fields = field_repo.find_by(document_id=record.document_id)

    low_fields = [
        f for f in fields
        if f.confidence is not None and f.confidence < OCR_LOW_CONFIDENCE_THRESHOLD
    ]
    if low_fields:
        names = [f.field_name for f in low_fields]
        return Anomaly(
            record_id=record.id,
            document_id=record.document_id,
            anomaly_type=AnomalyType.OCR_LOW_CONFIDENCE,
            severity=AnomalySeverity.WARNING,
            description=(
                f"OCR 辨識信心度過低 (<{OCR_LOW_CONFIDENCE_THRESHOLD}) 的欄位: "
                f"{', '.join(names)}"
            ),
        )
    return None


def _check_missing_required(record: StandardizedRecord) -> Optional[Anomaly]:
    """Check for missing required fields, per the active rule set."""
    required = _required_fields_for(record.domain)
    missing = [f for f in required if not record.data.get(f)]

    if missing:
        return Anomaly(
            record_id=record.id,
            document_id=record.document_id,
            anomaly_type=AnomalyType.MISSING_REQUIRED_FIELD,
            severity=AnomalySeverity.CRITICAL,
            description=f"缺少必要欄位: {', '.join(missing)}",
        )
    return None


def _check_verification_failed(record: StandardizedRecord) -> Optional[Anomaly]:
    """Check if verification determined V0 (unusable)."""
    if record.source_level == SourceLevel.V0:
        return Anomaly(
            record_id=record.id,
            document_id=record.document_id,
            anomaly_type=AnomalyType.VERIFICATION_FAILED,
            severity=AnomalySeverity.CRITICAL,
            description="來源核驗失敗 (V0): 資料無法使用或確認異常",
        )
    return None


def _check_conflict(record: StandardizedRecord) -> Optional[Anomaly]:
    """
    Check for conflicting data across farmer's records.

    Demo implementation: check if same domain has records with conflicting key values.
    """
    rec_repo = get_standardized_record_repo()
    same_domain_records = rec_repo.find_by(farmer_id=record.farmer_id, domain=record.domain.value)

    if len(same_domain_records) <= 1:
        return None

    # Simple conflict: same field with different values in same domain
    # For demo, check if area or amount differs significantly
    for other in same_domain_records:
        if other.id == record.id:
            continue
        for key in ("面積", "交易金額"):
            my_val = record.data.get(key)
            other_val = other.data.get(key)
            if my_val and other_val and my_val != other_val:
                try:
                    my_num = float(my_val.replace(",", ""))
                    other_num = float(other_val.replace(",", ""))
                    if abs(my_num - other_num) / max(my_num, other_num) > 0.5:
                        return Anomaly(
                            record_id=record.id,
                            document_id=record.document_id,
                            anomaly_type=AnomalyType.CONFLICT,
                            severity=AnomalySeverity.WARNING,
                            description=f"與同領域其他紀錄矛盾: {key} 差異超過 50%",
                        )
                except (ValueError, ZeroDivisionError):
                    pass
    return None


def _check_invalid_format(record: StandardizedRecord) -> Optional[Anomaly]:
    """Check for fields that should hold dates but cannot be parsed."""
    for field_name in (*EXPIRY_FIELD_NAMES, *EVENT_DATE_FIELD_NAMES):
        value = record.data.get(field_name)
        if value and parse_date(value) is None:
            return Anomaly(
                record_id=record.id,
                document_id=record.document_id,
                anomaly_type=AnomalyType.INVALID_FORMAT,
                severity=AnomalySeverity.WARNING,
                description=f"欄位格式無法解析: {field_name} = '{value}'",
            )
    return None
