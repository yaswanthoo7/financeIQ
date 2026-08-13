"""
File validation utilities for upload processing.
"""
import os
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = set(settings.ALLOWED_EXTENSIONS.split(","))
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes

# Magic bytes for file type detection
MAGIC_BYTES = {
    b"%PDF": ".pdf",
    b"\x89PNG": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"II\x2a\x00": ".tiff",  # Little-endian TIFF
    b"MM\x00\x2a": ".tiff",  # Big-endian TIFF
    b"RIFF": ".webp",  # WebP (needs further check for WEBP signature)
}


def get_file_extension(filename: str) -> str:
    """Get the lowercase file extension including the dot."""
    return Path(filename).suffix.lower()


def detect_file_type(content_start: bytes) -> str | None:
    """Detect file type from magic bytes."""
    for magic, ext in MAGIC_BYTES.items():
        if content_start.startswith(magic):
            return ext
    return None


async def validate_upload_file(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate an uploaded file for type, size, and basic integrity.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename exists
    if not file.filename:
        return False, "No filename provided"
    
    # Check extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"Unsupported file type '{ext}'. We support: {supported}"
    
    # Read the file content to check size and magic bytes
    content = await file.read()
    await file.seek(0)  # Reset file position for later use
    
    # Check file size
    if len(content) == 0:
        return False, "The uploaded file is empty"
    
    if len(content) > MAX_FILE_SIZE:
        return False, f"File size ({len(content) / 1024 / 1024:.1f}MB) exceeds the maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB)"
    
    # Verify file content matches extension (magic bytes check)
    detected_type = detect_file_type(content[:8])
    if detected_type and detected_type != ext:
        # Special case: .jpg and .jpeg are the same
        if not (detected_type == ".jpg" and ext == ".jpeg") and not (detected_type == ".jpeg" and ext == ".jpg"):
            return False, f"File content doesn't match the extension. File appears to be {detected_type} but has extension {ext}"
    
    # Basic PDF corruption check
    if ext == ".pdf":
        if not content.startswith(b"%PDF"):
            return False, "The PDF file appears to be corrupted (invalid header)"
        # Check for PDF EOF marker (not all PDFs end exactly with %%EOF but most do)
        if b"%%EOF" not in content[-1024:]:
            # Warning but not a hard failure — some valid PDFs don't have clean EOF
            pass
    
    return True, ""


def generate_safe_filename(original_filename: str, record_id: str) -> str:
    """Generate a safe filename for storage."""
    ext = get_file_extension(original_filename)
    return f"{record_id}{ext}"
