"""Document upload and processing for Streamlit UI.

This module handles file uploads, validation, sanitization, and
management of uploaded documents.
"""

import os
from pathlib import Path
from typing import List, Tuple, Dict
import streamlit as st
import re

# Upload directory (separate from manual documents)
PROJECT_ROOT = Path(__file__).parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploaded"


def ensure_upload_dir():
    """Ensure upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.

    Removes or replaces problematic characters that could cause issues
    in filesystems or be used maliciously.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for storage
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')

    # Keep only alphanumeric, dots, hyphens, underscores, and spaces
    safe_name = re.sub(r'[^\w\s.-]', '', filename)

    # Collapse multiple spaces
    safe_name = re.sub(r'\s+', ' ', safe_name)

    # Trim whitespace
    safe_name = safe_name.strip()

    # Ensure not empty
    if not safe_name:
        safe_name = "unnamed_file.txt"

    return safe_name


def validate_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate uploaded file.

    Checks:
    - File type (PDF, TXT, MD)
    - File size (max 10MB)
    - Non-empty file

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if file passes all validations
        - error_message: Empty string if valid, error description if invalid
    """
    # Check file type
    allowed_extensions = ['.txt', '.md', '.pdf']
    file_ext = Path(uploaded_file.name).suffix.lower()

    if file_ext not in allowed_extensions:
        return False, f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"

    # Check file size (max 10MB)
    max_size_bytes = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size_bytes:
        size_mb = uploaded_file.size / (1024 * 1024)
        return False, f"File too large: {size_mb:.1f}MB (max 10MB)"

    # Check if empty
    if uploaded_file.size == 0:
        return False, "File is empty (0 bytes)"

    # Check filename length
    if len(uploaded_file.name) > 200:
        return False, "Filename too long (max 200 characters)"

    return True, ""


def handle_file_upload(uploaded_files: List) -> bool:
    """
    Handle file upload and save to disk.

    Validates each file, sanitizes filenames, and saves to upload directory.
    Updates session state with upload results.

    Args:
        uploaded_files: List of Streamlit UploadedFile objects

    Returns:
        True if at least one file was successfully uploaded, False otherwise
    """
    ensure_upload_dir()

    success_count = 0
    errors = []
    saved_paths = []

    for uploaded_file in uploaded_files:
        # Validate
        is_valid, error_msg = validate_file(uploaded_file)
        if not is_valid:
            errors.append(f"**{uploaded_file.name}**: {error_msg}")
            continue

        # Sanitize filename
        safe_name = sanitize_filename(uploaded_file.name)
        file_path = UPLOAD_DIR / safe_name

        # Check if already exists
        if file_path.exists():
            # Add timestamp to make unique
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
                counter += 1

        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            success_count += 1
            saved_paths.append(str(file_path))

        except Exception as e:
            errors.append(f"**{uploaded_file.name}**: Failed to save - {str(e)}")

    # Update session state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    st.session_state.uploaded_files.extend(saved_paths)

    # Display results
    if success_count > 0:
        st.success(f"✅ Successfully uploaded {success_count} file(s)")

    if errors:
        st.error("**Upload Errors:**")
        for error in errors:
            st.write(f"- {error}")

    return success_count > 0


def clear_uploaded_files():
    """
    Remove all uploaded files.

    Deletes all files in the upload directory and clears session state.
    """
    if not UPLOAD_DIR.exists():
        return

    deleted_count = 0

    for file in UPLOAD_DIR.glob("*"):
        if file.is_file():
            try:
                file.unlink()
                deleted_count += 1
            except Exception as e:
                st.warning(f"Could not delete {file.name}: {e}")

    # Clear session state
    st.session_state.uploaded_files = []

    if deleted_count > 0:
        st.success(f"🗑️ Deleted {deleted_count} uploaded file(s)")


def get_uploaded_file_list() -> List[Dict]:
    """
    Get list of uploaded files with metadata.

    Returns:
        List of dictionaries with file information:
        - name: Filename
        - path: Full file path
        - size: File size in bytes
        - size_mb: File size in MB (formatted)
        - type: File extension
    """
    if not UPLOAD_DIR.exists():
        return []

    files = []

    for file in sorted(UPLOAD_DIR.glob("*")):
        if file.is_file():
            stat = file.stat()
            size_mb = stat.st_size / (1024 * 1024)

            files.append({
                'name': file.name,
                'path': str(file),
                'size': stat.st_size,
                'size_mb': f"{size_mb:.2f} MB",
                'type': file.suffix
            })

    return files


def get_upload_count() -> int:
    """Get count of uploaded files."""
    return len(get_uploaded_file_list())


def delete_uploaded_file(filename: str) -> bool:
    """
    Delete a specific uploaded file.

    Args:
        filename: Name of file to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        st.warning(f"File not found: {filename}")
        return False

    try:
        file_path.unlink()

        # Remove from session state
        if 'uploaded_files' in st.session_state:
            st.session_state.uploaded_files = [
                f for f in st.session_state.uploaded_files
                if f != str(file_path)
            ]

        st.success(f"✅ Deleted {filename}")
        return True

    except Exception as e:
        st.error(f"❌ Error deleting {filename}: {e}")
        return False


def load_documents_for_ui():
    """
    Load documents from both persistent and uploaded directories.

    This combines documents from:
    - data/documents/ (persistent user documents)
    - data/uploaded/ (session-based uploads)

    Returns:
        List of document dictionaries
    """
    from src.document_loader import load_all_documents

    docs = []

    # Load persistent documents
    try:
        persistent_docs = load_all_documents(directory="data/documents")
        docs.extend(persistent_docs)
    except Exception as e:
        st.warning(f"Could not load persistent documents: {e}")

    # Load uploaded documents
    try:
        if UPLOAD_DIR.exists():
            uploaded_docs = load_all_documents(directory=str(UPLOAD_DIR))
            docs.extend(uploaded_docs)
    except Exception as e:
        st.warning(f"Could not load uploaded documents: {e}")

    return docs
