"""Enhanced Streamlit application with Phase 3 Agent Integration.

This version uses AgentExecutorV3 with memory and self-reflection capabilities,
providing a more intelligent and context-aware chat experience.

NOW WITH MODERN UI! 🎨
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from typing import Dict, Any
from datetime import datetime
import atexit

# Import UI modules
from src.ui.state_manager import (
    initialize_session_state,
    get_error_message,
    clear_error
)
from src.ui.components import (
    show_error
)

# Import modern UI components
from src.ui.styles import get_modern_css, get_custom_header_html
from src.ui.enhanced_components import (
    render_enhanced_chat_message,
    render_typing_indicator,
    render_stats_dashboard,
    render_enhanced_sidebar_header,
    render_quick_actions,
    render_suggested_prompts,
    render_welcome_cards,
    render_stats_cards
)

# Import Config
from src.config import Config

# Import agent components
from src.system_init import initialize_system
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.agent.tool_registry import ToolRegistry
from src.agent.tools import (
    RAGTool,
    WebSearchTool,
    CalculatorTool,
    CodeExecutorTool,
    FileOpsTool,
    DocumentManagementTool,
    WebAgentTool,
    NewsApiTool
)


def configure_page():
    """Configure Streamlit page settings with modern styling."""
    st.set_page_config(
        page_title="RAG Agent Assistant - Modern UI",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "RAG Agent Assistant with Memory & Self-Reflection - Phase 3 + Modern UI"
        }
    )

    # Apply modern CSS styling
    st.markdown(get_modern_css(), unsafe_allow_html=True)


def initialize_agent_session_state():
    """Initialize agent-specific session state variables."""
    # Initialize base session state first
    initialize_session_state()

    # Agent-specific state
    agent_defaults = {
        'agent': None,
        'agent_initialized': False,
        'enable_memory': True,
        'enable_reflection': True,
        'show_agent_details': True,
        'show_memory_context': False,
        'show_reflection_insights': False,
        'session_queries': 0,
        'conversation_thread_id': None,  # NEW: Track conversation thread for memory
    }

    for key, value in agent_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Generate a unique conversation thread ID if not exists
    if st.session_state.conversation_thread_id is None:
        import uuid
        st.session_state.conversation_thread_id = f"streamlit_{uuid.uuid4().hex[:12]}"


@st.cache_resource
@st.cache_resource(show_spinner=False)
def _get_rag_chain():
    """Cached RAG chain initialization."""
    return initialize_system(rebuild_index=False, use_documents=True)


def initialize_agent_system(enable_memory: bool = True, enable_reflection: bool = True):
    """
    Initialize the agent system with all tools.

    Args:
        enable_memory: Enable memory features
        enable_reflection: Enable self-reflection features

    Returns:
        AgentExecutorV3 instance
    """
    # Get cached RAG system (loads faster on subsequent calls)
    rag_chain = _get_rag_chain()
    vector_store_manager = rag_chain.vector_store_manager

    # Register tools (lightweight, fast operations)
    tool_registry = ToolRegistry()

    # Core tools (always available, fast to initialize)
    tools_to_register = [
        RAGTool(rag_chain),
        WebSearchTool(max_results=3),
        CalculatorTool(),
        FileOpsTool(Config.FILE_OPS_WORKSPACE),
        DocumentManagementTool(vector_store_manager)
    ]

    # Code executor (optional, fast)
    if Config.CODE_EXECUTOR_ENABLED:
        tools_to_register.append(CodeExecutorTool(timeout=10))

    # Web Agent (slow - only add if Playwright available)
    try:
        web_agent = WebAgentTool(timeout=30, max_pages=5)
        if web_agent.available:
            tools_to_register.append(web_agent)
    except Exception:
        # Playwright not available - skip (expected on Streamlit Cloud)
        pass

    # Get LLM for tools that need it
    llm = rag_chain.llm

    # News API tool (optional, needs API key)
    try:
        news_api = NewsApiTool(llm_client=llm, filter_irrelevant=True)
        if news_api.available:
            tools_to_register.append(news_api)
    except Exception:
        # NewsAPI not available - skip
        pass

    for tool in tools_to_register:
        tool_registry.register(tool)
    agent = AgentExecutorV3(
        llm,
        tool_registry,
        Config,
        enable_memory=enable_memory,
        enable_reflection=enable_reflection
    )

    return agent


def get_or_create_agent():
    """Get or create the agent instance (lazy initialization on first use)."""
    if st.session_state.get('agent') is None:
        # Show status during first-time initialization
        status_placeholder = st.empty()
        status_placeholder.info("🚀 Initializing AI agent... (first time only, ~3-5 seconds)")

        try:
            agent = initialize_agent_system(
                enable_memory=st.session_state.enable_memory,
                enable_reflection=st.session_state.enable_reflection
            )
            st.session_state.agent = agent
            st.session_state.agent_initialized = True

            # Clear status message
            status_placeholder.empty()

        except Exception as e:
            status_placeholder.empty()
            show_error(f"Failed to initialize agent: {str(e)}")
            import traceback
            with st.expander("Show error details"):
                st.code(traceback.format_exc())
            return None

    return st.session_state.agent


def render_agent_sidebar():
    """Render enhanced sidebar with agent controls and modern styling."""
    # Modern sidebar header
    with st.sidebar:
        render_enhanced_sidebar_header()

    # Agent Features Toggle - Enhanced with expander
    with st.sidebar.expander("🧠 AI Features", expanded=True):
        st.markdown("##### Enable Advanced Capabilities")

        enable_memory = st.checkbox(
            "🧠 Memory System",
            value=st.session_state.enable_memory,
            help="Agent remembers conversation history and learns from past sessions",
            key="enable_memory_checkbox"
        )

        enable_reflection = st.checkbox(
            "🔄 Self-Reflection",
            value=st.session_state.enable_reflection,
            help="Agent evaluates its actions and learns from experience",
            key="enable_reflection_checkbox"
        )

        # Check if settings changed
        if (enable_memory != st.session_state.enable_memory or
            enable_reflection != st.session_state.enable_reflection):
            st.session_state.enable_memory = enable_memory
            st.session_state.enable_reflection = enable_reflection
            st.session_state.agent = None  # Force reinit
            st.session_state.agent_initialized = False
            st.cache_resource.clear()
            st.success("✅ Settings updated! Agent will restart.", icon="🔄")
            st.rerun()

    st.sidebar.markdown("---")

    # Display Options - Enhanced with expander
    with st.sidebar.expander("📊 Display Settings", expanded=False):
        st.markdown("##### Customize Information Display")

        st.session_state.show_agent_details = st.checkbox(
            "🔍 Agent Reasoning",
            value=st.session_state.show_agent_details,
            help="Display tool selection and execution details",
            key="show_details_checkbox"
        )

        st.session_state.show_memory_context = st.checkbox(
            "💭 Memory Context",
            value=st.session_state.show_memory_context,
            help="Display conversation memory and context",
            key="show_memory_checkbox"
        )

        st.session_state.show_reflection_insights = st.checkbox(
            "🧠 Learning Insights",
            value=st.session_state.show_reflection_insights,
            help="Display self-reflection and learning statistics",
            key="show_reflection_checkbox"
        )

    st.sidebar.markdown("---")

    # Session Stats - Enhanced visualization
    if st.session_state.agent_initialized and st.session_state.agent:
        with st.sidebar.expander("📈 Session Statistics", expanded=True):
            agent = st.session_state.agent

            # Create stats grid
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "📝 Queries",
                    st.session_state.session_queries,
                    delta="+1" if st.session_state.session_queries > 0 else None
                )

            with col2:
                if agent.enable_reflection and agent.learning_module:
                    perf = agent.learning_module.get_overall_performance()
                    success_rate = perf.get('success_rate', 0)
                    st.metric(
                        "✅ Success",
                        f"{success_rate:.0%}",
                        delta=None
                    )
                else:
                    st.metric("✅ Success", "N/A")

            # Additional metrics in two columns for better layout
            if agent.enable_reflection and agent.learning_module:
                perf = agent.learning_module.get_overall_performance()

                col3, col4 = st.columns(2)

                with col3:
                    st.metric(
                        "🛠️ Tools",
                        perf.get('unique_tools_used', 0),
                        help="Number of different tools used"
                    )

                with col4:
                    st.metric(
                        "⭐ Quality",
                        f"{perf.get('avg_quality_score', 0):.1f}/5",
                        help="Average quality score"
                    )

            st.markdown("---")

            # End Session Button - Enhanced
            if st.button("🏁 End & Save Session", use_container_width=True, type="primary"):
                summary = agent.end_session()
                st.success("✅ Session saved to memory!", icon="💾")

                with st.expander("📋 View Session Summary"):
                    st.json(summary)

    st.sidebar.markdown("---")

    # Document Upload Section - Enhanced
    with st.sidebar.expander("📁 Document Upload", expanded=False):
        st.markdown("##### Add Documents to Knowledge Base")

        uploaded_files = st.file_uploader(
            "Drag and drop files here",
            type=['txt', 'md', 'pdf', 'docx'],
            accept_multiple_files=True,
            help="Upload .txt, .md, .pdf, or .docx files to add to the knowledge base",
            label_visibility="collapsed"
        )

        if uploaded_files:
            # Show file count
            st.info(f"📚 {len(uploaded_files)} file(s) selected", icon="✨")

            # Show file names
            with st.expander("View selected files"):
                for file in uploaded_files:
                    st.markdown(f"• {file.name} ({file.size / 1024:.1f} KB)")

            if st.button("📤 Process & Index Documents", use_container_width=True, type="primary"):
                with st.status("Processing documents...", expanded=True) as status:
                    try:
                        from pathlib import Path

                        # Create documents directory if it doesn't exist
                        docs_dir = Path("data/documents")
                        docs_dir.mkdir(parents=True, exist_ok=True)

                        saved_files = []
                        for idx, uploaded_file in enumerate(uploaded_files, 1):
                            # Save file
                            file_path = docs_dir / uploaded_file.name
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            saved_files.append(uploaded_file.name)
                            status.update(
                                label=f"📄 Saving {idx}/{len(uploaded_files)}: {uploaded_file.name}...",
                                state="running"
                            )

                        status.update(label="🔄 Re-indexing vector store...", state="running")

                        # Force rebuild of vector store with new documents
                        from src.system_init import initialize_system
                        initialize_system(rebuild_index=True, use_documents=True)  # side effect only

                        # Clear cache and reinitialize agent with new vector store
                        st.cache_resource.clear()
                        st.session_state.agent = None
                        st.session_state.agent_initialized = False

                        status.update(label="✅ Upload complete!", state="complete")
                        st.success(f"✅ Successfully indexed {len(saved_files)} document(s)!", icon="🎉")
                        st.rerun()

                    except Exception as e:
                        status.update(label="❌ Upload failed", state="error")
                        st.error(f"Upload failed: {str(e)}", icon="🚨")

    # Confluence Integration Section
    from src.confluence_loader import is_confluence_configured, get_confluence_loader
    if is_confluence_configured():
        with st.sidebar.expander("🔗 Confluence Import", expanded=False):
            st.markdown("##### Import from Confluence")

            # Space key input
            space_key = st.text_input(
                "Space Key",
                value=Config.CONFLUENCE_SPACE_KEY or "",
                help="Confluence space key (e.g., 'DOCS', 'ENGINEERING')",
                placeholder="Enter space key..."
            )

            # Fetch options
            fetch_option = st.radio(
                "Fetch mode",
                options=["All pages from space", "Search pages", "Specific page ID"],
                help="Choose how to fetch pages from Confluence"
            )

            search_query = None
            page_id = None
            limit = 50

            if fetch_option == "Search pages":
                search_query = st.text_input(
                    "Search query",
                    placeholder="Enter search terms...",
                    help="Search for pages containing these terms"
                )
            elif fetch_option == "Specific page ID":
                page_id = st.text_input(
                    "Page ID",
                    placeholder="Enter Confluence page ID...",
                    help="The numeric page ID from Confluence"
                )
            else:
                limit = st.slider("Max pages to fetch", 10, 100, 50)

            if st.button("📥 Fetch from Confluence", use_container_width=True, type="secondary"):
                if not space_key and fetch_option != "Specific page ID":
                    st.error("Please enter a space key", icon="⚠️")
                elif fetch_option == "Search pages" and not search_query:
                    st.error("Please enter a search query", icon="⚠️")
                elif fetch_option == "Specific page ID" and not page_id:
                    st.error("Please enter a page ID", icon="⚠️")
                else:
                    with st.status("Fetching from Confluence...", expanded=True) as status:
                        try:
                            loader = get_confluence_loader()

                            if fetch_option == "Specific page ID":
                                status.update(label=f"📄 Fetching page {page_id}...", state="running")
                                documents = loader.load_documents(page_ids=[page_id])
                            elif fetch_option == "Search pages":
                                status.update(label=f"🔍 Searching for '{search_query}'...", state="running")
                                documents = loader.load_documents(
                                    space_key=space_key,
                                    search_query=search_query,
                                    limit=limit
                                )
                            else:
                                status.update(label=f"📚 Fetching pages from {space_key}...", state="running")
                                documents = loader.load_documents(
                                    space_key=space_key,
                                    limit=limit
                                )

                            if not documents:
                                status.update(label="⚠️ No pages found", state="complete")
                                st.warning("No pages found matching your criteria", icon="⚠️")
                            else:
                                status.update(label=f"🔄 Indexing {len(documents)} pages...", state="running")

                                # Add documents to vector store
                                from src.system_init import initialize_system
                                components = initialize_system(rebuild_index=False, use_documents=False)
                                if components and 'document_manager' in components:
                                    doc_manager = components['document_manager']

                                    # Chunk and index the documents
                                    all_chunks = []
                                    for doc in documents:
                                        chunks = doc_manager.embedding_manager.chunk_documents([doc])
                                        all_chunks.extend(chunks)

                                    if all_chunks:
                                        doc_manager.add_documents(all_chunks)
                                        doc_manager.save()

                                        # Clear cache for fresh agent
                                        st.cache_resource.clear()
                                        st.session_state.agent = None
                                        st.session_state.agent_initialized = False

                                        status.update(label="✅ Import complete!", state="complete")
                                        st.success(
                                            f"✅ Imported {len(documents)} pages ({len(all_chunks)} chunks)!",
                                            icon="🎉"
                                        )
                                        st.rerun()
                                    else:
                                        status.update(label="⚠️ No content to index", state="complete")
                                        st.warning("Pages had no content to index", icon="⚠️")

                        except Exception as e:
                            status.update(label="❌ Import failed", state="error")
                            st.error(f"Confluence import failed: {str(e)}", icon="🚨")
    else:
        with st.sidebar.expander("🔗 Confluence Import", expanded=False):
            st.info(
                "Confluence integration is not configured. "
                "Set CONFLUENCE_ENABLED=true and add your credentials in .env",
                icon="ℹ️"
            )

    st.sidebar.markdown("---")

    # Quick Actions with modern styling
    with st.sidebar:
        render_quick_actions()

    st.sidebar.markdown("---")

    # NEW: Start New Conversation
    if st.sidebar.button("🔄 Start New Conversation", use_container_width=True, help="Clear chat and start fresh conversation"):
        import uuid
        st.session_state.messages = []
        st.session_state.conversation_thread_id = f"streamlit_{uuid.uuid4().hex[:12]}"
        st.session_state.session_queries = 0
        st.rerun()

    st.sidebar.markdown("---")

    # Performance Dashboard
    if st.session_state.agent_initialized:
        with st.sidebar:
            st.sidebar.markdown("---")
            render_stats_dashboard()


def render_agent_details(result: Dict[str, Any]):
    """Render agent execution details in an expander."""
    if not st.session_state.show_agent_details:
        return

    with st.expander("🔍 Agent Reasoning Process", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Selected Tool**")
            selected_tool = result.get('selected_tool', 'N/A')
            st.code(selected_tool, language=None)

            st.markdown("**Tools Used**")
            tools_used = result.get('tools_used', [])
            st.write(", ".join(tools_used) if tools_used else "None")

        with col2:
            st.markdown("**Execution Phase**")
            phase = result.get('current_phase', 'N/A')
            st.code(phase, language=None)

            st.markdown("**Iterations**")
            iterations = result.get('iteration', 0)
            st.write(f"{iterations} / {result.get('max_iterations', 3)}")

        # Tool Results
        if result.get('tool_results'):
            st.markdown("**Tool Execution Results**")
            for i, tool_result in enumerate(result['tool_results'], 1):
                status = "✅" if tool_result.get('success') else "❌"
                tool_name = tool_result.get('tool', 'unknown')
                duration = tool_result.get('duration', 0)

                st.markdown(f"{status} **{tool_name}** ({duration:.2f}s)")

                if tool_result.get('error'):
                    st.error(f"Error: {tool_result['error']}")


def render_memory_context(unique_id: str = "default"):
    """Render memory context in a sidebar or expander."""
    if not st.session_state.show_memory_context:
        return

    agent = st.session_state.agent
    if not agent or not agent.enable_memory:
        return

    with st.expander("💭 Memory Context", expanded=False):
        memory_context = agent.get_memory_context()

        if memory_context:
            st.text_area(
                "Conversation History",
                value=memory_context,
                height=200,
                disabled=True,
                label_visibility="collapsed",
                key=f"memory_context_display_{unique_id}"
            )
        else:
            st.info("No conversation history yet")

        # Session stats
        if agent.memory_manager:
            stats = agent.memory_manager.get_session_stats()

            col1, col2, col3 = st.columns(3)
            col1.metric("Turn Count", stats.get('turn_count', 0))
            col2.metric("Messages", stats.get('total_messages', 0))
            col3.metric("Session ID", stats.get('session_id', 'N/A')[:8] + "...")


def render_reflection_insights():
    """Render reflection insights and learning statistics."""
    if not st.session_state.show_reflection_insights:
        return

    agent = st.session_state.agent
    if not agent or not agent.enable_reflection:
        return

    with st.expander("🧠 Reflection & Learning", expanded=False):
        # Overall Performance
        if agent.learning_module:
            perf = agent.learning_module.get_overall_performance()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Actions", perf.get('total_actions', 0))
            col2.metric("Success Rate", f"{perf.get('success_rate', 0):.1%}")
            col3.metric("Avg Quality", f"{perf.get('avg_quality_score', 0):.2f}/5.0")
            col4.metric("Tools", perf.get('unique_tools_used', 0))

            # Tool Rankings
            st.markdown("**Tool Performance Rankings**")
            rankings = agent.learning_module.get_tool_ranking()

            if rankings:
                for tool, score in rankings[:5]:
                    st.progress(min(score / 10, 1.0), text=f"{tool}: {score:.1f}")
            else:
                st.info("No tool performance data yet")

        # Recent Reflections
        if agent.reflection_module:
            insights = agent.reflection_module.get_insights_summary()

            st.markdown("**Recent Insights**")

            tool_insights = insights.get('tool_selection', [])
            if tool_insights:
                st.markdown("*Tool Selection:*")
                for insight in tool_insights[-3:]:
                    st.markdown(f"• {insight}")

            quality_insights = insights.get('answer_quality', [])
            if quality_insights:
                st.markdown("*Answer Quality:*")
                for insight in quality_insights[-3:]:
                    st.markdown(f"• {insight}")


def render_chat_message_agent(message: Dict):
    """Render a chat message with agent-specific enhancements and modern styling."""
    # Add timestamp if not present
    if 'timestamp' not in message:
        message['timestamp'] = datetime.now()

    # Use enhanced rendering
    render_enhanced_chat_message(message, show_timestamp=True)

    # Additional details for assistant messages
    role = message.get('role', 'assistant')
    if role == 'assistant':
        if message.get('agent_result'):
            # Pass unique ID based on message timestamp to avoid duplicate keys
            msg_id = str(message.get('timestamp', id(message)))
            render_memory_context(unique_id=msg_id)
            render_reflection_insights()


def handle_agent_query(prompt: str):
    """
    Handle user query through the agent system.

    Args:
        prompt: User's question
    """
    if not prompt or not prompt.strip():
        return

    # Add user message with timestamp
    st.session_state.messages.append({
        'role': 'user',
        'content': prompt,
        'timestamp': datetime.now()
    })

    # Get agent
    agent = get_or_create_agent()
    if agent is None:
        show_error("Agent not initialized")
        return

    # Execute agent with conversation thread ID for memory continuity
    try:
        with st.spinner("🤖 Agent is thinking and selecting tools..."):
            result = agent.execute(
                prompt,
                thread_id=st.session_state.conversation_thread_id,
                session_id=st.session_state.conversation_thread_id
            )

        # Increment query count
        st.session_state.session_queries += 1

        # Periodic auto-save of episodic memory (every 5 queries)
        if st.session_state.session_queries % 5 == 0:
            try:
                if agent.enable_memory and agent.memory_manager:
                    agent.memory_manager.save_episodic_memory()
                    print(f"💾 Auto-saved episodic memory (query #{st.session_state.session_queries})")
            except Exception as e:
                print(f"⚠️  Failed to auto-save memory: {e}")

        # Extract answer
        answer = result.get('final_answer', 'No answer generated')

        # Add assistant message with full result and timestamp
        st.session_state.messages.append({
            'role': 'assistant',
            'content': answer,
            'agent_result': result,
            'timestamp': datetime.now()
        })

    except Exception as e:
        error_msg = str(e)
        show_error(f"Agent error: {error_msg}")

        st.session_state.messages.append({
            'role': 'assistant',
            'content': f"Sorry, I encountered an error: {error_msg}",
            'agent_result': None,
            'timestamp': datetime.now()
        })

        import traceback
        with st.expander("Show error details"):
            st.code(traceback.format_exc())


def render_welcome_message_agent():
    """Render welcome message for agent interface with modern styling."""
    # Modern header with animation
    st.markdown(
        get_custom_header_html(
            "RAG Agent Assistant",
            "Powered by Memory, Self-Reflection & Multi-Tool Intelligence"
        ),
        unsafe_allow_html=True
    )

    # Welcome content with modern styling
    st.markdown("""
    <div class="fade-in" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
         border: 1px solid #6366f1; border-radius: 20px; padding: 2.5rem; margin: 1.5rem 0; text-align: center;">
        <h2 style="color: #f1f5f9; margin-top: 0; font-size: 2rem; font-weight: 700;">
            👋 Welcome to Your AI Assistant!
        </h2>
        <p style="color: #cbd5e1; line-height: 1.8; font-size: 1.1rem; max-width: 800px; margin: 1rem auto;">
            I'm an <strong style="color: #818cf8;">intelligent agent</strong> powered by cutting-edge AI.
            I can help you with <strong>research</strong>, <strong>calculations</strong>,
            <strong>code generation</strong>, <strong>web browsing</strong>, and much more!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Stats cards
    st.markdown("---")
    render_stats_cards()
    st.markdown("---")

    # Feature cards with new component
    render_welcome_cards()

    st.markdown("---")

    # Suggested prompts with click functionality
    selected_prompt = render_suggested_prompts()

    # If a prompt was selected, trigger it
    if selected_prompt:
        st.session_state['pending_prompt'] = selected_prompt
        st.rerun()

    # Quick tip
    st.markdown("""
    <div class="slide-up" style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981;
         border-radius: 12px; padding: 1.25rem; margin: 2rem 0; animation-delay: 0.8s;">
        <p style="color: #34d399; margin: 0; font-size: 1rem;">
            💡 <strong>Pro Tip:</strong> Enable "Show Agent Reasoning" in the sidebar to see how I make decisions and select tools!
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_main_chat_agent():
    """Render the main chat interface with agent capabilities and modern UI."""
    # Auto-index documents on first load
    if 'startup_index_done' not in st.session_state:
        try:
            from .auto_index_integration import check_and_index_on_startup
            with st.spinner("🔍 Checking for new documents to index..."):
                result = check_and_index_on_startup(force=False)
                if result['status'] == 'success' and result.get('new', 0) > 0:
                    st.toast(f"✅ Indexed {result['new']} new documents!", icon="📚")
        except Exception as e:
            # Auto-indexing is optional - don't block app startup
            print(f"⚠️  Auto-indexing failed: {e}")
        finally:
            st.session_state.startup_index_done = True

    # Agent will be initialized on first use (lazy loading)
    # This allows the UI to show immediately without waiting for heavy initialization

    # Check for errors
    error = get_error_message()
    if error:
        show_error(error)
        clear_error()

    # Handle pending prompt from suggested prompts
    pending_prompt = st.session_state.get('pending_prompt')
    if pending_prompt:
        st.session_state.pop('pending_prompt')
        handle_agent_query(pending_prompt)
        st.rerun()

    # Show welcome or chat history
    if not st.session_state.messages:
        render_welcome_message_agent()
    else:
        # Show custom header for chat mode
        st.markdown(
            get_custom_header_html(
                "RAG Agent Assistant",
                "Intelligent Conversation in Progress"
            ),
            unsafe_allow_html=True
        )

        # Render chat history with smooth animations
        for idx, message in enumerate(st.session_state.messages):
            # Add animation class to messages
            st.markdown(f'<div class="fade-in" style="animation-delay: {idx * 0.05}s;">', unsafe_allow_html=True)
            render_chat_message_agent(message)
            st.markdown('</div>', unsafe_allow_html=True)

    # Chat input with enhanced placeholder
    placeholder_text = "💬 Ask me anything... (Try 'What documents are indexed?' or 'Calculate 15% of 3,450')"
    if prompt := st.chat_input(placeholder_text, key='chat_input_agent'):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response with loading animation
        with st.chat_message("assistant"):
            # Show typing indicator
            typing_placeholder = st.empty()
            with typing_placeholder:
                render_typing_indicator()

            try:
                handle_agent_query(prompt)
                typing_placeholder.empty()

                # Display the response
                if st.session_state.messages:
                    last_msg = st.session_state.messages[-1]
                    if last_msg['role'] == 'assistant':
                        st.markdown(last_msg['content'])

                        if last_msg.get('agent_result'):
                            render_agent_details(last_msg['agent_result'])
                            render_memory_context()
                            render_reflection_insights()
            except Exception as e:
                typing_placeholder.empty()
                st.error(f"Error: {str(e)}")

        st.rerun()


def cleanup_resources():
    """Cleanup resources on app exit."""
    try:
        # Close agent and save episodic memory
        if hasattr(st.session_state, 'agent') and st.session_state.agent:
            try:
                # Save current session to episodic memory
                st.session_state.agent.end_session()
            except Exception as e:
                print(f"⚠️  Error saving session on exit: {e}")

        # Close database connections
        try:
            from src.database.session_manager import SessionManager
            # Get session manager instance if it exists
            if hasattr(SessionManager, '_instance'):
                session_mgr = SessionManager._instance
                if session_mgr:
                    session_mgr.close()
        except Exception as e:
            print(f"⚠️  Error closing database connections: {e}")
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")


def main():
    """Main application entry point."""
    # Register cleanup function (only once)
    if 'cleanup_registered' not in st.session_state:
        atexit.register(cleanup_resources)
        st.session_state.cleanup_registered = True

    configure_page()
    initialize_agent_session_state()
    render_agent_sidebar()
    render_main_chat_agent()


if __name__ == "__main__":
    main()
