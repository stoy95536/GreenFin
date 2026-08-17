"""
GATE-03 Tests: Document Upload & Validation

Verifies:
- Valid file upload succeeds
- Invalid MIME type is rejected
- File too large is rejected
- Duplicate file hash is rejected
- Document record is persisted
- File is stored on disk
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import DataDomain, DocumentStatus, SourceLevel
from backend.app.services.documents.storage import (
    compute_file_hash,
    validate_file_size,
    validate_file_type,
)
from backend.app.services.documents.upload import UploadError, upload_document
from backend.app.repositories import get_document_repo


FAKE_PDF_CONTENT = b"%PDF-1.4 fake content for testing"
FAKE_JPG_CONTENT = b"\xff\xd8\xff\xe0 fake jpeg content"


class TestFileValidation:
    """Test file type and size validation."""

    def test_valid_pdf_type(self):
        assert validate_file_type("application/pdf") is True

    def test_valid_jpeg_type(self):
        assert validate_file_type("image/jpeg") is True

    def test_valid_png_type(self):
        assert validate_file_type("image/png") is True

    def test_invalid_type_text(self):
        assert validate_file_type("text/plain") is False

    def test_invalid_type_exe(self):
        assert validate_file_type("application/x-executable") is False

    def test_valid_file_size(self):
        assert validate_file_size(1024) is True

    def test_file_size_zero(self):
        assert validate_file_size(0) is False

    def test_file_size_too_large(self):
        assert validate_file_size(11 * 1024 * 1024) is False

    def test_file_size_at_limit(self):
        assert validate_file_size(10 * 1024 * 1024) is True


class TestFileHash:
    """Test hash computation."""

    def test_hash_is_deterministic(self):
        h1 = compute_file_hash(FAKE_PDF_CONTENT)
        h2 = compute_file_hash(FAKE_PDF_CONTENT)
        assert h1 == h2

    def test_different_content_different_hash(self):
        h1 = compute_file_hash(FAKE_PDF_CONTENT)
        h2 = compute_file_hash(FAKE_JPG_CONTENT)
        assert h1 != h2

    def test_hash_is_sha256_length(self):
        h = compute_file_hash(FAKE_PDF_CONTENT)
        assert len(h) == 64  # SHA-256 hex digest


class TestUploadService:
    """Test the upload_document service function."""

    def test_valid_upload_creates_document(self, test_data_dir, tmp_path):
        doc_repo = get_document_repo()
        doc_repo.clear()

        doc = upload_document(
            content=FAKE_PDF_CONTENT,
            filename="test_cert.pdf",
            mime_type="application/pdf",
            farmer_id="farmer-test-1",
            domain=DataDomain.CERTIFICATION,
            uploads_dir=tmp_path,
        )

        assert doc.id is not None
        assert doc.filename == "test_cert.pdf"
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.domain == DataDomain.CERTIFICATION
        assert doc.file_hash is not None
        doc_repo.clear()

    def test_upload_persists_to_repo(self, test_data_dir, tmp_path):
        doc_repo = get_document_repo()
        doc_repo.clear()

        doc = upload_document(
            content=FAKE_PDF_CONTENT,
            filename="persist.pdf",
            mime_type="application/pdf",
            farmer_id="farmer-test-2",
            domain=DataDomain.TRANSACTION,
            uploads_dir=tmp_path,
        )

        loaded = doc_repo.get_by_id(doc.id)
        assert loaded is not None
        assert loaded.filename == "persist.pdf"
        doc_repo.clear()

    def test_upload_invalid_type_raises(self, test_data_dir, tmp_path):
        with pytest.raises(UploadError) as exc_info:
            upload_document(
                content=b"not a valid file",
                filename="malware.exe",
                mime_type="application/x-executable",
                farmer_id="farmer-test-3",
                domain=DataDomain.IDENTITY,
                uploads_dir=tmp_path,
            )
        assert exc_info.value.error_code == "INVALID_FILE_TYPE"

    def test_upload_duplicate_hash_raises(self, test_data_dir, tmp_path):
        doc_repo = get_document_repo()
        doc_repo.clear()

        # First upload succeeds
        upload_document(
            content=FAKE_PDF_CONTENT,
            filename="original.pdf",
            mime_type="application/pdf",
            farmer_id="farmer-dup",
            domain=DataDomain.CERTIFICATION,
            uploads_dir=tmp_path,
        )

        # Second upload with same content raises
        with pytest.raises(UploadError) as exc_info:
            upload_document(
                content=FAKE_PDF_CONTENT,
                filename="copy.pdf",
                mime_type="application/pdf",
                farmer_id="farmer-dup",
                domain=DataDomain.CERTIFICATION,
                uploads_dir=tmp_path,
            )
        assert exc_info.value.error_code == "DUPLICATE_FILE"
        doc_repo.clear()

    def test_upload_stores_file_on_disk(self, test_data_dir, tmp_path):
        doc_repo = get_document_repo()
        doc_repo.clear()

        doc = upload_document(
            content=FAKE_PDF_CONTENT,
            filename="stored.pdf",
            mime_type="application/pdf",
            farmer_id="farmer-store",
            domain=DataDomain.GREEN_ACTION,
            uploads_dir=tmp_path,
        )

        # Check file exists on disk
        stored_path = tmp_path / doc.file_path
        assert stored_path.exists()
        assert stored_path.read_bytes() == FAKE_PDF_CONTENT
        doc_repo.clear()

    def test_upload_source_level_default_v1(self, test_data_dir, tmp_path):
        doc_repo = get_document_repo()
        doc_repo.clear()

        doc = upload_document(
            content=FAKE_JPG_CONTENT,
            filename="photo.jpg",
            mime_type="image/jpeg",
            farmer_id="farmer-sl",
            domain=DataDomain.GREEN_ACTION,
            uploads_dir=tmp_path,
        )

        assert doc.source_level == SourceLevel.V1
        doc_repo.clear()
