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
    render_stats_cards,
    render_qa_dashboard,
    render_onboarding_steps,
    render_simple_prompts,
    render_empty_chat_state,
    render_compact_sidebar_section,
    render_home_document_upload,
    render_home_confluence_import,
    render_home_test_generator,
    render_home_qa_pipeline,
    render_home_action_card,
    render_home_settings
)

# Import Config
from src.config import Config

# Import agent components
from src.system_init import initialize_system
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.agent.tool_registry import ToolRegistry
from src.agent.tools import (
    RAGTool,
    DocumentManagementTool,
    # General Tools
    WebSearchTool,
    WebAgentTool,
    CalculatorTool,
    CodeExecutorTool,
    FileOpsTool,
    NewsApiTool,
    # QA Expert Tools
    QAAnalysisTool,
    BugReportTool,
    TestStrategyTool,
    RequirementsExtractorTool,
    TraceabilityMatrixTool,
    BDDGeneratorTool,
    TestDataGeneratorTool
)
from src.agent.qa_pipeline import QAPipeline
from src.agent.manager_agent import ManagerAgent, QAAgentInterface, create_manager_with_qa_agent

# Import input validation
from src.ui.input_validation import (
    InputValidator,
    validate_input,
    show_validation_feedback
)


def configure_page():
    """Configure Streamlit page settings with modern styling."""
    st.set_page_config(
        page_title="QA Expert Assistant",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "QA Expert Assistant - AI-Powered Test Case Generation & QA Automation"
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

    # Get LLM for tools that need it
    llm = rag_chain.llm

    # Core tools
    tools_to_register = [
        RAGTool(rag_chain),  # Query documents & generate test cases
        DocumentManagementTool(vector_store_manager),  # Manage indexed docs
    ]

    # General-purpose tools
    tools_to_register.extend([
        WebSearchTool(),  # Web search via DuckDuckGo
        WebAgentTool(),  # Extract content from URLs
        CalculatorTool(),  # Math calculations
        NewsApiTool(),  # News search
    ])

    # Optional tools based on config
    if Config.CODE_EXECUTOR_ENABLED:
        tools_to_register.append(CodeExecutorTool())
    if Config.FILE_OPS_ENABLED:
        from pathlib import Path
        workspace = Path(__file__).parent.parent.parent / "data" / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        tools_to_register.append(FileOpsTool(workspace_root=workspace))

    # QA Expert Tools
    tools_to_register.extend([
        QAAnalysisTool(rag_chain),
        BugReportTool(rag_chain),
        TestStrategyTool(rag_chain),
        RequirementsExtractorTool(rag_chain),
        TraceabilityMatrixTool(rag_chain),
        BDDGeneratorTool(rag_chain),
        TestDataGeneratorTool(rag_chain)
    ])

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
    import sys
    if st.session_state.get('agent') is None:
        print("[DEBUG] Agent is None, initializing...")
        sys.stdout.flush()
        # Show status during first-time initialization
        status_placeholder = st.empty()
        status_placeholder.info("🚀 Initializing AI agent... (first time only, ~3-5 seconds)")

        try:
            print("[DEBUG] Calling initialize_agent_system...")
            sys.stdout.flush()
            agent = initialize_agent_system(
                enable_memory=st.session_state.enable_memory,
                enable_reflection=st.session_state.enable_reflection
            )
            st.session_state.agent = agent
            st.session_state.agent_initialized = True
            print(f"[DEBUG] Agent initialized successfully: {type(agent)}")
            sys.stdout.flush()

            # Clear status message
            status_placeholder.empty()

        except Exception as e:
            status_placeholder.empty()
            import traceback
            print(f"[DEBUG] Agent init FAILED: {e}")
            print(traceback.format_exc())
            sys.stdout.flush()
            show_error(f"Failed to initialize agent: {str(e)}")
            st.error(f"Agent initialization failed:\n{traceback.format_exc()}")
            return None
    else:
        print("[DEBUG] Agent already exists, reusing")
        sys.stdout.flush()

    return st.session_state.agent


def render_minimal_sidebar():
    """Render a minimal sidebar with just session info and quick actions."""
    with st.sidebar:
        render_enhanced_sidebar_header()

        st.markdown("---")

        # Session Stats (compact)
        if st.session_state.agent_initialized and st.session_state.agent:
            agent = st.session_state.agent

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📝 Queries", st.session_state.session_queries)
            with col2:
                if agent.enable_reflection and agent.learning_module:
                    perf = agent.learning_module.get_overall_performance()
                    st.metric("✅ Success", f"{perf.get('success_rate', 0):.0%}")
                else:
                    st.metric("✅ Success", "N/A")

            st.markdown("---")

            # End Session
            if st.button("🏁 End & Save Session", use_container_width=True, type="secondary"):
                summary = agent.end_session()
                st.success("✅ Session saved!", icon="💾")

        st.markdown("---")

        # Quick Actions
        st.markdown("##### ⚡ Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear", use_container_width=True, key="sidebar_clear"):
                st.session_state.messages = []
                st.session_state.session_queries = 0
                st.rerun()
        with col2:
            if st.button("🔄 Reset", use_container_width=True, key="sidebar_reset"):
                st.session_state.agent = None
                st.session_state.agent_initialized = False
                st.cache_resource.clear()
                st.rerun()

        st.markdown("---")
        st.caption("💡 Use the tabs above for all features")


def render_agent_sidebar_full():
    """DEPRECATED: Full sidebar with all controls. Use render_minimal_sidebar() instead."""
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
                                from src.document_manager import get_document_manager
                                doc_manager = get_document_manager()

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

                                    # AUTO-TRIGGER: Check if auto-pipeline is enabled
                                    if st.session_state.get('auto_qa_pipeline', False):
                                        # Get topic from first document title or use space key
                                        auto_topic = documents[0].metadata.get('title', space_key) if documents else space_key
                                        st.session_state.pending_qa_pipeline = {
                                            "topic": auto_topic,
                                            "trigger": "confluence_import",
                                            "source_docs": len(documents)
                                        }
                                        st.info(f"🔄 Auto-QA Pipeline will run for: **{auto_topic}**", icon="🤖")

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

    # Test Case Generation Section
    with st.sidebar.expander("🧪 Test Case Generator", expanded=False):
        st.markdown("##### Generate QA Test Cases")
        st.caption("Generate test cases from indexed requirements")

        tc_query = st.text_input(
            "Requirements to test",
            placeholder="e.g., Client Setting Page, User Authentication...",
            help="Describe the feature/page to generate test cases for",
            key="tc_query_input"
        )

        # Output format selection
        tc_format = st.selectbox(
            "Output Format",
            options=["Documentation", "Pytest Code", "Both"],
            index=0,
            help="Documentation = Given/When/Then format, Pytest = Python test code",
            key="tc_format_select"
        )

        tc_options = st.columns(2)
        with tc_options[0]:
            tc_count = st.selectbox(
                "Retrieval depth",
                options=[5, 10, 15, 20],
                index=1,
                help="Number of requirement chunks to use"
            )
        with tc_options[1]:
            tc_priority = st.selectbox(
                "Focus",
                options=["All", "Functional", "Edge Cases", "Negative"],
                help="Test case focus area"
            )

        if st.button("🧪 Generate Test Cases", use_container_width=True, type="primary", key="generate_tc_btn"):
            if not tc_query:
                st.error("Please describe the requirements to test", icon="⚠️")
            else:
                with st.status("Generating test cases...", expanded=True) as status:
                    try:
                        from src.rag_chain import RAGChain
                        from src.document_manager import get_document_manager

                        status.update(label="📚 Loading RAG chain...", state="running")
                        doc_manager = get_document_manager()
                        rag_chain = RAGChain(doc_manager)

                        # Add focus to query if specified
                        full_query = tc_query
                        if tc_priority != "All":
                            full_query = f"{tc_query} - Focus on {tc_priority} test cases"

                        status.update(label="🔍 Retrieving requirements...", state="running")

                        # Generate based on selected format
                        result = {"query": full_query, "num_requirements": 0}

                        if tc_format in ["Documentation", "Both"]:
                            doc_result = rag_chain.generate_test_cases(full_query, top_k=tc_count)
                            result.update(doc_result)
                            result["test_cases"] = doc_result.get("test_cases", "")

                        if tc_format in ["Pytest Code", "Both"]:
                            status.update(label="🐍 Generating pytest code...", state="running")
                            pytest_result = rag_chain.generate_pytest_code(full_query, top_k=tc_count)
                            result["pytest_code"] = pytest_result.get("pytest_code", "")
                            result["suggested_filename"] = pytest_result.get("suggested_filename", "test_generated.py")
                            if result.get("num_requirements", 0) == 0:
                                result["num_requirements"] = pytest_result.get("num_requirements", 0)
                                result["sources"] = pytest_result.get("sources", [])

                        result["output_format"] = tc_format

                        if result.get("num_requirements", 0) == 0:
                            status.update(label="⚠️ No requirements found", state="complete")
                            st.warning(
                                "No requirements found. Import requirements from Confluence first.",
                                icon="⚠️"
                            )
                        else:
                            status.update(label="✅ Test cases generated!", state="complete")

                            # Store in session state for display
                            st.session_state.generated_test_cases = result

                            st.success(
                                f"Generated test cases from {result['num_requirements']} requirement chunks!",
                                icon="🎉"
                            )

                    except Exception as e:
                        status.update(label="❌ Generation failed", state="error")
                        st.error(f"Test case generation failed: {str(e)}", icon="🚨")

        # Display generated test cases if available
        if hasattr(st.session_state, 'generated_test_cases') and st.session_state.generated_test_cases:
            result = st.session_state.generated_test_cases
            output_format = result.get("output_format", "Documentation")
            st.markdown("---")
            st.markdown(f"**Based on {result['num_requirements']} requirements:**")

            # Show sources used
            with st.expander("📖 Sources Used", expanded=False):
                for src in result.get('sources', []):
                    st.markdown(f"• **{src.get('title', src.get('source', 'Unknown'))}**")

            # Display and download based on format
            if output_format in ["Documentation", "Both"] and result.get("test_cases"):
                st.markdown("**📋 Test Case Documentation:**")
                st.download_button(
                    "📥 Download Documentation (.md)",
                    data=result['test_cases'],
                    file_name="test_cases.md",
                    mime="text/markdown",
                    key="download_tc_md"
                )

            if output_format in ["Pytest Code", "Both"] and result.get("pytest_code"):
                st.markdown("**🐍 Pytest Code:**")
                st.download_button(
                    "📥 Download Pytest (.py)",
                    data=result['pytest_code'],
                    file_name=result.get("suggested_filename", "test_generated.py"),
                    mime="text/x-python",
                    key="download_tc_py"
                )

    st.sidebar.markdown("---")

    # QA Expert Mode Section
    with st.sidebar.expander("🎯 QA Expert Mode", expanded=False):
        st.markdown("##### AI-Powered QA Assistant")
        st.caption("Specialized tools for QA professionals")

        st.markdown("**Quick Actions:**")

        col1, col2 = st.columns(2)
        with col1:
            # Bug Report Generator
            if st.button("🐛 Bug Report", use_container_width=True, key="qa_bug_btn"):
                st.session_state.qa_prefill = "Write a bug report for the following issue:\n\n[Describe the bug here - what happened, where, and any error messages]"
                st.session_state.qa_tool = "bug_report"
                st.rerun()

        with col2:
            # Test Case Analyzer
            if st.button("🔍 Analyze Tests", use_container_width=True, key="qa_analyze_btn"):
                st.session_state.qa_prefill = "Analyze these test cases for coverage gaps:\n\n[Paste your test cases here]\n\nRequirements context (optional):\n[Describe what the feature should do]"
                st.session_state.qa_tool = "qa_analysis"
                st.rerun()

        col3, col4 = st.columns(2)
        with col3:
            # Test Strategy Advisor
            if st.button("📋 Strategy", use_container_width=True, key="qa_strategy_btn"):
                st.session_state.qa_prefill = "Create a test strategy for:\n\n[Describe the feature or system to test]\n\nApplication type: [web/mobile/API/desktop]\nTech stack: [e.g., React, Python, PostgreSQL]"
                st.session_state.qa_tool = "test_strategy"
                st.rerun()

        with col4:
            # Test Case Generator
            if st.button("📝 Generate", use_container_width=True, key="qa_generate_btn"):
                st.session_state.qa_prefill = "Generate test cases for:\n\n[Describe the feature or user story to test]"
                st.session_state.qa_tool = "rag_query"
                st.rerun()

        # Requirements Extractor (full width)
        if st.button("📄 Extract Requirements", use_container_width=True, key="qa_extract_btn"):
            st.session_state.qa_prefill = "Extract requirements from documents about:\n\n[Enter the feature or topic to extract requirements for]\n\nOutput format: structured (or: user_stories, acceptance_criteria)"
            st.session_state.qa_tool = "requirements_extractor"
            st.rerun()

        st.markdown("**Advanced Tools:**")

        col5, col6 = st.columns(2)
        with col5:
            # Traceability Matrix
            if st.button("📊 Traceability", use_container_width=True, key="qa_trace_btn"):
                st.session_state.qa_prefill = "Generate a traceability matrix for:\n\n[Enter feature/topic to map requirements to test cases]\n\nOutput format: markdown (or: csv, json)"
                st.session_state.qa_tool = "traceability_matrix"
                st.rerun()

        with col6:
            # BDD/Gherkin Generator
            if st.button("🥒 BDD/Gherkin", use_container_width=True, key="qa_bdd_btn"):
                st.session_state.qa_prefill = "Generate BDD scenarios for:\n\n[Describe the feature or paste requirements]\n\nFramework: cucumber (or: behave)"
                st.session_state.qa_tool = "bdd_generator"
                st.rerun()

        # Test Data Generator (full width)
        if st.button("🎲 Generate Test Data", use_container_width=True, key="qa_data_btn"):
            st.session_state.qa_prefill = "Generate test data for these fields:\n\n- username: string, 3-50 characters\n- email: valid email format\n- age: integer, 18-120\n\n[Modify the fields above for your needs]\n\nOutput format: json (or: csv)"
            st.session_state.qa_tool = "test_data_generator"
            st.rerun()

        # Clear QA mode button
        if st.session_state.get('qa_prefill'):
            if st.button("❌ Cancel", use_container_width=True, key="qa_cancel_btn"):
                st.session_state.pop('qa_prefill', None)
                st.session_state.pop('qa_tool', None)
                st.rerun()

        st.markdown("---")
        st.markdown("**Tips:**")
        st.caption("""
• Click a button above to get started
• Fill in the template that appears
• Be specific for better results
        """)

    # Auto QA Pipeline Section
    with st.sidebar.expander("🔄 Auto QA Pipeline", expanded=False):
        st.markdown("##### Automated QA Workflow")
        st.caption("Run full pipeline: Requirements → Tests → Gap Analysis")

        # Auto-run toggle
        st.session_state.auto_qa_pipeline = st.checkbox(
            "Auto-run after document import",
            value=st.session_state.get('auto_qa_pipeline', False),
            help="Automatically run QA pipeline when documents are imported"
        )

        # Get default topic from pending pipeline (e.g., after Confluence import)
        pending_pipeline = st.session_state.get('pending_qa_pipeline', {})
        default_topic = pending_pipeline.get('topic', '') if pending_pipeline.get('trigger') == 'confluence_import' else ''

        # Show notification if auto-pipeline is pending
        if pending_pipeline and pending_pipeline.get('trigger') == 'confluence_import':
            st.info(f"📥 Ready to analyze: **{pending_pipeline.get('topic')}** ({pending_pipeline.get('source_docs', 0)} docs imported)")

        # Topic input
        pipeline_topic = st.text_input(
            "Topic/Feature Area",
            value=default_topic,
            placeholder="e.g., User Authentication",
            help="Feature area to analyze",
            key="pipeline_topic_input"
        )

        # Run pipeline button
        if st.button("▶️ Run QA Pipeline", use_container_width=True, type="primary", key="run_pipeline_btn"):
            if pipeline_topic:
                st.session_state.pending_qa_pipeline = {
                    "topic": pipeline_topic,
                    "trigger": "manual"
                }
                st.rerun()
            else:
                st.error("Please enter a topic")

        # Show pipeline status if running
        if st.session_state.get('pipeline_results'):
            results = st.session_state.pipeline_results
            if results.get('success'):
                st.success(f"Pipeline complete! ({results.get('total_duration', 0):.1f}s)")
            else:
                st.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")

    # Manager Agent Section
    with st.sidebar.expander("🤖 Manager Agent", expanded=False):
        st.markdown("##### AI Task Orchestrator")
        st.caption("Give high-level goals - AI plans and executes")

        # Initialize full manager agent with all agents if not exists
        if "manager_agent" not in st.session_state and st.session_state.get("rag_chain"):
            try:
                from src.agent.manager_agent import create_full_manager
                st.session_state.manager_agent = create_full_manager(
                    rag_chain=st.session_state.rag_chain,
                    llm=st.session_state.rag_chain.llm,
                    enable_memory=True
                )
            except Exception as e:
                # Fallback to basic manager
                try:
                    st.session_state.manager_agent = create_manager_with_qa_agent(
                        rag_chain=st.session_state.rag_chain,
                        llm=st.session_state.rag_chain.llm
                    )
                except Exception as e2:
                    st.warning(f"Manager agent not available: {e2}")

        # Show available agents
        manager = st.session_state.get("manager_agent")
        if manager and hasattr(manager, 'agents'):
            agent_names = list(manager.agents.keys())
            st.caption(f"**Agents:** {', '.join(agent_names)}")

        # Goal input
        manager_goal = st.text_area(
            "What do you want to accomplish?",
            placeholder="e.g., Ensure user authentication is fully tested with BDD scenarios and test data",
            help="Describe your goal - the manager will plan and delegate to specialized agents",
            key="manager_goal_input",
            height=80
        )

        # Example goals with all agent types
        with st.popover("💡 Example Goals"):
            st.markdown("""
            **🧪 QA Goals:**
            - Create comprehensive tests for login feature
            - Generate BDD scenarios with test data
            - Analyze test coverage and fill gaps

            **💻 Dev Goals:**
            - Generate code for user authentication
            - Refactor the payment module
            - Analyze code for improvements

            **📝 Doc Goals:**
            - Create API documentation for endpoints
            - Write a user guide for the dashboard
            - Generate README for the project

            **🔒 Security Goals:**
            - Perform security review on auth code
            - Generate security test cases
            - Check OWASP compliance

            **🔀 Multi-Agent Goals:**
            - Document the API and create tests for it
            - Generate code and security tests for auth
            """)

        # Get recommendations if memory available
        if manager_goal and manager and hasattr(manager, 'get_recommendations'):
            with st.popover("🎯 Smart Recommendations"):
                try:
                    recs = manager.get_recommendations(manager_goal)
                    if recs.get("suggested_agents"):
                        st.markdown(f"**Suggested Agents:** {', '.join(recs['suggested_agents'])}")
                    if recs.get("estimated_tasks"):
                        st.markdown(f"**Est. Tasks:** {recs['estimated_tasks']}")
                    if recs.get("tips"):
                        for tip in recs["tips"][:2]:
                            st.caption(f"💡 {tip}")
                except Exception:
                    st.caption("Enter a goal to see recommendations")

        # Execute button
        if st.button("🚀 Execute Goal", use_container_width=True, type="primary", key="manager_execute_btn"):
            if manager_goal and st.session_state.get("manager_agent"):
                st.session_state.pending_manager_goal = manager_goal
                st.rerun()
            elif not manager_goal:
                st.error("Please enter a goal")
            else:
                st.error("Manager agent not initialized")

        # Show last execution summary
        if st.session_state.get("manager_last_result"):
            result = st.session_state.manager_last_result
            status = "✅" if result.get("success") else "❌"
            st.markdown(f"**Last Execution:** {status}")
            if st.button("View Details", key="view_manager_details"):
                st.session_state.show_manager_details = True

        # Performance summary
        if manager and hasattr(manager, 'get_performance_summary'):
            with st.popover("📊 Performance"):
                try:
                    perf = manager.get_performance_summary()
                    st.metric("Total Executions", perf.get("total_executions", 0))
                    if perf.get("success_rate"):
                        st.metric("Success Rate", f"{perf['success_rate']:.0%}")
                except Exception:
                    st.caption("No performance data yet")

    # Task Scheduler Section
    with st.sidebar.expander("📅 Task Scheduler", expanded=False):
        st.markdown("##### Schedule Recurring Tasks")
        st.caption("Automate QA workflows on a schedule")

        # Initialize scheduler if not exists
        if "task_scheduler" not in st.session_state and st.session_state.get("manager_agent"):
            try:
                from src.agent.task_scheduler import TaskScheduler
                st.session_state.task_scheduler = TaskScheduler(
                    st.session_state.manager_agent
                )
            except Exception as e:
                st.warning(f"Scheduler not available: {e}")

        scheduler = st.session_state.get("task_scheduler")

        if scheduler:
            # Scheduler status
            status = scheduler.get_status()
            col1, col2 = st.columns(2)
            col1.metric("Scheduled", status.get("total_tasks", 0))
            col2.metric("Pending", status.get("pending_tasks", 0))

            # Add new scheduled task
            st.markdown("**Add Scheduled Task**")
            sched_goal = st.text_input(
                "Goal",
                placeholder="Run QA analysis for auth module",
                key="scheduler_goal"
            )
            sched_type = st.selectbox(
                "Frequency",
                ["daily", "weekly", "hourly", "interval"],
                key="scheduler_type"
            )

            col1, col2 = st.columns(2)
            with col1:
                sched_time = st.text_input("Time (HH:MM)", value="09:00", key="scheduler_time")
            with col2:
                if sched_type == "weekly":
                    sched_day = st.selectbox("Day", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], key="scheduler_day")
                elif sched_type == "interval":
                    sched_interval = st.number_input("Minutes", min_value=5, value=60, key="scheduler_interval")

            if st.button("➕ Add Schedule", use_container_width=True, key="add_schedule_btn"):
                if sched_goal:
                    try:
                        day_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
                        task_id = scheduler.schedule_recurring(
                            goal=sched_goal,
                            schedule_type=sched_type,
                            time=sched_time,
                            day_of_week=day_map.get(sched_day, 0) if sched_type == "weekly" else 0,
                            interval_minutes=sched_interval if sched_type == "interval" else 60
                        )
                        st.success(f"Scheduled! ID: {task_id}")
                    except Exception as e:
                        st.error(f"Failed: {e}")
                else:
                    st.error("Please enter a goal")

            # Show scheduled tasks
            tasks = scheduler.get_all_tasks()
            if tasks:
                st.markdown("**Scheduled Tasks**")
                for task in tasks[:5]:
                    with st.container():
                        status_icon = "✅" if task.enabled else "⏸️"
                        st.markdown(f"{status_icon} **{task.goal[:30]}...**")
                        st.caption(f"{task.schedule_type} | Next: {task.next_run[:16]}")

            # Start/stop scheduler
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if not scheduler.is_running():
                    if st.button("▶️ Start", key="start_scheduler"):
                        scheduler.start()
                        st.success("Scheduler started!")
                else:
                    if st.button("⏹️ Stop", key="stop_scheduler"):
                        scheduler.stop()
                        st.info("Scheduler stopped")

            with col2:
                if scheduler.is_running():
                    st.markdown("🟢 **Running**")
                else:
                    st.markdown("🔴 **Stopped**")
        else:
            st.info("Initialize Manager Agent first")

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


def run_qa_pipeline(topic: str):
    """
    Run the automated QA pipeline.

    Args:
        topic: Feature/topic area to analyze
    """
    if not topic or not topic.strip():
        st.error("Please provide a topic for the pipeline")
        return

    # Get agent to access tools
    agent = get_or_create_agent()
    if agent is None:
        st.error("Agent not initialized")
        return

    # Get the RAG chain and tools
    rag_chain = _get_rag_chain()

    # Get tool instances
    requirements_tool = agent.tool_registry.get_tool("requirements_extractor")
    qa_analysis_tool = agent.tool_registry.get_tool("qa_analysis")

    if not requirements_tool or not qa_analysis_tool:
        st.error("Required tools not available")
        return

    # Progress callback
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(message: str, percent: int):
        progress_bar.progress(percent / 100)
        status_text.text(message)

    # Run pipeline
    try:
        pipeline = QAPipeline(
            rag_chain=rag_chain,
            requirements_tool=requirements_tool,
            qa_analysis_tool=qa_analysis_tool,
            progress_callback=progress_callback
        )

        results = pipeline.run(topic=topic)
        st.session_state.pipeline_results = results

        # Add results to chat
        if results.get('success'):
            # Format pipeline results as a message
            output_parts = [f"## QA Pipeline Results: {topic}\n"]

            if 'requirements' in results.get('stages', {}):
                req_stage = results['stages']['requirements']
                output_parts.append(f"### Requirements ({req_stage.get('count', 0)} found)\n")
                output_parts.append(req_stage.get('output', 'No requirements found')[:2000])
                output_parts.append("\n\n")

            if 'test_cases' in results.get('stages', {}):
                tc_stage = results['stages']['test_cases']
                output_parts.append("### Generated Test Cases\n")
                output_parts.append(tc_stage.get('output', 'No test cases generated')[:2000])
                output_parts.append("\n\n")

            if 'gap_analysis' in results.get('stages', {}):
                gap_stage = results['stages']['gap_analysis']
                output_parts.append("### Gap Analysis\n")
                output_parts.append(gap_stage.get('output', 'No gap analysis')[:2000])

            output = "\n".join(output_parts)

            st.session_state.messages.append({
                'role': 'user',
                'content': f"Run QA pipeline for: {topic}",
                'timestamp': datetime.now()
            })
            st.session_state.messages.append({
                'role': 'assistant',
                'content': output,
                'timestamp': datetime.now()
            })
        else:
            st.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        progress_bar.empty()
        status_text.empty()


def run_manager_agent(goal: str):
    """
    Run the manager agent to execute a high-level goal.

    The manager agent:
    1. Plans the execution strategy
    2. Delegates to specialized agents (QA, Dev, etc.)
    3. Aggregates and synthesizes results

    Args:
        goal: High-level goal to accomplish
    """
    if not goal or not goal.strip():
        st.error("Please provide a goal")
        return

    manager = st.session_state.get('manager_agent')
    if not manager:
        st.error("Manager agent not initialized")
        return

    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(message: str, percent: int):
        progress_bar.progress(percent / 100)
        status_text.text(message)

    try:
        # Execute goal through manager
        result = manager.execute(goal, progress_callback=progress_callback)

        # Store result for display
        st.session_state.manager_last_result = result

        # Format output for chat
        if result.get('success'):
            output_parts = [f"## Manager Agent Execution: {goal}\n"]
            output_parts.append(f"**Status:** ✅ Successful\n")

            # Add plan summary
            plan = result.get('plan')
            if plan:
                output_parts.append(f"\n### Execution Plan")
                output_parts.append(f"**Tasks:** {len(plan.tasks)}\n")
                for task in plan.tasks:
                    status_icon = "✅" if task.status == "completed" else "❌"
                    output_parts.append(f"- {status_icon} {task.instruction[:80]}...")

            # Add task results summary
            output_parts.append(f"\n### Results Summary")
            for task_id, task_result in result.get('results', {}).items():
                if task_result.get('success'):
                    # Truncate output for chat display
                    output = task_result.get('output', '')[:500]
                    output_parts.append(f"\n**{task_id}:**\n{output}")
                    if len(task_result.get('output', '')) > 500:
                        output_parts.append("... (truncated)")

            # Add AI summary if available
            summary = result.get('summary', '')
            if summary:
                output_parts.append(f"\n### Summary\n{summary}")

            output = "\n".join(output_parts)

            # Add to chat
            st.session_state.messages.append({
                'role': 'user',
                'content': f"🤖 Manager Agent Goal: {goal}",
                'timestamp': datetime.now()
            })
            st.session_state.messages.append({
                'role': 'assistant',
                'content': output,
                'timestamp': datetime.now(),
                'manager_result': True
            })

            st.success("Goal executed successfully!")

        else:
            # Handle failure
            error_msg = f"Manager agent execution failed.\n\n"
            for task_id, task_result in result.get('results', {}).items():
                if not task_result.get('success'):
                    error_msg += f"- {task_id}: {task_result.get('output', 'Unknown error')}\n"

            st.error(error_msg)

    except Exception as e:
        st.error(f"Manager agent error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        progress_bar.empty()
        status_text.empty()


def show_manager_result_details():
    """Show detailed modal for manager agent results."""
    result = st.session_state.get('manager_last_result')
    if not result:
        return

    # Create a modal-like expander
    with st.expander("🤖 Manager Agent - Execution Details", expanded=True):
        # Close button
        col1, col2 = st.columns([9, 1])
        with col2:
            if st.button("✕", key="close_manager_modal"):
                st.session_state.show_manager_details = False
                st.rerun()

        # Status
        status = "✅ Success" if result.get('success') else "❌ Failed"
        st.markdown(f"### Status: {status}")

        # Plan details
        plan = result.get('plan')
        if plan:
            st.markdown("### Execution Plan")
            st.markdown(f"**Goal:** {plan.goal}")
            st.markdown(f"**Tasks:** {len(plan.tasks)}")
            st.markdown(f"**Created:** {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            # Task table
            st.markdown("#### Tasks")
            for task in plan.tasks:
                status_icon = {"completed": "✅", "failed": "❌", "pending": "⏳"}.get(task.status, "❓")
                with st.container():
                    st.markdown(f"""
                    **{status_icon} {task.task_id}**
                    - Agent: {task.agent_type.value}
                    - Priority: {task.priority}
                    - Instruction: {task.instruction}
                    """)
                    if task.result:
                        with st.expander("View Result"):
                            st.code(task.result[:2000])

        # Results
        st.markdown("### Task Results")
        for task_id, task_result in result.get('results', {}).items():
            with st.expander(f"{task_id}: {'✅' if task_result.get('success') else '❌'}"):
                st.markdown(f"**Tool Used:** {task_result.get('tool_used', 'N/A')}")
                st.markdown(f"**Duration:** {task_result.get('metadata', {}).get('duration', 'N/A')}")
                st.markdown("**Output:**")
                st.code(task_result.get('output', 'No output')[:3000])

        # Summary
        if result.get('summary'):
            st.markdown("### AI Summary")
            st.markdown(result['summary'])


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
    """Render the feature tabs (QA Tools, Documents, Test Generator, Settings).

    Called from render_main_chat_agent() inside non-chat tabs.
    The Chat tab is handled separately in render_main_chat_agent().
    """
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚀 Quick Start",
        "🎯 QA Tools",
        "📁 Documents",
        "🧪 Test Generator",
        "⚙️ Settings"
    ])

    with tab1:
        # Onboarding steps
        render_onboarding_steps()

        st.markdown("---")

        # Simple prompts to get started
        selected_prompt = render_simple_prompts()
        if selected_prompt:
            st.session_state['pending_prompt'] = selected_prompt
            st.rerun()

    with tab2:
        # QA Tools Dashboard
        st.markdown("### 🛠️ QA Automation Tools")
        st.caption("Click any tool to get started")

        qa_action = render_qa_dashboard()

        # Handle QA action selection
        if qa_action:
            prefills = {
                'generate': ("Generate test cases for:\n\n[Describe the feature or user story]", "rag_query"),
                'analyze': ("Analyze coverage gaps for:\n\n[Paste test cases]\n\nRequirements:\n[Describe requirements]", "qa_analysis"),
                'bdd': ("Generate BDD scenarios for:\n\n[Describe the feature]", "bdd_generator"),
                'data': ("Generate test data for:\n\n- field_name: type, constraints\n- email: string, valid email\n- age: integer, 18-99", "test_data_generator"),
                'bug': ("Write a bug report:\n\n**Summary:** [Brief description]\n**Steps to Reproduce:**\n1. \n2. \n**Expected:** \n**Actual:**", "bug_report"),
                'trace': ("Generate traceability matrix for:\n\n[Enter feature/topic name]", "traceability_matrix"),
            }
            if qa_action in prefills:
                st.session_state.qa_prefill = prefills[qa_action][0]
                st.session_state.qa_tool = prefills[qa_action][1]
                st.rerun()

        st.markdown("---")

        # QA Pipeline section
        st.markdown("### 🔄 Auto QA Pipeline")
        st.caption("Run full pipeline: Requirements → Tests → Gap Analysis")

        col1, col2 = st.columns([3, 1])
        with col1:
            pipeline_topic = st.text_input(
                "Topic/Feature Area",
                placeholder="e.g., User Authentication",
                key="home_pipeline_topic_tab"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("▶️ Run Pipeline", type="primary", use_container_width=True, key="home_run_pipeline"):
                if pipeline_topic:
                    st.session_state.pending_qa_pipeline = {"topic": pipeline_topic, "trigger": "manual"}
                    st.rerun()
                else:
                    st.error("Please enter a topic")

        st.markdown("---")

        # Manager Agent Section
        st.markdown("### 🤖 Manager Agent")
        st.caption("Give high-level goals - AI plans and executes automatically")

        # Initialize manager if not exists
        if "manager_agent" not in st.session_state and st.session_state.get("rag_chain"):
            try:
                from src.agent.manager_agent import create_full_manager
                st.session_state.manager_agent = create_full_manager(
                    rag_chain=st.session_state.rag_chain,
                    llm=st.session_state.rag_chain.llm,
                    enable_memory=True
                )
            except Exception:
                pass

        manager = st.session_state.get("manager_agent")
        if manager and hasattr(manager, 'agents'):
            st.caption(f"**Available Agents:** {', '.join(manager.agents.keys())}")

        manager_goal = st.text_area(
            "What do you want to accomplish?",
            placeholder="e.g., Ensure user authentication is fully tested with BDD scenarios and test data",
            help="Describe your goal - the manager will plan and delegate",
            key="tab_manager_goal",
            height=80
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            with st.popover("💡 Example Goals"):
                st.markdown("""
                **🧪 QA:** Create comprehensive tests for login
                **💻 Dev:** Generate code for user auth
                **📝 Doc:** Write API documentation
                **🔒 Security:** Perform security review
                **🔀 Multi:** Document and test the API
                """)
        with col2:
            if st.button("🚀 Execute", type="primary", use_container_width=True, key="tab_manager_execute"):
                if manager_goal and manager:
                    st.session_state.pending_manager_goal = manager_goal
                    st.rerun()
                elif not manager_goal:
                    st.error("Please enter a goal")
                else:
                    st.error("Manager not initialized")

        # Show last result if available
        if st.session_state.get("manager_last_result"):
            result = st.session_state.manager_last_result
            status = "✅ Success" if result.get("success") else "❌ Failed"
            st.info(f"**Last Execution:** {status}")

    with tab3:
        # Document Management Tab
        col1, col2 = st.columns(2)

        with col1:
            # Document Upload
            render_home_action_card(
                "📁", "Upload Documents",
                "Add PDFs, Word docs, and text files to your knowledge base",
                "#6366f1"
            )

            uploaded_files = st.file_uploader(
                "Drag and drop files here",
                type=['txt', 'md', 'pdf', 'docx'],
                accept_multiple_files=True,
                help="Upload .txt, .md, .pdf, or .docx files",
                label_visibility="collapsed",
                key="home_file_upload"
            )

            if uploaded_files:
                st.info(f"📚 {len(uploaded_files)} file(s) selected")
                with st.expander("View selected files"):
                    for file in uploaded_files:
                        st.markdown(f"• {file.name} ({file.size / 1024:.1f} KB)")

                if st.button("📤 Process & Index", type="primary", use_container_width=True, key="home_process_docs"):
                    _process_uploaded_documents(uploaded_files)

        with col2:
            # Confluence Import
            render_home_action_card(
                "🔗", "Confluence Import",
                "Import pages directly from your Confluence workspace",
                "#8b5cf6"
            )

            from src.confluence_loader import is_confluence_configured
            if is_confluence_configured():
                from src.config import Config
                space_key = st.text_input(
                    "Space Key",
                    value=Config.CONFLUENCE_SPACE_KEY or "",
                    placeholder="e.g., DOCS",
                    key="home_confluence_space"
                )

                fetch_mode = st.selectbox(
                    "Fetch Mode",
                    options=["All pages", "Search", "Page ID"],
                    key="home_confluence_mode"
                )

                search_query = None
                page_id = None
                limit = 50

                if fetch_mode == "Search":
                    search_query = st.text_input("Search query", placeholder="Enter search terms...", key="home_conf_search")
                elif fetch_mode == "Page ID":
                    page_id = st.text_input("Page ID", placeholder="Enter page ID...", key="home_conf_pageid")
                else:
                    limit = st.slider("Max pages", 10, 100, 50, key="home_conf_limit")

                if st.button("📥 Fetch from Confluence", type="secondary", use_container_width=True, key="home_fetch_confluence"):
                    _fetch_from_confluence(space_key, fetch_mode, search_query, page_id, limit)
            else:
                st.info("Confluence not configured. Set CONFLUENCE_ENABLED=true in .env", icon="ℹ️")

    with tab4:
        # Test Case Generator Tab
        render_home_action_card(
            "🧪", "Test Case Generator",
            "Generate comprehensive test cases from your indexed requirements documents",
            "#10b981"
        )

        tc_query = st.text_input(
            "Feature/Requirements to test",
            placeholder="e.g., User Authentication, Shopping Cart, Client Settings...",
            key="home_tc_query"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            tc_format = st.selectbox(
                "Output Format",
                options=["Documentation", "Pytest Code", "Both"],
                key="home_tc_format"
            )

        with col2:
            tc_count = st.selectbox(
                "Retrieval Depth",
                options=[5, 10, 15, 20],
                index=1,
                key="home_tc_count",
                help="Number of requirement chunks to use"
            )

        with col3:
            tc_priority = st.selectbox(
                "Focus Area",
                options=["All", "Functional", "Edge Cases", "Negative"],
                key="home_tc_priority"
            )

        if st.button("🧪 Generate Test Cases", type="primary", use_container_width=True, key="home_generate_tc"):
            # Validate input
            validation = InputValidator.validate_requirement_query(tc_query)
            if validation.is_valid:
                if validation.warnings:
                    for warning in validation.warnings:
                        st.warning(f"💡 {warning}")
                _generate_test_cases_home(validation.sanitized_value, tc_format, tc_count, tc_priority)
            else:
                st.error(f"⚠️ {validation.error_message}", icon="⚠️")

        # Show generated test cases if available
        if hasattr(st.session_state, 'generated_test_cases') and st.session_state.generated_test_cases:
            _display_generated_test_cases()

    with tab5:
        # Settings Tab
        col1, col2 = st.columns(2)

        with col1:
            render_home_action_card(
                "🧠", "AI Features",
                "Configure memory and self-reflection capabilities",
                "#f59e0b"
            )

            enable_memory = st.checkbox(
                "🧠 Memory System",
                value=st.session_state.get('enable_memory', True),
                help="Agent remembers conversation history and learns from past sessions",
                key="home_enable_memory"
            )

            enable_reflection = st.checkbox(
                "🔄 Self-Reflection",
                value=st.session_state.get('enable_reflection', True),
                help="Agent evaluates its actions and learns from experience",
                key="home_enable_reflection"
            )

            # Check for settings changes
            if (enable_memory != st.session_state.get('enable_memory') or
                enable_reflection != st.session_state.get('enable_reflection')):
                st.session_state.enable_memory = enable_memory
                st.session_state.enable_reflection = enable_reflection
                st.session_state.agent = None
                st.session_state.agent_initialized = False
                st.cache_resource.clear()
                st.success("✅ Settings updated! Agent will restart.", icon="🔄")
                st.rerun()

        with col2:
            render_home_action_card(
                "📊", "Display Options",
                "Customize what information is shown in responses",
                "#ec4899"
            )

            st.session_state.show_agent_details = st.checkbox(
                "🔍 Agent Reasoning",
                value=st.session_state.get('show_agent_details', True),
                help="Display tool selection and execution details",
                key="home_show_details"
            )

            st.session_state.show_memory_context = st.checkbox(
                "💭 Memory Context",
                value=st.session_state.get('show_memory_context', False),
                help="Display conversation memory and context",
                key="home_show_memory"
            )

            st.session_state.show_reflection_insights = st.checkbox(
                "🧠 Learning Insights",
                value=st.session_state.get('show_reflection_insights', False),
                help="Display self-reflection and learning statistics",
                key="home_show_reflection"
            )

        st.markdown("---")

        # Task Scheduler Section
        st.markdown("### 📅 Task Scheduler")
        st.caption("Schedule recurring QA tasks to run automatically")

        # Initialize scheduler if not exists
        if "task_scheduler" not in st.session_state and st.session_state.get("manager_agent"):
            try:
                from src.agent.task_scheduler import TaskScheduler
                st.session_state.task_scheduler = TaskScheduler(st.session_state.manager_agent)
            except Exception:
                pass

        scheduler = st.session_state.get("task_scheduler")

        if scheduler:
            col1, col2 = st.columns(2)

            # Status
            status = scheduler.get_status()
            col1.metric("📋 Scheduled", status.get("total_tasks", 0))
            col2.metric("⏳ Pending", status.get("pending_tasks", 0))

            # Add new task
            with st.expander("➕ Add Scheduled Task"):
                sched_goal = st.text_input("Goal", placeholder="Run QA for auth module", key="settings_sched_goal")
                sched_type = st.selectbox("Frequency", ["daily", "weekly", "hourly"], key="settings_sched_type")
                sched_time = st.text_input("Time (HH:MM)", value="09:00", key="settings_sched_time")

                if st.button("Add Schedule", type="primary", key="settings_add_schedule"):
                    if sched_goal:
                        try:
                            task_id = scheduler.schedule_recurring(
                                goal=sched_goal,
                                schedule_type=sched_type,
                                time=sched_time
                            )
                            st.success(f"✅ Scheduled! ID: {task_id}")
                        except Exception as e:
                            st.error(f"Failed: {e}")

            # Show tasks and controls
            tasks = scheduler.get_all_tasks()
            if tasks:
                with st.expander(f"📋 View Tasks ({len(tasks)})"):
                    for task in tasks[:5]:
                        status_icon = "✅" if task.enabled else "⏸️"
                        st.markdown(f"{status_icon} **{task.goal[:40]}...** ({task.schedule_type})")

            # Start/Stop
            col1, col2 = st.columns(2)
            with col1:
                if not scheduler.is_running():
                    if st.button("▶️ Start Scheduler", key="settings_start_sched"):
                        scheduler.start()
                        st.success("Scheduler started!")
                else:
                    if st.button("⏹️ Stop Scheduler", key="settings_stop_sched"):
                        scheduler.stop()
                        st.info("Scheduler stopped")
            with col2:
                st.markdown("🟢 **Running**" if scheduler.is_running() else "🔴 **Stopped**")
        else:
            st.info("Run Manager Agent first to enable scheduling")

        st.markdown("---")

        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True, key="home_clear_chat"):
                st.session_state.messages = []
                st.session_state.session_queries = 0
                st.rerun()

        with col2:
            if st.button("🔄 Restart Agent", use_container_width=True, key="home_restart_agent"):
                st.session_state.agent = None
                st.session_state.agent_initialized = False
                st.cache_resource.clear()
                st.rerun()

        with col3:
            if st.button("🆕 New Conversation", use_container_width=True, key="home_new_convo"):
                import uuid
                st.session_state.messages = []
                st.session_state.conversation_thread_id = f"streamlit_{uuid.uuid4().hex[:12]}"
                st.session_state.session_queries = 0
                st.rerun()

        # Feature overview at the bottom
        st.markdown("---")
        st.markdown("### 📚 Features Overview")
        render_welcome_cards()


def _process_uploaded_documents(uploaded_files):
    """Process and index uploaded documents."""
    with st.status("Processing documents...", expanded=True) as status:
        try:
            from pathlib import Path

            docs_dir = Path("data/documents")
            docs_dir.mkdir(parents=True, exist_ok=True)

            saved_files = []
            for idx, uploaded_file in enumerate(uploaded_files, 1):
                file_path = docs_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append(uploaded_file.name)
                status.update(label=f"📄 Saving {idx}/{len(uploaded_files)}: {uploaded_file.name}...", state="running")

            status.update(label="🔄 Re-indexing vector store...", state="running")

            from src.system_init import initialize_system
            initialize_system(rebuild_index=True, use_documents=True)

            st.cache_resource.clear()
            st.session_state.agent = None
            st.session_state.agent_initialized = False

            status.update(label="✅ Upload complete!", state="complete")
            st.success(f"✅ Successfully indexed {len(saved_files)} document(s)!", icon="🎉")
            st.rerun()

        except Exception as e:
            status.update(label="❌ Upload failed", state="error")
            st.error(f"Upload failed: {str(e)}", icon="🚨")


def _fetch_from_confluence(space_key, fetch_mode, search_query, page_id, limit):
    """Fetch documents from Confluence."""
    # Validate inputs based on fetch mode
    if fetch_mode != "Page ID":
        space_validation = InputValidator.validate_confluence_space_key(space_key)
        if not space_validation.is_valid:
            st.error(f"⚠️ {space_validation.error_message}", icon="⚠️")
            return
        space_key = space_validation.sanitized_value

    if fetch_mode == "Search" and not search_query:
        st.error("Please enter a search query", icon="⚠️")
        return

    if fetch_mode == "Page ID":
        page_validation = InputValidator.validate_confluence_page_id(page_id)
        if not page_validation.is_valid:
            st.error(f"⚠️ {page_validation.error_message}", icon="⚠️")
            return
        page_id = page_validation.sanitized_value

    with st.status("Fetching from Confluence...", expanded=True) as status:
        try:
            from src.confluence_loader import get_confluence_loader

            loader = get_confluence_loader()

            if fetch_mode == "Page ID":
                status.update(label=f"📄 Fetching page {page_id}...", state="running")
                documents = loader.load_documents(page_ids=[page_id])
            elif fetch_mode == "Search":
                status.update(label=f"🔍 Searching for '{search_query}'...", state="running")
                documents = loader.load_documents(space_key=space_key, search_query=search_query, limit=limit)
            else:
                status.update(label=f"📚 Fetching pages from {space_key}...", state="running")
                documents = loader.load_documents(space_key=space_key, limit=limit)

            if not documents:
                status.update(label="⚠️ No pages found", state="complete")
                st.warning("No pages found matching your criteria", icon="⚠️")
            else:
                status.update(label=f"🔄 Indexing {len(documents)} pages...", state="running")

                from src.document_manager import get_document_manager
                doc_manager = get_document_manager()

                all_chunks = []
                for doc in documents:
                    chunks = doc_manager.embedding_manager.chunk_documents([doc])
                    all_chunks.extend(chunks)

                if all_chunks:
                    doc_manager.add_documents(all_chunks)
                    doc_manager.save()

                    st.cache_resource.clear()
                    st.session_state.agent = None
                    st.session_state.agent_initialized = False

                    status.update(label="✅ Import complete!", state="complete")
                    st.success(f"✅ Imported {len(documents)} pages ({len(all_chunks)} chunks)!", icon="🎉")
                    st.rerun()
                else:
                    status.update(label="⚠️ No content to index", state="complete")
                    st.warning("Pages had no content to index", icon="⚠️")

        except Exception as e:
            status.update(label="❌ Import failed", state="error")
            st.error(f"Confluence import failed: {str(e)}", icon="🚨")


def _generate_test_cases_home(tc_query, tc_format, tc_count, tc_priority):
    """Generate test cases from home screen."""
    with st.status("Generating test cases...", expanded=True) as status:
        try:
            from src.rag_chain import RAGChain
            from src.document_manager import get_document_manager

            status.update(label="📚 Loading RAG chain...", state="running")
            doc_manager = get_document_manager()
            rag_chain = RAGChain(doc_manager)

            full_query = tc_query
            if tc_priority != "All":
                full_query = f"{tc_query} - Focus on {tc_priority} test cases"

            status.update(label="🔍 Retrieving requirements...", state="running")

            result = {"query": full_query, "num_requirements": 0}

            if tc_format in ["Documentation", "Both"]:
                doc_result = rag_chain.generate_test_cases(full_query, top_k=tc_count)
                result.update(doc_result)
                result["test_cases"] = doc_result.get("test_cases", "")

            if tc_format in ["Pytest Code", "Both"]:
                status.update(label="🐍 Generating pytest code...", state="running")
                pytest_result = rag_chain.generate_pytest_code(full_query, top_k=tc_count)
                result["pytest_code"] = pytest_result.get("pytest_code", "")
                result["suggested_filename"] = pytest_result.get("suggested_filename", "test_generated.py")
                if result.get("num_requirements", 0) == 0:
                    result["num_requirements"] = pytest_result.get("num_requirements", 0)
                    result["sources"] = pytest_result.get("sources", [])

            result["output_format"] = tc_format

            if result.get("num_requirements", 0) == 0:
                status.update(label="⚠️ No requirements found", state="complete")
                st.warning("No requirements found. Import requirements from Confluence first.", icon="⚠️")
            else:
                status.update(label="✅ Test cases generated!", state="complete")
                st.session_state.generated_test_cases = result
                st.success(f"Generated test cases from {result['num_requirements']} requirement chunks!", icon="🎉")

        except Exception as e:
            status.update(label="❌ Generation failed", state="error")
            st.error(f"Test case generation failed: {str(e)}", icon="🚨")


def _display_generated_test_cases():
    """Display generated test cases in the UI."""
    result = st.session_state.generated_test_cases
    output_format = result.get("output_format", "Documentation")

    st.markdown("---")
    st.markdown(f"**Based on {result.get('num_requirements', 0)} requirements:**")

    with st.expander("📖 Sources Used", expanded=False):
        for src in result.get('sources', []):
            st.markdown(f"• **{src.get('title', src.get('source', 'Unknown'))}**")

    if output_format in ["Documentation", "Both"] and result.get("test_cases"):
        st.markdown("**📋 Test Case Documentation:**")
        with st.expander("View Documentation", expanded=True):
            st.markdown(result['test_cases'])
        st.download_button(
            "📥 Download Documentation (.md)",
            data=result['test_cases'],
            file_name="test_cases.md",
            mime="text/markdown",
            key="home_download_tc_md"
        )

    if output_format in ["Pytest Code", "Both"] and result.get("pytest_code"):
        st.markdown("**🐍 Pytest Code:**")
        with st.expander("View Pytest Code", expanded=True):
            st.code(result['pytest_code'], language="python")
        st.download_button(
            "📥 Download Pytest (.py)",
            data=result['pytest_code'],
            file_name=result.get("suggested_filename", "test_generated.py"),
            mime="text/x-python",
            key="home_download_tc_py"
        )

    if st.button("🗑️ Clear Results", key="home_clear_tc"):
        st.session_state.generated_test_cases = None
        st.rerun()


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

    # Handle pending QA pipeline
    pending_pipeline = st.session_state.get('pending_qa_pipeline')
    if pending_pipeline:
        st.session_state.pop('pending_qa_pipeline')

        # Show trigger source message
        if pending_pipeline.get('trigger') == 'confluence_import':
            st.toast(f"🔄 Auto-running QA Pipeline for: {pending_pipeline['topic']}", icon="🤖")

        run_qa_pipeline(pending_pipeline['topic'])
        st.rerun()

    # Handle pending manager agent goal
    pending_manager_goal = st.session_state.get('pending_manager_goal')
    if pending_manager_goal and st.session_state.get('manager_agent'):
        st.session_state.pop('pending_manager_goal')
        run_manager_agent(pending_manager_goal)
        st.rerun()

    # Show manager details modal if requested
    if st.session_state.get('show_manager_details') and st.session_state.get('manager_last_result'):
        show_manager_result_details()

    # Header
    st.markdown(
        get_custom_header_html(
            "QA Expert Assistant",
            "AI-Powered Test Case Generation & QA Automation"
        ),
        unsafe_allow_html=True
    )

    # Top-level tabs: Chat is its own tab alongside feature tabs
    chat_tab, tools_tab = st.tabs(["💬 Chat", "🛠️ Tools & Features"])

    with tools_tab:
        render_welcome_message_agent()

    with chat_tab:
        # Render chat history
        if st.session_state.messages:
            for idx, message in enumerate(st.session_state.messages):
                st.markdown(f'<div class="fade-in" style="animation-delay: {idx * 0.05}s;">', unsafe_allow_html=True)
                render_chat_message_agent(message)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
                 border: 1px solid #6366f1; border-radius: 20px; padding: 2rem; margin: 1rem 0; text-align: center;">
                <h3 style="color: #f1f5f9; margin-top: 0;">👋 Start a conversation</h3>
                <p style="color: #cbd5e1;">Ask me anything — I can search the web, query your documents, generate test cases, and more.</p>
            </div>
            """, unsafe_allow_html=True)

    # Display generated test cases if available (from sidebar generator)
    if hasattr(st.session_state, 'generated_test_cases') and st.session_state.generated_test_cases:
        result = st.session_state.generated_test_cases
        output_format = result.get("output_format", "Documentation")

        # Get the appropriate content based on format
        if output_format == "Pytest Code":
            content = result.get('pytest_code', '')
            title = f"🐍 Generated Pytest Code ({result.get('num_requirements', 0)} requirements)"
            file_ext = "py"
            mime_type = "text/x-python"
        else:
            content = result.get('test_cases', '')
            title = f"🧪 Generated Test Cases ({result.get('num_requirements', 0)} requirements)"
            file_ext = "md"
            mime_type = "text/markdown"

        if content:
            with st.expander(title, expanded=True):
                if output_format == "Pytest Code":
                    st.code(content, language="python")
                else:
                    st.markdown(content)

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Clear Test Cases", key="clear_tc_main"):
                        st.session_state.generated_test_cases = None
                        st.rerun()
                with col2:
                    # Download button
                    query_slug = result.get('query', 'test_cases').replace(' ', '_')[:30]
                    st.download_button(
                        label=f"📥 Download as .{file_ext}",
                        data=content,
                        file_name=f"test_cases_{query_slug}.{file_ext}",
                        mime=mime_type,
                        key="download_tc"
                    )

    # QA Quick Action Input (appears when QA button is clicked)
    if st.session_state.get('qa_prefill'):
        qa_tool = st.session_state.get('qa_tool', 'unknown')
        tool_labels = {
            'bug_report': '🐛 Bug Report',
            'qa_analysis': '🔍 Test Analysis',
            'test_strategy': '📋 Test Strategy',
            'rag_query': '📝 Test Generation'
        }
        st.info(f"**{tool_labels.get(qa_tool, 'QA Tool')}** - Complete the template below and click Submit")

        qa_input = st.text_area(
            "Your request:",
            value=st.session_state.qa_prefill,
            height=200,
            key="qa_input_area",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ Submit", type="primary", use_container_width=True, key="qa_submit_btn"):
                # Clear the prefill state
                st.session_state.pop('qa_prefill', None)
                st.session_state.pop('qa_tool', None)

                # Process the query
                with st.chat_message("user"):
                    st.markdown(qa_input)

                with st.chat_message("assistant"):
                    typing_placeholder = st.empty()
                    with typing_placeholder:
                        render_typing_indicator()

                    try:
                        handle_agent_query(qa_input)
                        typing_placeholder.empty()

                        if st.session_state.messages:
                            last_msg = st.session_state.messages[-1]
                            if last_msg['role'] == 'assistant':
                                st.markdown(last_msg['content'])
                                if last_msg.get('agent_result'):
                                    render_agent_details(last_msg['agent_result'])
                    except Exception as e:
                        typing_placeholder.empty()
                        st.error(f"Error: {str(e)}")

                st.rerun()

        with col2:
            if st.button("❌ Cancel", use_container_width=True, key="qa_cancel_main"):
                st.session_state.pop('qa_prefill', None)
                st.session_state.pop('qa_tool', None)
                st.rerun()

        st.markdown("---")

    # Chat input with simplified placeholder
    placeholder_text = "Ask a question or describe what you need help with..."
    if prompt := st.chat_input(placeholder_text, key='chat_input_agent'):
        print(f"[DEBUG] Chat input received: {prompt}")
        import sys; sys.stdout.flush()

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            try:
                print(f"[DEBUG] Calling handle_agent_query...")
                sys.stdout.flush()
                handle_agent_query(prompt)
                print(f"[DEBUG] handle_agent_query completed")
                sys.stdout.flush()

                # Display the response
                if st.session_state.messages:
                    last_msg = st.session_state.messages[-1]
                    if last_msg['role'] == 'assistant':
                        st.markdown(last_msg['content'])

                        if last_msg.get('agent_result'):
                            render_agent_details(last_msg['agent_result'])
                            render_memory_context()
                            render_reflection_insights()
                    else:
                        st.warning("No assistant response generated.")
                else:
                    st.warning("No messages in session state.")
            except Exception as e:
                import traceback
                print(f"[DEBUG] ERROR: {e}")
                print(traceback.format_exc())
                sys.stdout.flush()
                st.error(f"Error: {str(e)}\n\n{traceback.format_exc()}")

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
    render_minimal_sidebar()  # Clean minimal sidebar - all features in main tabs
    render_main_chat_agent()


if __name__ == "__main__":
    main()
