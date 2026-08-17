"""
Document, DocumentField, and StandardizedRecord models.

Represents the evidence pipeline:
  Original Document → OCR → Fields → Normalized Record
"""

from typing import Optional

from pydantic import Field

from backend.app.models.base import EntityBase
from backend.app.models.enums import DataDomain, DocumentStatus, SourceLevel


class Document(EntityBase):
    """An uploaded original document (evidence)."""

    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    filename: str = Field(..., description="Original filename")
    file_hash: Optional[str] = Field(default=None, description="SHA-256 hash for duplicate detection")
    file_path: Optional[str] = Field(default=None, description="Storage path")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    domain: DataDomain = Field(..., description="Data domain this document belongs to")
    source_level: SourceLevel = Field(default=SourceLevel.V1, description="Initial source level")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Processing status")
    upload_note: Optional[str] = Field(default=None, description="Farmer's note about this document")


class DocumentField(EntityBase):
    """A field extracted from a document (via OCR or manual input)."""

    document_id: str = Field(..., description="Reference to Document.id")
    field_name: str = Field(..., description="Field name (e.g. 發票金額)")
    raw_value: Optional[str] = Field(default=None, description="Raw OCR value")
    normalized_value: Optional[str] = Field(default=None, description="Normalized value")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="OCR confidence 0-1")
    source: str = Field(default="ocr", description="Source: ocr, manual, api")
    manually_corrected: bool = Field(default=False, description="Whether human corrected this field")


class StandardizedRecord(EntityBase):
    """A normalized, structured record derived from document fields."""

    document_id: str = Field(..., description="Reference to Document.id")
    farmer_id: str = Field(..., description="Reference to FarmerProfile.id")
    domain: DataDomain = Field(..., description="Data domain")
    record_type: str = Field(..., description="Record type (e.g. income_record, certification)")
    data: dict = Field(default_factory=dict, description="Structured record data (key-value)")
    source_level: SourceLevel = Field(default=SourceLevel.V1, description="Verified source level")
    is_valid: bool = Field(default=True, description="Whether this record passed validation")
