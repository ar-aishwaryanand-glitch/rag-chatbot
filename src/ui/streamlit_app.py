"""Main Streamlit application for RAG Agent POC.

This is the main entry point for the Streamlit web UI. It orchestrates
all components and provides the chat interface.
"""

import streamlit as st
from typing import Dict

# Import UI modules
from .state_manager import (
    initialize_session_state,
    get_rag_chain,
    is_initialized,
    get_error_message,
    clear_error,
    config_override
)
from .components import (
    render_sidebar,
    render_chat_message,
    render_welcome_message,
    show_error,
    show_info
)

# Import Config for overrides
from src.config import Config


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="RAG Chat Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "RAG Chat Assistant - Powered by Google Gemini and Streamlit"
        }
    )


def initialize_rag_system():
    """
    Initialize the RAG system if not already initialized.

    Returns:
        True if initialized successfully, False otherwise
    """
    if is_initialized():
        return True

    try:
        with st.spinner("🚀 Initializing RAG system..."):
            rag_chain = get_rag_chain()

            if rag_chain is None:
                error = get_error_message()
                show_error(f"Initialization failed: {error or 'Unknown error'}")
                return False

            show_info("System initialized successfully!")
            return True

    except Exception as e:
        show_error(f"Initialization error: {str(e)}")
        import traceback
        with st.expander("Show detailed error"):
            st.code(traceback.format_exc())
        return False


def handle_user_input(prompt: str):
    """
    Handle user question and generate response.

    Args:
        prompt: User's question
    """
    if not prompt or not prompt.strip():
        return

    # Add user message to history
    st.session_state.messages.append({
        'role': 'user',
        'content': prompt
    })

    # Get RAG chain
    rag_chain = st.session_state.get('rag_chain')

    if rag_chain is None:
        show_error("RAG system not initialized")
        return

    # Generate response with config overrides
    try:
        with st.spinner("🔍 Searching documents and generating answer..."):
            # Apply configuration overrides
            overrides = st.session_state.get('config_overrides', {})

            with config_override(
                TOP_K_RESULTS=overrides.get('top_k', Config.TOP_K_RESULTS),
                LLM_TEMPERATURE=overrides.get('temperature', Config.LLM_TEMPERATURE),
                CHUNK_SIZE=overrides.get('chunk_size', Config.CHUNK_SIZE),
                CHUNK_OVERLAP=overrides.get('chunk_overlap', Config.CHUNK_OVERLAP)
            ):
                # Call RAG chain
                result = rag_chain.ask(prompt)

        # Add assistant response to history
        st.session_state.messages.append({
            'role': 'assistant',
            'content': result['answer'],
            'sources': result.get('sources', [])
        })

    except Exception as e:
        error_msg = str(e)
        show_error(f"Error processing question: {error_msg}")

        # Add error message to chat
        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"Sorry, I encountered an error: {error_msg}",
            'sources': []
        })

        # Show detailed error in expander
        import traceback
        with st.expander("Show detailed error"):
            st.code(traceback.format_exc())


def render_main_chat():
    """Render the main chat interface."""
    st.title("💬 Chat with Your Documents")

    # Initialize system if needed
    if not is_initialized():
        initialized = initialize_rag_system()
        if not initialized:
            st.stop()

    # Check for errors
    error = get_error_message()
    if error:
        show_error(error)
        clear_error()

    # Show welcome message if no chat history
    if not st.session_state.messages:
        render_welcome_message()
    else:
        # Render chat history
        for message in st.session_state.messages:
            render_chat_message(message)

    # Chat input (always shown at bottom)
    if prompt := st.chat_input("Ask a question about your documents...", key='chat_input'):
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response with spinner
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Process input (this adds to session state)
                handle_user_input(prompt)

                # Get the last assistant message to display
                if st.session_state.messages:
                    last_msg = st.session_state.messages[-1]
                    if last_msg['role'] == 'assistant':
                        st.markdown(last_msg['content'])

                        # Show sources
                        if last_msg.get('sources'):
                            sources = last_msg['sources']
                            with st.expander(f"📖 View {len(sources)} source(s)", expanded=False):
                                for i, source in enumerate(sources, 1):
                                    from .components import render_source_card
                                    render_source_card(source, i)

        # Rerun to update the chat display properly
        st.rerun()


def main():
    """Main application entry point."""
    # Configure page
    configure_page()

    # Initialize session state
    initialize_session_state()

    # Render layout
    render_sidebar()
    render_main_chat()


if __name__ == "__main__":
    main()
