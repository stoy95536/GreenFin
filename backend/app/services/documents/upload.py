"""
Document Upload Service.

Orchestrates the upload flow:
1. Validate file type and size
2. Compute hash
3. Check for duplicates
4. Store file
5. Create Document record
6. Trigger OCR (async in future, synchronous mock for demo)
"""

from pathlib import Path
from typing import Optional

from backend.app.models import Document, DataDomain, DocumentStatus, SourceLevel
from backend.app.repositories import get_document_repo
from backend.app.services import audit
from backend.app.services.documents.storage import (
    UPLOADS_DIR,
    compute_file_hash,
    save_file,
    validate_file_size,
    validate_file_type,
)


class UploadError(Exception):
    """Upload validation or processing error."""

    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code


def upload_document(
    content: bytes,
    filename: str,
    mime_type: str,
    farmer_id: str,
    domain: DataDomain,
    source_level: SourceLevel = SourceLevel.V1,
    upload_note: Optional[str] = None,
    uploads_dir: Optional[Path] = None,
) -> Document:
    """
    Process a document upload.

    Args:
        content: Raw file bytes.
        filename: Original filename.
        mime_type: MIME type of the file.
        farmer_id: ID of the farmer uploading.
        domain: Data domain this document belongs to.
        source_level: Initial source level (default V1 for self-submitted).
        upload_note: Optional farmer note.
        uploads_dir: Override for testing.

    Returns:
        Created Document entity.

    Raises:
        UploadError: If validation fails.
    """
    # Step 1: Validate file type
    if not validate_file_type(mime_type):
        raise UploadError(
            f"不支援的檔案類型: {mime_type}。支援: PDF, JPEG, PNG, WEBP, XLSX",
            "INVALID_FILE_TYPE",
        )

    # Step 2: Validate file size
    if not validate_file_size(len(content)):
        raise UploadError(
            f"檔案大小超過限制 (最大 10MB)",
            "FILE_TOO_LARGE",
        )

    # Step 3: Compute hash
    file_hash = compute_file_hash(content)

    # Step 4: Check for duplicates
    doc_repo = get_document_repo()
    existing = doc_repo.find_by(file_hash=file_hash, farmer_id=farmer_id)
    if existing:
        raise UploadError(
            f"重複檔案: 此檔案已上傳過 (document_id: {existing[0].id})",
            "DUPLICATE_FILE",
        )

    # Step 5: Store file
    file_path = save_file(content, farmer_id, filename, uploads_dir=uploads_dir)

    # Step 6: Create document record
    document = Document(
        farmer_id=farmer_id,
        filename=filename,
        file_hash=file_hash,
        file_path=file_path,
        mime_type=mime_type,
        domain=domain,
        source_level=source_level,
        status=DocumentStatus.UPLOADED,
        upload_note=upload_note,
    )
    doc_repo.create(document)

    audit.document_uploaded(
        document_id=document.id,
        farmer_id=farmer_id,
        filename=filename,
        domain=domain.value,
    )

    return document
