"""Enhanced Streamlit application with Phase 3 Agent Integration.

This version uses AgentExecutorV3 with memory and self-reflection capabilities,
providing a more intelligent and context-aware chat experience.

NOW WITH MODERN UI! 🎨
"""

import streamlit as st
from typing import Dict, Any
import json
from datetime import datetime

# Import UI modules
from .state_manager import (
    initialize_session_state,
    is_initialized,
    get_error_message,
    clear_error,
    config_override
)
from .components import (
    render_sidebar,
    show_error,
    show_info
)

# Import modern UI components
from .styles import get_modern_css, get_custom_header_html
from .enhanced_components import (
    render_enhanced_chat_message,
    render_typing_indicator,
    render_stats_dashboard,
    render_enhanced_sidebar_header,
    render_quick_actions
)

# Import Config
from src.config import Config

# Import agent components
from src.main import initialize_system
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.agent.tool_registry import ToolRegistry
from src.agent.tools import (
    RAGTool,
    WebSearchTool,
    CalculatorTool,
    CodeExecutorTool,
    FileOpsTool,
    DocumentManagementTool,
    WebAgentTool
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
    }

    for key, value in agent_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def initialize_agent_system(enable_memory: bool = True, enable_reflection: bool = True):
    """
    Initialize the agent system with all tools.

    Args:
        enable_memory: Enable memory features
        enable_reflection: Enable self-reflection features

    Returns:
        AgentExecutorV3 instance
    """
    # Initialize RAG system
    rag_chain = initialize_system(rebuild_index=False, use_documents=True)
    vector_store_manager = rag_chain.vector_store_manager

    # Register tools
    tool_registry = ToolRegistry()

    tools_to_register = [
        RAGTool(rag_chain),
        WebSearchTool(max_results=3),
        CalculatorTool(),
        CodeExecutorTool(timeout=10),
        FileOpsTool(Config.FILE_OPS_WORKSPACE),
        DocumentManagementTool(vector_store_manager)
    ]

    # Add Web Agent only if Playwright is available (not on Streamlit Cloud)
    try:
        web_agent = WebAgentTool(timeout=30, max_pages=5)
        if web_agent.available:
            tools_to_register.append(web_agent)
    except Exception as e:
        # Playwright not available - skip web agent (expected on Streamlit Cloud)
        pass

    for tool in tools_to_register:
        tool_registry.register(tool)

    # Initialize agent with Phase 3 features
    llm = rag_chain.llm
    agent = AgentExecutorV3(
        llm,
        tool_registry,
        Config,
        enable_memory=enable_memory,
        enable_reflection=enable_reflection
    )

    return agent


def get_or_create_agent():
    """Get or create the agent instance."""
    if st.session_state.get('agent') is None:
        try:
            with st.spinner("🚀 Initializing Agent with Phase 3 features..."):
                agent = initialize_agent_system(
                    enable_memory=st.session_state.enable_memory,
                    enable_reflection=st.session_state.enable_reflection
                )
                st.session_state.agent = agent
                st.session_state.agent_initialized = True
                show_info("✅ Agent initialized with memory & reflection!")
        except Exception as e:
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

    # Agent Features Toggle
    st.sidebar.subheader("🧠 Phase 3 Features")

    enable_memory = st.sidebar.checkbox(
        "Enable Memory",
        value=st.session_state.enable_memory,
        help="Agent remembers conversation history and learns from past sessions"
    )

    enable_reflection = st.sidebar.checkbox(
        "Enable Self-Reflection",
        value=st.session_state.enable_reflection,
        help="Agent evaluates its actions and learns from experience"
    )

    # Check if settings changed
    if (enable_memory != st.session_state.enable_memory or
        enable_reflection != st.session_state.enable_reflection):
        st.session_state.enable_memory = enable_memory
        st.session_state.enable_reflection = enable_reflection
        st.session_state.agent = None  # Force reinit
        st.session_state.agent_initialized = False
        st.cache_resource.clear()
        st.rerun()

    st.sidebar.markdown("---")

    # Display Options
    st.sidebar.subheader("📊 Display Options")

    st.session_state.show_agent_details = st.sidebar.checkbox(
        "Show Agent Reasoning",
        value=st.session_state.show_agent_details,
        help="Display tool selection and execution details"
    )

    st.session_state.show_memory_context = st.sidebar.checkbox(
        "Show Memory Context",
        value=st.session_state.show_memory_context,
        help="Display conversation memory and context"
    )

    st.session_state.show_reflection_insights = st.sidebar.checkbox(
        "Show Reflection Insights",
        value=st.session_state.show_reflection_insights,
        help="Display self-reflection and learning statistics"
    )

    st.sidebar.markdown("---")

    # Session Stats
    if st.session_state.agent_initialized and st.session_state.agent:
        st.sidebar.subheader("📈 Session Stats")
        agent = st.session_state.agent

        st.sidebar.metric("Queries", st.session_state.session_queries)

        if agent.enable_reflection and agent.learning_module:
            perf = agent.learning_module.get_overall_performance()
            st.sidebar.metric("Success Rate", f"{perf.get('success_rate', 0):.1%}")
            st.sidebar.metric("Tools Used", perf.get('unique_tools_used', 0))

        # End Session Button
        if st.sidebar.button("🏁 End Session & Save", use_container_width=True):
            summary = agent.end_session()
            st.sidebar.success("Session saved to episodic memory!")

            with st.sidebar.expander("Session Summary"):
                st.json(summary)

    st.sidebar.markdown("---")

    # Document Upload Section
    st.sidebar.subheader("📁 Upload Documents")

    uploaded_files = st.sidebar.file_uploader(
        "Upload documents to index",
        type=['txt', 'md', 'pdf', 'docx'],
        accept_multiple_files=True,
        help="Upload .txt, .md, .pdf, or .docx files to add to the knowledge base"
    )

    if uploaded_files:
        if st.sidebar.button("📤 Process & Index", use_container_width=True):
            with st.sidebar.status("Processing documents...") as status:
                try:
                    from pathlib import Path
                    import shutil

                    # Create documents directory if it doesn't exist
                    docs_dir = Path("data/documents")
                    docs_dir.mkdir(parents=True, exist_ok=True)

                    saved_files = []
                    for uploaded_file in uploaded_files:
                        # Save file
                        file_path = docs_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        saved_files.append(uploaded_file.name)
                        status.update(label=f"Saved {uploaded_file.name}...")

                    status.update(label="Re-indexing vector store...")

                    # Force rebuild of vector store with new documents
                    from src.main import initialize_system
                    rag_chain = initialize_system(rebuild_index=True, use_documents=True)

                    # Clear cache and reinitialize agent with new vector store
                    st.cache_resource.clear()
                    st.session_state.agent = None
                    st.session_state.agent_initialized = False

                    status.update(label="✅ Upload complete!", state="complete")
                    st.sidebar.success(f"Uploaded {len(saved_files)} file(s):\n" + "\n".join(f"• {f}" for f in saved_files))
                    st.rerun()

                except Exception as e:
                    st.sidebar.error(f"Upload failed: {str(e)}")

    st.sidebar.markdown("---")

    # Quick Actions with modern styling
    with st.sidebar:
        render_quick_actions()

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


def render_memory_context():
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
                key="memory_context_display"
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
            render_memory_context()
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

    # Execute agent
    try:
        with st.spinner("🤖 Agent is thinking and selecting tools..."):
            result = agent.execute(prompt)

        # Increment query count
        st.session_state.session_queries += 1

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
    # Modern header
    st.markdown(
        get_custom_header_html(
            "RAG Agent Assistant",
            "Powered by Memory, Self-Reflection & Multi-Tool Intelligence"
        ),
        unsafe_allow_html=True
    )

    # Welcome content with modern cards
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(10px);
         border: 1px solid #334155; border-radius: 16px; padding: 2rem; margin: 1rem 0;">
        <h3 style="color: #f1f5f9; margin-top: 0;">👋 Welcome!</h3>
        <p style="color: #cbd5e1; line-height: 1.6;">
            I'm an <strong>intelligent agent</strong> powered by cutting-edge AI capabilities.
            I can help you with research, calculations, code generation, and much more!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid #6366f1;
             border-radius: 12px; padding: 1.5rem; height: 100%;">
            <h4 style="color: #818cf8; margin-top: 0;">🧠 Intelligent Features</h4>
            <ul style="color: #cbd5e1; line-height: 1.8;">
                <li><strong>Memory</strong>: I remember our conversations</li>
                <li><strong>Self-Reflection</strong>: I learn from mistakes</li>
                <li><strong>Multi-Tool</strong>: Access to 7+ specialized tools</li>
                <li><strong>Web Agent</strong>: Autonomous web browsing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid #8b5cf6;
             border-radius: 12px; padding: 1.5rem; height: 100%;">
            <h4 style="color: #a78bfa; margin-top: 0;">💬 Try Asking Me</h4>
            <ul style="color: #cbd5e1; line-height: 1.8;">
                <li>"What is RAG and how does it work?"</li>
                <li>"Calculate 15% of 3,450"</li>
                <li>"Write Python code to sort a list"</li>
                <li>"What documents are indexed?"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Quick tip
    st.markdown("""
    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981;
         border-radius: 12px; padding: 1rem; margin: 1rem 0;">
        <p style="color: #34d399; margin: 0;">
            💡 <strong>Pro Tip:</strong> Enable "Show Agent Reasoning" in the sidebar to see how I make decisions!
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_main_chat_agent():
    """Render the main chat interface with agent capabilities and modern UI."""
    # Initialize agent
    if not st.session_state.agent_initialized:
        agent = get_or_create_agent()
        if agent is None:
            st.stop()

    # Check for errors
    error = get_error_message()
    if error:
        show_error(error)
        clear_error()

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

        # Render chat history
        for message in st.session_state.messages:
            render_chat_message_agent(message)

    # Chat input
    if prompt := st.chat_input("Ask me anything...", key='chat_input_agent'):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                handle_agent_query(prompt)

                # Display the response
                if st.session_state.messages:
                    last_msg = st.session_state.messages[-1]
                    if last_msg['role'] == 'assistant':
                        st.markdown(last_msg['content'])

                        if last_msg.get('agent_result'):
                            render_agent_details(last_msg['agent_result'])
                            render_memory_context()
                            render_reflection_insights()

        st.rerun()


def main():
    """Main application entry point."""
    configure_page()
    initialize_agent_session_state()
    render_agent_sidebar()
    render_main_chat_agent()


if __name__ == "__main__":
    main()
