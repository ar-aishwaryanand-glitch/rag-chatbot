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
from .url_handler import handle_url_submission

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


def render_url_input_section():
    """
    Render URL input section in sidebar.

    Allows users to:
    - Enter URLs to fetch content from
    - Automatically extract and save web content
    - Index content in vector store
    """
    st.sidebar.subheader("🌐 Add from URL")

    url_input = st.sidebar.text_input(
        "Enter URL",
        placeholder="https://example.com/article",
        help="Paste a URL to fetch and index its content",
        key='url_input'
    )

    if url_input and url_input.strip():
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("✅ Fetch & Index", use_container_width=True, key='fetch_url_button'):
                with st.spinner("Fetching content..."):
                    success = handle_url_submission(url_input.strip())

                    if success:
                        # Clear the input by triggering rerun
                        st.session_state.rebuild_pending = True
                        st.rerun()

        with col2:
            if st.button("❌ Clear", use_container_width=True, key='clear_url_button'):
                st.rerun()

    # Show fetched URLs count
    url_count = len(st.session_state.get('url_sources', []))
    if url_count > 0:
        st.sidebar.info(f"🔗 {url_count} URL(s) indexed")


def render_session_manager():
    """
    Render session management controls.

    Allows users to:
    - Create new sessions
    - View past sessions
    - Restore previous conversations
    - Delete sessions
    """
    try:
        from src.database.session_manager import SessionManager
    except ImportError:
        return  # PostgreSQL not available

    # Initialize session manager
    if 'session_manager' not in st.session_state:
        try:
            st.session_state.session_manager = SessionManager()
        except Exception:
            return  # Failed to initialize

    session_mgr = st.session_state.session_manager

    # Only show if PostgreSQL is enabled
    if not session_mgr.is_available():
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Session Management")

    # Get current session ID
    current_session = st.session_state.get('current_session_id')

    # Session selector
    sessions = session_mgr.list_sessions(limit=20)

    if sessions:
        session_options = {
            f"{s['title']} ({s['message_count']} messages)": s['session_id']
            for s in sessions
        }
        session_options = {"➕ New Session": None, **session_options}

        selected = st.sidebar.selectbox(
            "Select Session",
            options=list(session_options.keys()),
            key='session_selector'
        )

        selected_id = session_options[selected]

        # Handle session change
        if selected_id and selected_id != current_session:
            # Restore session
            restored = session_mgr.restore_session(selected_id)
            if restored:
                st.session_state.current_session_id = selected_id
                st.session_state.messages = restored['conversation']
                st.success(f"✅ Restored: {restored['session']['title']}")
                st.rerun()

        elif not selected_id and current_session:
            # Create new session
            new_id = session_mgr.create_session(title="New Conversation")
            if new_id:
                st.session_state.current_session_id = new_id
                st.session_state.messages = []
                st.success("✅ New session created")
                st.rerun()

    else:
        # No sessions yet
        if st.sidebar.button("➕ Start First Session", use_container_width=True):
            new_id = session_mgr.create_session(title="First Conversation")
            if new_id:
                st.session_state.current_session_id = new_id
                st.session_state.messages = []
                st.rerun()

    # Session info
    if current_session:
        st.sidebar.info(f"📝 Session: {current_session[:8]}...")

        # Rename session
        with st.sidebar.expander("⚙️ Session Options"):
            new_title = st.text_input(
                "Rename Session",
                placeholder="Enter new title",
                key='session_rename_input'
            )

            if st.button("💾 Save Title", key='save_title_button'):
                if new_title:
                    session_mgr.update_session_title(current_session, new_title)
                    st.success("✅ Title updated")
                    st.rerun()

            # Delete session
            if st.button("🗑️ Delete Session", key='delete_session_button', type='secondary'):
                if st.session_state.get('confirm_delete'):
                    session_mgr.delete_session(current_session)
                    st.session_state.current_session_id = None
                    st.session_state.messages = []
                    st.session_state.confirm_delete = False
                    st.success("✅ Session deleted")
                    st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning("⚠️ Click again to confirm deletion")


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
        st.sidebar.markdown("---")
        render_url_input_section()


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

        # Session management (if PostgreSQL enabled)
        render_session_manager()

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


# ==============================================================================
# POLICY ENGINE UI COMPONENTS
# ==============================================================================

def render_policy_dashboard(agent_executor):
    """
    Render policy engine dashboard in sidebar.

    Args:
        agent_executor: AgentExecutorV3 instance with policy engine
    """
    if not agent_executor or not hasattr(agent_executor, 'policy_engine'):
        return

    policy_engine = agent_executor.policy_engine
    if not policy_engine or not policy_engine.is_enabled():
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("🛡️ Policy Engine")

    with st.sidebar.expander("📊 Policy Status", expanded=False):
        # Get active policies
        policies = agent_executor.get_active_policies()

        if policies:
            # Group by policy type
            policy_types = {}
            for policy in policies:
                ptype = policy['policy_type']
                if ptype not in policy_types:
                    policy_types[ptype] = []
                policy_types[ptype].append(policy)

            # Display by type
            for ptype, type_policies in policy_types.items():
                enabled_count = sum(1 for p in type_policies if p['enabled'])
                st.markdown(f"**{ptype.replace('_', ' ').title()}:** {enabled_count}/{len(type_policies)} active")

            st.caption(f"Total: {len(policies)} policies loaded")
        else:
            st.info("No policies configured")

    with st.sidebar.expander("⚠️ Policy Violations", expanded=False):
        # Get recent violations
        session_id = st.session_state.get('current_session_id')
        violations = agent_executor.get_policy_violations(session_id=session_id, limit=10)

        if violations:
            st.warning(f"{len(violations)} violation(s) detected")

            for v in violations[:5]:  # Show last 5
                st.markdown(f"""
                **{v['policy_type']}**
                {v['details']}
                *Action: {v['action_taken']}*
                """)
                st.caption(f"ID: {v['violation_id'][:8]}... | {v['timestamp']}")
                st.markdown("---")
        else:
            st.success("No violations")


def render_policy_settings(agent_executor):
    """
    Render policy engine settings panel.

    Args:
        agent_executor: AgentExecutorV3 instance with policy engine
    """
    if not agent_executor or not hasattr(agent_executor, 'policy_engine'):
        st.info("Policy engine not available")
        return

    policy_engine = agent_executor.policy_engine
    if not policy_engine or not policy_engine.is_enabled():
        st.info("Policy engine is disabled. Set USE_POLICY_ENGINE=true in .env to enable.")
        return

    st.subheader("🛡️ Policy Engine Settings")

    # Get all policies
    policies = agent_executor.get_active_policies()

    if not policies:
        st.warning("No policies configured. Add policies in `src/policy/default_policies.yaml`")
        return

    # Policy type filter
    policy_type = st.selectbox(
        "Filter by Type",
        options=["all"] + list(set(p['policy_type'] for p in policies)),
        format_func=lambda x: x.replace('_', ' ').title() if x != "all" else "All Policies"
    )

    filtered_policies = policies if policy_type == "all" else [
        p for p in policies if p['policy_type'] == policy_type
    ]

    # Display policies
    for policy in filtered_policies:
        with st.expander(f"**{policy['name']}** ({'✅ Enabled' if policy['enabled'] else '❌ Disabled'})", expanded=False):
            st.markdown(f"**Description:** {policy['description']}")
            st.markdown(f"**Type:** {policy['policy_type'].replace('_', ' ').title()}")
            st.markdown(f"**Action:** {policy['action'].replace('_', ' ').title()}")
            st.markdown(f"**Priority:** {policy['priority']}")
            st.caption(f"Rule ID: {policy['rule_id']}")


def render_policy_violations_table(agent_executor, session_id: str = None):
    """
    Render table of policy violations.

    Args:
        agent_executor: AgentExecutorV3 instance
        session_id: Optional session ID filter
    """
    if not agent_executor or not hasattr(agent_executor, 'policy_engine'):
        return

    violations = agent_executor.get_policy_violations(session_id=session_id, limit=50)

    if not violations:
        st.info("No policy violations recorded")
        return

    st.subheader("⚠️ Policy Violations")

    # Create DataFrame for table display
    import pandas as pd

    df = pd.DataFrame([
        {
            'Time': v['timestamp'][:19],
            'Type': v['policy_type'].replace('_', ' ').title(),
            'Action': v['action_taken'].replace('_', ' ').title(),
            'Details': v['details'][:50] + '...' if len(v['details']) > 50 else v['details']
        }
        for v in violations
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Download violations as CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Violations CSV",
        data=csv,
        file_name="policy_violations.csv",
        mime="text/csv"
    )


# ==============================================================================
# TASK QUEUE UI COMPONENTS
# ==============================================================================

def render_task_queue_dashboard():
    """Render task queue dashboard in sidebar."""
    try:
        from src.queue import get_task_queue

        task_queue = get_task_queue()

        if not task_queue.is_available():
            return

        st.sidebar.markdown("---")
        st.sidebar.subheader("📦 Task Queue")

        with st.sidebar.expander("📊 Queue Status", expanded=False):
            stats = task_queue.get_queue_stats()

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Pending", stats.pending_tasks)
                st.metric("Running", stats.running_tasks)

            with col2:
                st.metric("Completed", stats.completed_tasks)
                st.metric("Failed", stats.failed_tasks)

            st.metric("Active Workers", stats.active_workers)

            if stats.total_tasks > 0:
                st.metric(
                    "Success Rate",
                    f"{stats.success_rate * 100:.1f}%"
                )

    except ImportError:
        pass  # Queue not available
    except Exception as e:
        st.sidebar.error(f"Queue error: {e}")


def render_task_monitor(agent_executor):
    """
    Render task monitoring interface.

    Args:
        agent_executor: AgentExecutorV3 instance
    """
    st.subheader("📦 Task Queue Monitor")

    try:
        from src.queue import get_task_queue, TaskStatus

        task_queue = get_task_queue()

        if not task_queue.is_available():
            st.info("Task queue is disabled. Set USE_REDIS_QUEUE=true in .env to enable.")
            return

        # Queue statistics
        st.markdown("### 📊 Queue Statistics")

        stats = task_queue.get_queue_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("⏳ Pending", stats.pending_tasks)
        with col2:
            st.metric("▶️ Running", stats.running_tasks)
        with col3:
            st.metric("✅ Completed", stats.completed_tasks)
        with col4:
            st.metric("❌ Failed", stats.failed_tasks)

        col5, col6 = st.columns(2)

        with col5:
            st.metric("👷 Active Workers", stats.active_workers)
        with col6:
            if stats.total_tasks > 0:
                st.metric("📈 Success Rate", f"{stats.success_rate * 100:.1f}%")

        # Task list
        st.markdown("---")
        st.markdown("### 📋 Task List")

        status_filter = st.selectbox(
            "Filter by Status",
            options=["all", "pending", "running", "completed", "failed"],
            format_func=lambda x: x.replace('_', ' ').title()
        )

        # Get tasks
        if status_filter == "all":
            tasks = task_queue.list_tasks(limit=50)
        else:
            status_enum = TaskStatus(status_filter)
            tasks = task_queue.list_tasks(status=status_enum, limit=50)

        if tasks:
            import pandas as pd

            df = pd.DataFrame([
                {
                    'Task ID': t.task_id[:8] + '...',
                    'Type': t.task_type.value.replace('_', ' ').title(),
                    'Status': t.status.value.title(),
                    'Priority': t.priority.name,
                    'Created': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Worker': t.worker_id[:8] + '...' if t.worker_id else '-'
                }
                for t in tasks
            ])

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No tasks found")

    except ImportError:
        st.error("Task queue module not available")
    except Exception as e:
        st.error(f"Error: {e}")
