"""Reusable UI components for Streamlit app.

This module contains all the UI widgets and rendering functions used
in the Streamlit interface.
"""

import streamlit as st
from typing import Dict, List, Optional
from .state_manager import trigger_rebuild, clear_chat_history, update_config, get_config
from .document_handler import (
    handle_file_upload,
    clear_uploaded_files,
    get_uploaded_file_list,
    delete_uploaded_file,
    get_upload_count
)

# Import Config for defaults
from src.config import Config


def render_chat_message(message: Dict):
    """
    Render a chat message bubble.

    Args:
        message: Dictionary with 'role', 'content', and optional 'sources'
    """
    role = message['role']
    content = message['content']

    with st.chat_message(role):
        st.markdown(content)

        # Render sources for assistant messages
        if role == 'assistant' and message.get('sources'):
            sources = message['sources']
            with st.expander(f"📖 View {len(sources)} source(s)", expanded=False):
                for i, source in enumerate(sources, 1):
                    render_source_card(source, i)


def render_source_card(source: Dict, index: int):
    """
    Render a source information card.

    Args:
        source: Dictionary with 'source', 'topic', and 'content'
        index: Source number for display
    """
    st.markdown(f"**Source {index}: {source['source']}**")
    st.caption(f"Topic: {source['topic']}")

    # Content preview in a text area (scrollable)
    st.text_area(
        f"Content Preview",
        value=source['content'],
        height=100,
        disabled=True,
        label_visibility="collapsed",
        key=f"source_{index}_{hash(source['content'][:50])}"
    )

    if index < 10:  # Reasonable limit
        st.markdown("---")


def render_settings_panel():
    """
    Render settings control panel in sidebar.

    Allows runtime adjustment of:
    - LLM temperature
    - Top-K retrieval results
    - Chunk size (requires rebuild)
    - Chunk overlap (requires rebuild)
    """
    st.sidebar.subheader("⚙️ Settings")

    # Get current config values
    current_temp = get_config('temperature')
    current_topk = get_config('top_k')
    current_chunk_size = get_config('chunk_size')
    current_chunk_overlap = get_config('chunk_overlap')

    # LLM Settings
    with st.sidebar.expander("🤖 LLM Settings", expanded=True):
        temp = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(current_temp) if current_temp else 0.7,
            step=0.1,
            help="Controls randomness. Lower = more deterministic, Higher = more creative",
            key='temp_slider'
        )

    # Retrieval Settings
    with st.sidebar.expander("🔍 Retrieval Settings", expanded=True):
        top_k = st.slider(
            "Top-K Results",
            min_value=1,
            max_value=10,
            value=int(current_topk) if current_topk else 3,
            help="Number of document chunks to retrieve per query",
            key='topk_slider'
        )

    # Chunking Settings (requires rebuild)
    with st.sidebar.expander("✂️ Chunking Settings", expanded=False):
        st.caption("⚠️ Changes require vector store rebuild")

        chunk_size = st.number_input(
            "Chunk Size (characters)",
            min_value=200,
            max_value=2000,
            value=int(current_chunk_size) if current_chunk_size else 800,
            step=100,
            help="Size of document chunks for embedding",
            key='chunk_size_input'
        )

        chunk_overlap = st.number_input(
            "Chunk Overlap (characters)",
            min_value=0,
            max_value=500,
            value=int(current_chunk_overlap) if current_chunk_overlap else 100,
            step=50,
            help="Character overlap between consecutive chunks",
            key='chunk_overlap_input'
        )

    # Detect changes and apply
    changes_made = False

    if temp != current_temp:
        update_config('temperature', temp)
        changes_made = True

    if top_k != current_topk:
        update_config('top_k', top_k)
        changes_made = True

    # Check if chunking settings changed (requires rebuild)
    chunking_changed = False

    if chunk_size != current_chunk_size:
        update_config('chunk_size', chunk_size)
        changes_made = True
        chunking_changed = True

    if chunk_overlap != current_chunk_overlap:
        update_config('chunk_overlap', chunk_overlap)
        changes_made = True
        chunking_changed = True

    if chunking_changed and changes_made:
        st.sidebar.warning("⚠️ Chunking settings changed. Rebuild vector store to apply.")
        if st.sidebar.button("🔄 Rebuild Now"):
            trigger_rebuild()
            st.rerun()


def render_upload_section():
    """
    Render file upload section in sidebar.

    Provides:
    - File uploader widget
    - Upload button
    - List of uploaded files
    - Clear uploads button
    """
    st.sidebar.subheader("📤 Upload Documents")

    uploaded_files = st.sidebar.file_uploader(
        "Choose files",
        type=['txt', 'md', 'pdf'],
        accept_multiple_files=True,
        help="Upload PDF, TXT, or MD files (max 10MB each)",
        key='file_uploader'
    )

    if uploaded_files:
        st.sidebar.info(f"📎 {len(uploaded_files)} file(s) selected")

        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("✅ Upload", use_container_width=True):
                with st.spinner("Processing files..."):
                    success = handle_file_upload(uploaded_files)

                    if success:
                        st.sidebar.success("Upload complete!")
                        st.sidebar.info("💡 Rebuild vector store to index new documents")
                        # Trigger rebuild prompt
                        st.session_state.rebuild_pending = True
                        st.rerun()

        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.rerun()

    # Show uploaded files list
    file_list = get_uploaded_file_list()

    if file_list:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Uploaded Files ({len(file_list)}):**")

        for file_info in file_list:
            col1, col2 = st.sidebar.columns([3, 1])

            with col1:
                st.caption(f"📄 {file_info['name']}")
                st.caption(f"   {file_info['size_mb']}")

            with col2:
                if st.button("🗑️", key=f"delete_{file_info['name']}", help="Delete file"):
                    delete_uploaded_file(file_info['name'])
                    st.rerun()

        # Clear all button
        if st.sidebar.button("🗑️ Clear All Uploads", use_container_width=True):
            clear_uploaded_files()
            st.rerun()


def render_vector_store_info():
    """
    Render vector store information and controls.

    Shows:
    - Initialization status
    - Document count
    - Rebuild button
    - Clear chat button
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗄️ Vector Store")

    # Check initialization status
    if st.session_state.get('initialized', False):
        st.sidebar.success("✅ System Initialized")

        # Document mode indicator
        mode = st.session_state.get('document_mode', 'sample')
        mode_label = "Sample Documents" if mode == 'sample' else "Custom Documents"
        st.sidebar.info(f"📚 Mode: {mode_label}")

        # Show upload count in custom mode
        if mode == 'custom':
            upload_count = get_upload_count()
            if upload_count > 0:
                st.sidebar.info(f"📤 Uploaded: {upload_count} file(s)")

    else:
        st.sidebar.warning("⚠️ Not Initialized")

    # Rebuild button
    rebuild_col, clear_col = st.sidebar.columns(2)

    with rebuild_col:
        if st.button("🔄 Rebuild", use_container_width=True, help="Rebuild vector store from documents"):
            trigger_rebuild()
            st.rerun()

    with clear_col:
        if st.button("🗑️ Clear Chat", use_container_width=True, help="Clear chat history"):
            clear_chat_history()
            st.rerun()

    # Show rebuild pending warning
    if st.session_state.get('rebuild_pending', False):
        st.sidebar.warning("⚠️ Rebuild pending - vector store will be recreated on next query")


def render_mode_selector():
    """
    Render document mode selector in sidebar.

    Allows switching between:
    - Sample Documents (built-in AI/ML topics)
    - Custom Documents (user-provided files)
    """
    current_mode = st.session_state.get('document_mode', 'sample')

    mode = st.sidebar.radio(
        "📚 Document Source",
        options=['sample', 'custom'],
        format_func=lambda x: "📖 Sample Documents" if x == 'sample' else "📁 Custom Documents",
        index=0 if current_mode == 'sample' else 1,
        help="Choose between built-in sample documents or your own custom documents",
        key='mode_radio'
    )

    # Detect mode change
    if mode != current_mode:
        st.session_state.document_mode = mode
        st.session_state.initialized = False
        trigger_rebuild()
        st.rerun()

    # Show upload section only in custom mode
    if mode == 'custom':
        render_upload_section()


def render_sidebar():
    """
    Render complete sidebar with all sections.

    Includes:
    - App title
    - Mode selector
    - Upload section (if custom mode)
    - Settings panel
    - Vector store info
    """
    with st.sidebar:
        st.title("🤖 RAG Assistant")
        st.markdown("Retrieval-Augmented Generation")
        st.markdown("---")

        # Mode selector (includes upload section if custom mode)
        render_mode_selector()

        st.markdown("---")

        # Settings panel
        render_settings_panel()

        # Vector store info
        render_vector_store_info()

        # Footer
        st.markdown("---")
        st.caption("Built with Streamlit & Google Gemini")


def render_welcome_message():
    """
    Render welcome message when chat is empty.
    """
    st.markdown("""
    ### Welcome to RAG Chat Assistant! 👋

    Ask questions about your documents and I'll retrieve relevant information to answer them.

    **How it works:**
    1. Your question is converted to a vector embedding
    2. Similar document chunks are retrieved from the vector database
    3. Google Gemini generates an answer based on the retrieved context
    4. Sources are shown for transparency

    **Tips:**
    - Ask specific questions for better results
    - Check the source viewer to see retrieved context
    - Adjust settings in the sidebar for different behavior
    - Switch between Sample and Custom document modes

    **Get started:** Type your question below!
    """)


def show_error(error_msg: str):
    """
    Display error message with formatting.

    Args:
        error_msg: Error message to display
    """
    st.error(f"❌ **Error:** {error_msg}")


def show_info(info_msg: str):
    """
    Display info message with formatting.

    Args:
        info_msg: Info message to display
    """
    st.info(f"ℹ️ {info_msg}")


def show_success(success_msg: str):
    """
    Display success message with formatting.

    Args:
        success_msg: Success message to display
    """
    st.success(f"✅ {success_msg}")
