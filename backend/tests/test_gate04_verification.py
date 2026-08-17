"""
GATE-04 Tests: Verification Service

Verifies:
- V3 source level preserved for valid official documents
- V2 for third-party verifiable documents
- V1 when OCR confidence is low
- V0 for expired documents
- V0 for invalid records
- VerificationResult has reason
- Evidence IDs preserved
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    DataDomain, Document, DocumentStatus, SourceLevel, StandardizedRecord,
)
from backend.app.repositories import (
    get_document_repo, get_document_field_repo,
    get_standardized_record_repo, get_verification_repo,
)
from backend.app.models import DocumentField
from backend.app.services.verification.verify import verify_record


def _setup_doc_and_record(
    doc_id="vdoc-1", rec_id="vrec-1", source_level=SourceLevel.V3,
    data=None, is_valid=True, fields=None,
):
    """Helper to set up a document + record for verification testing."""
    doc_repo = get_document_repo()
    rec_repo = get_standardized_record_repo()
    field_repo = get_document_field_repo()
    get_verification_repo().clear()

    # Clean up existing
    if doc_repo.exists(doc_id):
        doc_repo.delete(doc_id)
    if rec_repo.exists(rec_id):
        rec_repo.delete(rec_id)

    doc = Document(
        id=doc_id, farmer_id="farmer-ver-test", filename="test.pdf",
        domain=DataDomain.CERTIFICATION, source_level=source_level,
        status=DocumentStatus.NORMALIZED,
    )
    doc_repo.create(doc)

    record = StandardizedRecord(
        id=rec_id, document_id=doc_id, farmer_id="farmer-ver-test",
        domain=DataDomain.CERTIFICATION, record_type="certification_record",
        source_level=source_level, is_valid=is_valid,
        data=data or {"認證機構": "Test", "有效期限": "2027-06-30"},
    )
    rec_repo.create(record)

    # Add fields if specified
    if fields:
        for f in fields:
            if not field_repo.exists(f.id):
                field_repo.create(f)

    return record


class TestVerificationLevels:
    """Test V0-V3 determination."""

    def test_v3_preserved_for_valid_official(self, test_data_dir):
        record = _setup_doc_and_record(source_level=SourceLevel.V3)
        result = verify_record(record)
        assert result.source_level == SourceLevel.V3

    def test_v2_preserved_for_third_party(self, test_data_dir):
        record = _setup_doc_and_record(
            doc_id="vdoc-2", rec_id="vrec-2", source_level=SourceLevel.V2,
        )
        result = verify_record(record)
        assert result.source_level == SourceLevel.V2

    def test_v1_for_self_submitted(self, test_data_dir):
        record = _setup_doc_and_record(
            doc_id="vdoc-3", rec_id="vrec-3", source_level=SourceLevel.V1,
        )
        result = verify_record(record)
        assert result.source_level == SourceLevel.V1

    def test_downgrade_to_v0_when_expired(self, test_data_dir):
        record = _setup_doc_and_record(
            doc_id="vdoc-exp", rec_id="vrec-exp", source_level=SourceLevel.V3,
            data={"認證機構": "Test", "有效期限": "2020-01-01"},  # Past date
        )
        result = verify_record(record)
        assert result.source_level == SourceLevel.V0
        assert "過期" in result.reason

    def test_downgrade_to_v0_when_invalid(self, test_data_dir):
        record = _setup_doc_and_record(
            doc_id="vdoc-inv", rec_id="vrec-inv", source_level=SourceLevel.V2,
            is_valid=False,
        )
        result = verify_record(record)
        assert result.source_level == SourceLevel.V0
        assert "無效" in result.reason

    def test_downgrade_to_v1_when_low_confidence(self, test_data_dir):
        field_repo = get_document_field_repo()
        field_repo.clear()
        # Add a low-confidence field
        low_field = DocumentField(
            id="low-conf-field", document_id="vdoc-lc",
            field_name="test_field", raw_value="blurry", confidence=0.3,
        )
        record = _setup_doc_and_record(
            doc_id="vdoc-lc", rec_id="vrec-lc", source_level=SourceLevel.V3,
            fields=[low_field],
        )
        result = verify_record(record)
        assert result.source_level == SourceLevel.V1
        assert "信心度" in result.reason


class TestVerificationResult:
    """Test VerificationResult structure."""

    def test_result_has_reason(self, test_data_dir):
        record = _setup_doc_and_record(doc_id="vdoc-r", rec_id="vrec-r")
        result = verify_record(record)
        assert result.reason is not None
        assert len(result.reason) > 0

    def test_result_has_evidence_ids(self, test_data_dir):
        record = _setup_doc_and_record(doc_id="vdoc-e", rec_id="vrec-e")
        result = verify_record(record)
        assert len(result.evidence_ids) > 0
        assert "vdoc-e" in result.evidence_ids

    def test_result_persisted(self, test_data_dir):
        record = _setup_doc_and_record(doc_id="vdoc-p", rec_id="vrec-p")
        result = verify_record(record)
        ver_repo = get_verification_repo()
        loaded = ver_repo.get_by_id(result.id)
        assert loaded is not None
        assert loaded.record_id == record.id

    def test_no_document_yields_v0(self, test_data_dir):
        """Record with nonexistent document should be V0."""
        rec_repo = get_standardized_record_repo()
        get_verification_repo().clear()
        orphan = StandardizedRecord(
            id="vrec-orphan", document_id="nonexistent-doc",
            farmer_id="farmer-x", domain=DataDomain.IDENTITY,
            record_type="test", source_level=SourceLevel.V1,
            data={},
        )
        if rec_repo.exists(orphan.id):
            rec_repo.delete(orphan.id)
        rec_repo.create(orphan)

        result = verify_record(orphan)
        assert result.source_level == SourceLevel.V0
        assert "不存在" in result.reason
