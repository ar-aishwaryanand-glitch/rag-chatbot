"""Session state management for Streamlit UI.

This module handles Streamlit session state initialization, RAG chain caching,
and state management operations.
"""

import streamlit as st
from typing import Optional
from contextlib import contextmanager

# Import from parent src module
from src.system_init import initialize_system
from src.config import Config


def initialize_session_state():
    """Initialize all session state variables with defaults."""
    defaults = {
        # RAG System State
        'initialized': False,
        'rag_chain': None,
        'initialization_mode': 'sample',

        # Chat State
        'messages': [],

        # Document Management
        'uploaded_files': [],
        'custom_docs_count': 0,

        # Configuration Overrides (runtime settings)
        'config_overrides': {
            'temperature': Config.LLM_TEMPERATURE,
            'top_k': Config.TOP_K_RESULTS,
            'chunk_size': Config.CHUNK_SIZE,
            'chunk_overlap': Config.CHUNK_OVERLAP,
        },

        # UI State
        'rebuild_pending': False,
        'processing': False,
        'error_message': None,
        'document_mode': 'sample',  # 'sample' or 'custom'
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def get_rag_chain_cached(mode: str, rebuild: bool = False):
    """
    Get or create RAG chain with caching.

    This function is cached with @st.cache_resource to prevent re-initialization
    on every page interaction. The cache is cleared when mode changes or rebuild is requested.

    Args:
        mode: 'sample' or 'custom' - determines document source
        rebuild: Force rebuild of vector store

    Returns:
        Initialized RAGChain instance
    """
    use_documents = (mode == 'custom')
    return initialize_system(rebuild_index=rebuild, use_documents=use_documents)


def get_rag_chain():
    """
    Get or initialize RAG chain from session state.

    Returns:
        RAGChain instance or None if initialization fails
    """
    try:
        mode = st.session_state.get('document_mode', 'sample')
        rebuild = st.session_state.get('rebuild_pending', False)

        # Get cached RAG chain
        rag_chain = get_rag_chain_cached(mode, rebuild)

        # Reset rebuild flag
        if rebuild:
            st.session_state.rebuild_pending = False

        # Update initialization state
        st.session_state.initialized = True
        st.session_state.rag_chain = rag_chain

        return rag_chain

    except Exception as e:
        st.session_state.error_message = str(e)
        st.session_state.initialized = False
        return None


def clear_chat_history():
    """Clear all chat messages from session state."""
    st.session_state.messages = []


def reset_system():
    """
    Reset entire system state.

    Clears all caches and reinitializes session state.
    """
    # Clear Streamlit caches
    st.cache_resource.clear()
    st.cache_data.clear()

    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Reinitialize
    initialize_session_state()


def trigger_rebuild():
    """Mark that vector store needs to be rebuilt."""
    st.session_state.rebuild_pending = True
    st.cache_resource.clear()  # Clear cached RAG chain


def update_config(key: str, value):
    """
    Update configuration override.

    Args:
        key: Configuration key (e.g., 'temperature', 'top_k')
        value: New value
    """
    if 'config_overrides' not in st.session_state:
        st.session_state.config_overrides = {}

    st.session_state.config_overrides[key] = value


def get_config(key: str):
    """
    Get configuration value (override or default).

    Args:
        key: Configuration key

    Returns:
        Configuration value
    """
    if 'config_overrides' in st.session_state:
        return st.session_state.config_overrides.get(key)

    # Fallback to Config defaults
    return getattr(Config, key.upper(), None)


@contextmanager
def config_override(**overrides):
    """
    Context manager for temporarily overriding configuration values.

    Usage:
        with config_override(TOP_K_RESULTS=5, LLM_TEMPERATURE=0.5):
            result = rag_chain.ask(question)

    Args:
        **overrides: Configuration key-value pairs to override
    """
    original_values = {}

    try:
        # Save original values and apply overrides
        for key, value in overrides.items():
            if hasattr(Config, key):
                original_values[key] = getattr(Config, key)
                setattr(Config, key, value)

        yield

    finally:
        # Restore original values
        for key, value in original_values.items():
            setattr(Config, key, value)


def is_initialized() -> bool:
    """Check if RAG system is initialized."""
    return st.session_state.get('initialized', False)


def get_error_message() -> Optional[str]:
    """Get current error message, if any."""
    return st.session_state.get('error_message')


def clear_error():
    """Clear error message."""
    st.session_state.error_message = None
