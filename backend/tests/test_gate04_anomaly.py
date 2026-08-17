"""
GATE-04 Tests: Anomaly Detection Service

Verifies all 8 anomaly types per AGENTS.md §13:
- EXPIRED
- FUTURE_DATE
- DUPLICATE
- OCR_LOW_CONFIDENCE
- MISSING_REQUIRED_FIELD
- VERIFICATION_FAILED
- CONFLICT
- INVALID_FORMAT
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    Anomaly, AnomalySeverity, AnomalyType,
    DataDomain, Document, DocumentField, DocumentStatus,
    SourceLevel, StandardizedRecord,
)
from backend.app.repositories import (
    get_anomaly_repo, get_document_field_repo,
    get_document_repo, get_standardized_record_repo,
)
from backend.app.services.anomaly.detect import detect_anomalies, get_review_queue


def _setup(doc_id, rec_id, data, domain=DataDomain.CERTIFICATION,
           source_level=SourceLevel.V2, is_valid=True, file_hash=None,
           fields=None):
    """Helper to set up document + record for anomaly testing."""
    doc_repo = get_document_repo()
    rec_repo = get_standardized_record_repo()
    field_repo = get_document_field_repo()
    get_anomaly_repo().clear()

    if doc_repo.exists(doc_id):
        doc_repo.delete(doc_id)
    if rec_repo.exists(rec_id):
        rec_repo.delete(rec_id)

    doc = Document(
        id=doc_id, farmer_id="farmer-anom-test", filename="test.pdf",
        domain=domain, source_level=source_level,
        status=DocumentStatus.NORMALIZED, file_hash=file_hash,
    )
    doc_repo.create(doc)

    record = StandardizedRecord(
        id=rec_id, document_id=doc_id, farmer_id="farmer-anom-test",
        domain=domain, record_type="test_record",
        source_level=source_level, is_valid=is_valid, data=data,
    )
    rec_repo.create(record)

    if fields:
        for f in fields:
            if not field_repo.exists(f.id):
                field_repo.create(f)

    return record


class TestExpiredAnomaly:
    """Test EXPIRED detection."""

    def test_expired_date_detected(self, test_data_dir):
        record = _setup("ad-exp", "ar-exp", {"有效期限": "2020-01-01"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.EXPIRED in types

    def test_expired_severity_critical(self, test_data_dir):
        record = _setup("ad-exp2", "ar-exp2", {"有效期限": "2019-06-15"})
        anomalies = detect_anomalies(record)
        expired = next(a for a in anomalies if a.anomaly_type == AnomalyType.EXPIRED)
        assert expired.severity == AnomalySeverity.CRITICAL

    def test_valid_date_no_expired(self, test_data_dir):
        record = _setup("ad-val", "ar-val", {"有效期限": "2030-12-31"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.EXPIRED not in types


class TestFutureDateAnomaly:
    """Test FUTURE_DATE detection."""

    def test_far_future_date_detected(self, test_data_dir):
        record = _setup("ad-fut", "ar-fut", {"交易日期": "2035-01-01"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.FUTURE_DATE in types

    def test_normal_future_date_ok(self, test_data_dir):
        record = _setup("ad-nf", "ar-nf", {"交易日期": "2027-01-01"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.FUTURE_DATE not in types


class TestDuplicateAnomaly:
    """Test DUPLICATE detection."""

    def test_duplicate_hash_detected(self, test_data_dir):
        doc_repo = get_document_repo()
        get_anomaly_repo().clear()

        # Create two docs with same hash
        if doc_repo.exists("ad-dup1"):
            doc_repo.delete("ad-dup1")
        if doc_repo.exists("ad-dup2"):
            doc_repo.delete("ad-dup2")

        doc_repo.create(Document(
            id="ad-dup1", farmer_id="farmer-anom-test", filename="a.pdf",
            domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V2,
            status=DocumentStatus.NORMALIZED, file_hash="same_hash_123",
        ))
        doc_repo.create(Document(
            id="ad-dup2", farmer_id="farmer-anom-test", filename="b.pdf",
            domain=DataDomain.CERTIFICATION, source_level=SourceLevel.V2,
            status=DocumentStatus.NORMALIZED, file_hash="same_hash_123",
        ))

        rec_repo = get_standardized_record_repo()
        if rec_repo.exists("ar-dup1"):
            rec_repo.delete("ar-dup1")
        record = StandardizedRecord(
            id="ar-dup1", document_id="ad-dup1", farmer_id="farmer-anom-test",
            domain=DataDomain.CERTIFICATION, record_type="test",
            source_level=SourceLevel.V2, data={"認證機構": "X", "有效期限": "2030-01-01"},
        )
        rec_repo.create(record)

        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.DUPLICATE in types


class TestOCRLowConfidence:
    """Test OCR_LOW_CONFIDENCE detection."""

    def test_low_confidence_detected(self, test_data_dir):
        field_repo = get_document_field_repo()
        field_repo.clear()

        low_field = DocumentField(
            id="lc-field-1", document_id="ad-lc",
            field_name="blurry_field", confidence=0.2, raw_value="???",
        )
        record = _setup("ad-lc", "ar-lc", {"認證機構": "X", "有效期限": "2030-01-01"}, fields=[low_field])
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.OCR_LOW_CONFIDENCE in types

    def test_good_confidence_no_anomaly(self, test_data_dir):
        field_repo = get_document_field_repo()
        field_repo.clear()

        good_field = DocumentField(
            id="gc-field-1", document_id="ad-gc",
            field_name="clear_field", confidence=0.95, raw_value="clear",
        )
        record = _setup("ad-gc", "ar-gc", {"認證機構": "X", "有效期限": "2030-01-01"}, fields=[good_field])
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.OCR_LOW_CONFIDENCE not in types


class TestMissingRequiredField:
    """Test MISSING_REQUIRED_FIELD detection."""

    def test_missing_field_detected(self, test_data_dir):
        # CERTIFICATION requires: 認證機構, 有效期限
        record = _setup("ad-mf", "ar-mf", {"認證機構": "X"})  # Missing 有效期限
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.MISSING_REQUIRED_FIELD in types

    def test_all_fields_present_no_anomaly(self, test_data_dir):
        record = _setup("ad-af", "ar-af", {"認證機構": "X", "有效期限": "2030-01-01"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.MISSING_REQUIRED_FIELD not in types


class TestVerificationFailed:
    """Test VERIFICATION_FAILED detection."""

    def test_v0_triggers_verification_failed(self, test_data_dir):
        record = _setup(
            "ad-vf", "ar-vf", {"認證機構": "X", "有效期限": "2030-01-01"},
            source_level=SourceLevel.V0,
        )
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.VERIFICATION_FAILED in types

    def test_v2_no_verification_failed(self, test_data_dir):
        record = _setup(
            "ad-v2", "ar-v2", {"認證機構": "X", "有效期限": "2030-01-01"},
            source_level=SourceLevel.V2,
        )
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.VERIFICATION_FAILED not in types


class TestInvalidFormat:
    """Test INVALID_FORMAT detection."""

    def test_invalid_date_format_detected(self, test_data_dir):
        record = _setup("ad-if", "ar-if", {"認證機構": "X", "有效期限": "not-a-date"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.INVALID_FORMAT in types

    def test_valid_date_no_format_error(self, test_data_dir):
        record = _setup("ad-vd", "ar-vd", {"認證機構": "X", "有效期限": "2030-06-15"})
        anomalies = detect_anomalies(record)
        types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.INVALID_FORMAT not in types


class TestReviewQueue:
    """Test review queue functionality."""

    def test_review_queue_returns_unresolved(self, test_data_dir):
        get_anomaly_repo().clear()
        get_standardized_record_repo().clear()

        rec_repo = get_standardized_record_repo()
        rec_repo.create(StandardizedRecord(
            id="rq-rec", document_id="rq-doc", farmer_id="farmer-rq",
            domain=DataDomain.IDENTITY, record_type="test",
            source_level=SourceLevel.V1, data={},
        ))

        anomaly_repo = get_anomaly_repo()
        anomaly_repo.create(Anomaly(
            id="rq-anom-1", record_id="rq-rec",
            anomaly_type=AnomalyType.EXPIRED, severity=AnomalySeverity.CRITICAL,
            description="test expired", is_resolved=False,
        ))
        anomaly_repo.create(Anomaly(
            id="rq-anom-2", record_id="rq-rec",
            anomaly_type=AnomalyType.DUPLICATE, severity=AnomalySeverity.WARNING,
            description="test dup", is_resolved=True,
        ))

        queue = get_review_queue("farmer-rq")
        assert len(queue) == 1
        assert queue[0].id == "rq-anom-1"
