"""
File Storage Service.

Handles saving uploaded files to disk and computing file hashes.
Files are stored in backend/uploads/ organized by farmer_id.
"""

import hashlib
from pathlib import Path
from typing import Optional

# Default uploads directory
UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"

# Allowed MIME types for upload
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
}

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def validate_file_type(mime_type: str) -> bool:
    """Check if MIME type is allowed."""
    return mime_type in ALLOWED_MIME_TYPES


def validate_file_size(size: int) -> bool:
    """Check if file size is within limit."""
    return 0 < size <= MAX_FILE_SIZE


def save_file(content: bytes, farmer_id: str, filename: str, uploads_dir: Optional[Path] = None) -> str:
    """
    Save file to disk.

    Args:
        content: File bytes.
        farmer_id: Farmer who uploaded the file.
        filename: Original filename.
        uploads_dir: Override uploads directory (for testing).

    Returns:
        Relative storage path.
    """
    base_dir = uploads_dir or UPLOADS_DIR
    farmer_dir = base_dir / farmer_id
    farmer_dir.mkdir(parents=True, exist_ok=True)

    # Add hash prefix to avoid filename collisions
    file_hash = compute_file_hash(content)[:8]
    safe_filename = f"{file_hash}_{filename}"
    file_path = farmer_dir / safe_filename

    file_path.write_bytes(content)
    return str(file_path.relative_to(base_dir))


def get_file_path(relative_path: str, uploads_dir: Optional[Path] = None) -> Path:
    """Get absolute path for a stored file."""
    base_dir = uploads_dir or UPLOADS_DIR
    return base_dir / relative_path
