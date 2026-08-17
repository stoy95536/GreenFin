"""
GATE-03 Tests: Field Extraction, Confirmation, and Normalization

Verifies:
- OCR run creates DocumentField records
- Document status transitions correctly
- Field confirmation works (with and without corrections)
- Normalization produces StandardizedRecord
- Date/amount/area normalization logic
- Per AGENTS.md §14: raw_value, normalized_value, confidence, source, manually_corrected
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import (
    DataDomain, Document, DocumentStatus, SourceLevel,
)
from backend.app.repositories import (
    get_document_repo, get_document_field_repo, get_standardized_record_repo,
)
from backend.app.services.documents.extraction import (
    confirm_fields, normalize_document, normalize_value, run_ocr,
)


FAKE_PDF = b"%PDF-1.4 test content"


def _create_test_document(domain=DataDomain.CERTIFICATION) -> Document:
    """Helper to create a test document."""
    doc_repo = get_document_repo()
    doc = Document(
        id="doc-test-extract",
        farmer_id="farmer-extract-test",
        filename="test_doc.pdf",
        domain=domain,
        source_level=SourceLevel.V2,
        status=DocumentStatus.UPLOADED,
    )
    # Remove if exists from previous test
    if doc_repo.exists(doc.id):
        doc_repo.delete(doc.id)
    doc_repo.create(doc)
    return doc


class TestRunOCR:
    """Test OCR execution and field creation."""

    def test_run_ocr_creates_fields(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        fields = run_ocr(doc, FAKE_PDF)
        assert len(fields) > 0

    def test_run_ocr_updates_document_status(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        run_ocr(doc, FAKE_PDF)
        updated = get_document_repo().get_by_id(doc.id)
        assert updated.status == DocumentStatus.OCR_COMPLETED

    def test_fields_have_correct_document_id(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        fields = run_ocr(doc, FAKE_PDF)
        for field in fields:
            assert field.document_id == doc.id

    def test_fields_have_confidence(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        fields = run_ocr(doc, FAKE_PDF)
        for field in fields:
            assert field.confidence is not None
            assert 0.0 <= field.confidence <= 1.0

    def test_fields_source_is_ocr(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        fields = run_ocr(doc, FAKE_PDF)
        for field in fields:
            assert field.source == "ocr"

    def test_fields_not_manually_corrected(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        fields = run_ocr(doc, FAKE_PDF)
        for field in fields:
            assert field.manually_corrected is False


class TestConfirmFields:
    """Test field confirmation with optional corrections."""

    def test_confirm_without_corrections(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        run_ocr(doc, FAKE_PDF)

        confirmed = confirm_fields(doc.id)
        assert len(confirmed) > 0

        updated_doc = get_document_repo().get_by_id(doc.id)
        assert updated_doc.status == DocumentStatus.FIELDS_CONFIRMED

    def test_confirm_with_correction(self, test_data_dir):
        get_document_field_repo().clear()
        doc = _create_test_document()
        fields = run_ocr(doc, FAKE_PDF)

        # Correct the first field
        first_field_id = fields[0].id
        confirmed = confirm_fields(doc.id, corrections={first_field_id: "corrected value"})

        corrected = next(f for f in confirmed if f.id == first_field_id)
        assert corrected.raw_value == "corrected value"
        assert corrected.manually_corrected is True


class TestNormalization:
    """Test value normalization logic."""

    def test_normalize_date_slash(self):
        assert normalize_value("日期", "2026/03/15") == "2026-03-15"

    def test_normalize_date_dot(self):
        assert normalize_value("日期", "2026.3.5") == "2026-03-05"

    def test_normalize_date_dash(self):
        assert normalize_value("日期", "2026-12-31") == "2026-12-31"

    def test_normalize_amount_ntd(self):
        assert normalize_value("金額", "NT$125,000") == "125000"

    def test_normalize_amount_dollar(self):
        assert normalize_value("金額", "$85,000") == "85000"

    def test_normalize_amount_with_decimals(self):
        assert normalize_value("金額", "NT$1,234.56") == "1234.56"

    def test_normalize_area_hectares(self):
        assert normalize_value("面積", "2.5 公頃") == "2.5"

    def test_normalize_plain_text(self):
        assert normalize_value("名稱", "  慈心基金會  ") == "慈心基金會"

    def test_normalize_empty_string(self):
        assert normalize_value("any", "") == ""


class TestNormalizeDocument:
    """Test full document normalization to StandardizedRecord."""

    def test_normalize_creates_record(self, test_data_dir):
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()
        doc = _create_test_document()
        run_ocr(doc, FAKE_PDF)
        confirm_fields(doc.id)

        record = normalize_document(doc.id)
        assert record is not None
        assert record.document_id == doc.id
        assert record.farmer_id == doc.farmer_id
        assert record.domain == DataDomain.CERTIFICATION

    def test_normalize_updates_document_status(self, test_data_dir):
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()
        doc = _create_test_document()
        run_ocr(doc, FAKE_PDF)
        confirm_fields(doc.id)
        normalize_document(doc.id)

        updated = get_document_repo().get_by_id(doc.id)
        assert updated.status == DocumentStatus.NORMALIZED

    def test_normalize_persists_record(self, test_data_dir):
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()
        doc = _create_test_document()
        run_ocr(doc, FAKE_PDF)
        confirm_fields(doc.id)
        record = normalize_document(doc.id)

        rec_repo = get_standardized_record_repo()
        loaded = rec_repo.get_by_id(record.id)
        assert loaded is not None
        assert loaded.record_type == "certification_record"

    def test_normalize_fields_have_normalized_values(self, test_data_dir):
        get_document_field_repo().clear()
        get_standardized_record_repo().clear()
        doc = _create_test_document()
        run_ocr(doc, FAKE_PDF)
        confirm_fields(doc.id)
        normalize_document(doc.id)

        field_repo = get_document_field_repo()
        fields = field_repo.find_by(document_id=doc.id)
        for field in fields:
            assert field.normalized_value is not None

    def test_normalize_nonexistent_document(self, test_data_dir):
        result = normalize_document("nonexistent-doc-id")
        assert result is None
