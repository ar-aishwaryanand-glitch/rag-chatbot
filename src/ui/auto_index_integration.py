"""Integration module for auto-indexing in Streamlit app."""

import streamlit as st

from src.auto_indexer import get_auto_indexer
from src.config import Config


def check_and_index_on_startup(force: bool = False) -> dict:
    """
    Check for document changes on app startup and auto-index if needed.

    Args:
        force: Force rebuild even if no changes detected

    Returns:
        Dictionary with indexing results
    """
    auto_indexer = get_auto_indexer()

    # Check if indexing is needed
    if force or auto_indexer.needs_indexing():
        with st.spinner("🔄 Auto-indexing documents..."):
            result = auto_indexer.index_documents(force_rebuild=force, verbose=False)
            return result
    else:
        return {"status": "up_to_date", "new": 0, "modified": 0, "deleted": 0}


def handle_file_upload(uploaded_files, auto_index: bool = True):
    """
    Handle file uploads with automatic indexing.

    Args:
        uploaded_files: List of uploaded file objects from st.file_uploader
        auto_index: Whether to automatically index after upload

    Returns:
        Tuple of (success: bool, message: str, result: dict)
    """
    if not uploaded_files:
        return False, "No files to upload", {}

    try:
        # Create documents directory if it doesn't exist
        docs_dir = Config.DOCUMENTS_DIR
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files
        saved_files = []
        for uploaded_file in uploaded_files:
            file_path = docs_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            saved_files.append(uploaded_file.name)

        # Auto-index if enabled
        result = {}
        if auto_index:
            auto_indexer = get_auto_indexer()
            result = auto_indexer.index_documents(force_rebuild=False, verbose=False)

        success_msg = f"✅ Uploaded {len(saved_files)} file(s):\n" + "\n".join(f"• {f}" for f in saved_files)

        if auto_index and result.get("status") == "success":
            success_msg += f"\n\n📚 Indexed: {result.get('new', 0)} new, {result.get('modified', 0)} modified"

        return True, success_msg, result

    except Exception as e:
        return False, f"Upload failed: {str(e)}", {}


def show_index_status_sidebar():
    """Display indexing status in the sidebar."""
    auto_indexer = get_auto_indexer()
    status = auto_indexer.get_status()

    with st.sidebar.expander("📊 Index Status", expanded=False):
        st.markdown(f"**Total Documents:** {status['total_indexed']}")

        if status['last_index']:
            from datetime import datetime
            try:
                last_index_dt = datetime.fromisoformat(status['last_index'])
                st.markdown(f"**Last Indexed:** {last_index_dt.strftime('%Y-%m-%d %H:%M')}")
            except (ValueError, TypeError, AttributeError):
                # Fallback if timestamp parsing fails
                st.markdown(f"**Last Indexed:** {status['last_index']}")

        pending = status['pending_changes']
        if status['needs_indexing']:
            st.warning(f"⚠️ Pending changes:\n- New: {pending['new']}\n- Modified: {pending['modified']}\n- Deleted: {pending['deleted']}")

            if st.button("🔄 Re-index Now", key="manual_reindex"):
                with st.spinner("Re-indexing..."):
                    result = auto_indexer.index_documents(force_rebuild=True, verbose=False)
                    if result["status"] == "success":
                        st.success("✅ Re-indexing complete!")
                        st.rerun()
                    else:
                        st.error("❌ Re-indexing failed")
        else:
            st.success("✅ All documents indexed")


def auto_index_uploaded_files_widget():
    """
    Streamlit widget for file upload with automatic indexing.

    This replaces the manual "Process & Index" button workflow.
    """
    st.sidebar.subheader("📁 Upload Documents")

    uploaded_files = st.sidebar.file_uploader(
        "Upload documents to index",
        type=['txt', 'md', 'pdf'],
        accept_multiple_files=True,
        help="Files will be automatically indexed when uploaded",
        key="auto_uploader"
    )

    if uploaded_files:
        # Use session state to track if we've processed these files
        if 'last_uploaded_files' not in st.session_state:
            st.session_state.last_uploaded_files = set()

        # Get current file names
        current_files = {f.name for f in uploaded_files}

        # Check if these are new files
        if current_files != st.session_state.last_uploaded_files:
            with st.sidebar.status("Processing documents...") as status:
                success, message, result = handle_file_upload(uploaded_files, auto_index=True)

                if success:
                    status.update(label="✅ Upload complete!", state="complete")
                    st.sidebar.success(message)

                    # Update session state
                    st.session_state.last_uploaded_files = current_files

                    # Clear caches
                    st.cache_resource.clear()
                    if 'agent' in st.session_state:
                        st.session_state.agent = None
                        st.session_state.agent_initialized = False

                    # Rerun to refresh
                    st.rerun()
                else:
                    status.update(label="❌ Upload failed", state="error")
                    st.sidebar.error(message)

    st.sidebar.markdown("---")
