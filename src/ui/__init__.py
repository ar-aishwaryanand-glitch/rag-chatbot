"""Streamlit UI module for RAG Agent POC.

This module provides a web-based user interface for the RAG system using Streamlit.
It wraps the existing RAG functionality without modifying the core code.

Usage:
    streamlit run run_ui.py
"""

from .streamlit_app_agent import main
from .state_manager import initialize_session_state, get_rag_chain, clear_chat_history
from .document_handler import handle_file_upload, clear_uploaded_files, get_uploaded_file_list

__all__ = [
    'main',
    'initialize_session_state',
    'get_rag_chain',
    'clear_chat_history',
    'handle_file_upload',
    'clear_uploaded_files',
    'get_uploaded_file_list',
]
