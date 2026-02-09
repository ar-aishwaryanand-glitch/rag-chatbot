"""Enhanced UI components for modern chat interface."""

import streamlit as st
from typing import Dict, Any, List
import time
from datetime import datetime


def render_enhanced_chat_message(message: Dict[str, Any], show_timestamp: bool = True):
    """
    Render an enhanced chat message with modern styling.

    Args:
        message: Message dictionary with role, content, and optional metadata
        show_timestamp: Whether to show message timestamp
    """
    role = message.get('role', 'assistant')
    content = message.get('content', '')
    timestamp = message.get('timestamp', datetime.now())

    with st.chat_message(role):
        # Message header with timestamp
        if show_timestamp:
            col1, col2 = st.columns([6, 1])
            with col2:
                st.caption(f"🕐 {timestamp.strftime('%H:%M')}")

        # Message content with markdown support
        st.markdown(content)

        # Show copy button for assistant messages
        if role == 'assistant':
            if st.button("📋 Copy", key=f"copy_{timestamp}", help="Copy response"):
                st.write(f"```\n{content}\n```")
                st.success("Response ready to copy!", icon="✅")

        # Show agent details if available
        if role == 'assistant' and message.get('agent_result'):
            render_agent_result_card(message['agent_result'])

        # Show sources if available
        if role == 'assistant' and message.get('sources'):
            render_sources_card(message['sources'])


def render_agent_result_card(result: Dict[str, Any]):
    """
    Render agent execution result in a modern card.

    Args:
        result: Agent result dictionary
    """
    if not st.session_state.get('show_agent_details', True):
        return

    with st.expander("🔍 Agent Reasoning", expanded=False):
        # Performance metrics in compact grid
        metrics_cols = st.columns(4)

        with metrics_cols[0]:
            tool = result.get('selected_tool', 'N/A')
            st.metric("Tool Used", tool if tool != 'N/A' else "Direct")

        with metrics_cols[1]:
            phase = result.get('current_phase', 'completed')
            st.metric("Phase", phase.title()[:8])

        with metrics_cols[2]:
            iterations = result.get('iteration', 0)
            max_iter = result.get('max_iterations', 3)
            st.metric("Iterations", f"{iterations}/{max_iter}")

        with metrics_cols[3]:
            tools_used = len(result.get('tools_used', []))
            st.metric("Tools", tools_used)

        # Tool execution results
        if result.get('tool_results'):
            st.markdown("---")
            st.markdown("**🛠️ Tool Execution**")

            for i, tool_result in enumerate(result['tool_results'], 1):
                success = tool_result.get('success', False)
                tool_name = tool_result.get('tool', 'unknown')
                duration = tool_result.get('duration', 0)
                error = tool_result.get('error')

                # Status badge with new colors
                status = "✅" if success else "❌"
                badge_html = f"""
                <div style="display: inline-flex; align-items: center; gap: 6px;
                     padding: 6px 10px; background: {'rgba(16, 185, 129, 0.1)' if success else 'rgba(239, 68, 68, 0.1)'};
                     border: 1px solid {'#10b981' if success else '#ef4444'};
                     border-radius: 6px; margin: 3px 0; font-size: 0.85rem;">
                    <span>{status}</span>
                    <span style="color: #f1f5f9; font-weight: 500;">{tool_name}</span>
                    <span style="color: #94a3b8; font-size: 0.8rem;">({duration:.2f}s)</span>
                </div>
                """
                st.markdown(badge_html, unsafe_allow_html=True)

                if error:
                    st.error(f"Error: {error}", icon="🚨")


def render_sources_card(sources: List[Dict[str, str]]):
    """
    Render document sources in a modern card layout.

    Args:
        sources: List of source dictionaries
    """
    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
        for i, source in enumerate(sources, 1):
            source_name = source.get('source', 'unknown')
            topic = source.get('topic', 'N/A')
            content_preview = source.get('content', 'No preview available')

            # Source card
            card_html = f"""
            <div style="background: rgba(22, 32, 50, 0.6); border: 1px solid #1e3a5f;
                 border-radius: 10px; padding: 0.75rem; margin: 0.35rem 0;
                 backdrop-filter: blur(10px); transition: all 0.2s ease;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 1rem;">📄</span>
                        <strong style="color: #f1f5f9; font-size: 0.9rem;">{source_name}</strong>
                    </div>
                    <span style="background: rgba(6, 182, 212, 0.2); color: #22d3ee;
                         padding: 3px 10px; border-radius: 10px; font-size: 0.75rem; font-weight: 500;">
                        {topic}
                    </span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0; line-height: 1.4;">
                    {content_preview}
                </p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


def render_typing_indicator():
    """Render a typing indicator animation."""
    typing_html = """
    <div style="display: flex; align-items: center; gap: 6px; padding: 0.75rem;">
        <span style="width: 8px; height: 8px; border-radius: 50%; background: #06b6d4;
              animation: pulse 1.4s ease-in-out infinite;"></span>
        <span style="width: 8px; height: 8px; border-radius: 50%; background: #14b8a6;
              animation: pulse 1.4s ease-in-out 0.2s infinite;"></span>
        <span style="width: 8px; height: 8px; border-radius: 50%; background: #22d3ee;
              animation: pulse 1.4s ease-in-out 0.4s infinite;"></span>
    </div>
    <style>
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.8); }
    }
    </style>
    """
    st.markdown(typing_html, unsafe_allow_html=True)


def render_stats_dashboard():
    """Render a performance stats dashboard."""
    if not st.session_state.get('agent_initialized'):
        return

    agent = st.session_state.get('agent')
    if not agent:
        return

    st.markdown("### 📊 Performance")

    # Main metrics in 2x2 grid for better spacing
    col1, col2 = st.columns(2)

    with col1:
        queries = st.session_state.get('session_queries', 0)
        st.metric("🔢 Queries", queries)

    with col2:
        tools = len(agent.tool_registry.get_tool_names())
        st.metric("🛠️ Tools", tools)

    # Second row
    col3, col4 = st.columns(2)

    with col3:
        if agent.enable_reflection and agent.learning_module:
            perf = agent.learning_module.get_overall_performance()
            success_rate = perf.get('success_rate', 0)
            st.metric("✅ Success", f"{success_rate:.0%}")
        else:
            st.metric("✅ Success", "N/A")

    with col4:
        if agent.enable_reflection and agent.learning_module:
            perf = agent.learning_module.get_overall_performance()
            quality = perf.get('avg_quality_score', 0)
            st.metric("⭐ Quality", f"{quality:.1f}/5")
        else:
            st.metric("⭐ Quality", "N/A")

    # Tool usage chart with improved layout
    if agent.enable_reflection and agent.learning_module:
        st.markdown("---")
        st.markdown("**🔧 Tool Rankings**")

        rankings = agent.learning_module.get_tool_ranking()
        if rankings:
            for tool, score in rankings[:5]:
                # Create a cleaner display
                progress_value = min(score / 10, 1.0)

                # Tool name and score on same line
                st.markdown(f"**{tool}** • Score: {score:.1f}")
                st.progress(progress_value)
                st.markdown("")  # Add spacing
        else:
            st.info("No tool performance data yet", icon="📊")


def render_enhanced_sidebar_header():
    """Render an enhanced sidebar header."""
    header_html = """
    <div style="background: linear-gradient(135deg, #06b6d4 0%, #14b8a6 100%);
         padding: 1rem; border-radius: 10px; margin-bottom: 0.75rem;
         box-shadow: 0 8px 12px -3px rgba(6, 182, 212, 0.2);">
        <h2 style="color: white; margin: 0; font-size: 1.1rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">🧪</span> QA Expert
        </h2>
        <p style="color: rgba(255, 255, 255, 0.85); margin: 0.2rem 0 0 0; font-size: 0.8rem;">
            Settings & Tools
        </p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_feature_card(title: str, description: str, enabled: bool, key: str) -> bool:
    """
    Render a feature toggle card.

    Args:
        title: Feature title
        description: Feature description
        enabled: Current state
        key: Unique key for checkbox

    Returns:
        New state value
    """
    card_html = f"""
    <div style="background: rgba(22, 32, 50, 0.6); border: 1px solid #1e3a5f;
         border-radius: 10px; padding: 0.75rem; margin: 0.35rem 0; backdrop-filter: blur(10px);">
        <strong style="color: #f1f5f9; font-size: 0.95rem;">{title}</strong>
        <p style="color: #cbd5e1; font-size: 0.8rem; margin: 0.35rem 0 0 0; line-height: 1.4;">
            {description}
        </p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    return st.checkbox(
        "Enable",
        value=enabled,
        key=key,
        label_visibility="collapsed"
    )


def render_success_toast(message: str):
    """
    Render a success toast notification.

    Args:
        message: Success message
    """
    st.success(message, icon="✅")


def render_error_toast(message: str):
    """
    Render an error toast notification.

    Args:
        message: Error message
    """
    st.error(message, icon="🚨")


def render_info_toast(message: str):
    """
    Render an info toast notification.

    Args:
        message: Info message
    """
    st.info(message, icon="💡")


def render_loading_state(message: str = "Processing..."):
    """
    Render a loading state with spinner.

    Args:
        message: Loading message
    """
    with st.spinner(message):
        # Show typing indicator
        render_typing_indicator()
        time.sleep(0.5)  # Brief pause for visual effect


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary", help="Clear all messages"):
            st.session_state.messages = []
            st.session_state.session_queries = 0
            st.rerun()

    with col2:
        if st.button("🔄 Restart Agent", use_container_width=True, type="secondary", help="Restart agent system"):
            st.session_state.agent = None
            st.session_state.agent_initialized = False
            st.cache_resource.clear()
            st.rerun()


def render_suggested_prompts():
    """Render suggested prompts for users to click."""
    suggested_prompts = [
        {"icon": "📚", "text": "What is RAG and how does it work?"},
        {"icon": "🔍", "text": "Search for information about machine learning"},
        {"icon": "🧮", "text": "Calculate 15% of 3,450"},
        {"icon": "🐍", "text": "Write Python code to sort a list"},
        {"icon": "📄", "text": "What documents are currently indexed?"},
        {"icon": "🌐", "text": "What are the latest AI news?"},
    ]

    st.markdown("### 💬 Try These Prompts")

    # Display prompts in 2 columns
    col1, col2 = st.columns(2)

    for idx, prompt in enumerate(suggested_prompts):
        col = col1 if idx % 2 == 0 else col2

        with col:
            prompt_html = f"""
            <div class="suggested-prompt slide-up" style="animation-delay: {idx * 0.1}s;">
                <span class="suggested-prompt-icon">{prompt['icon']}</span>
                <span class="suggested-prompt-text">{prompt['text']}</span>
            </div>
            """
            st.markdown(prompt_html, unsafe_allow_html=True)

            # Create invisible button overlay
            if st.button(
                prompt['text'],
                key=f"suggested_{idx}",
                use_container_width=True,
                type="secondary",
                help=f"Click to ask: {prompt['text']}"
            ):
                return prompt['text']

    return None


def format_code_block(code: str, language: str = "python") -> str:
    """
    Format code with syntax highlighting.

    Args:
        code: Code string
        language: Programming language

    Returns:
        Formatted HTML
    """
    return f"""
    <div style="position: relative;">
        <pre style="background: rgba(12, 18, 34, 0.8); border: 1px solid #1e3a5f;
             border-radius: 10px; padding: 0.75rem; overflow-x: auto;">
            <code class="language-{language}">{code}</code>
        </pre>
        <button class="copy-button" onclick="navigator.clipboard.writeText('{code}')">
            📋 Copy
        </button>
    </div>
    """


def render_welcome_cards():
    """Render feature cards for the welcome screen."""
    features = [
        {
            "icon": "🧠",
            "title": "Intelligent Memory",
            "description": "Remembers conversations and learns from interactions for better answers.",
            "color": "#06b6d4"
        },
        {
            "icon": "🔍",
            "title": "Smart Search",
            "description": "Search documents and web with advanced RAG for accurate answers.",
            "color": "#14b8a6"
        },
        {
            "icon": "🛠️",
            "title": "Multi-Tool Agent",
            "description": "7+ tools: web search, code execution, calculations, and more.",
            "color": "#10b981"
        },
        {
            "icon": "🌐",
            "title": "Web Browsing",
            "description": "Fetch and analyze web content in real-time.",
            "color": "#22d3ee"
        },
        {
            "icon": "🔄",
            "title": "Self-Reflection",
            "description": "Evaluates decisions and learns from experience.",
            "color": "#f472b6"
        },
        {
            "icon": "⚡",
            "title": "Fast & Reliable",
            "description": "3-5 second response times with async operations.",
            "color": "#f59e0b"
        }
    ]

    st.markdown('<div class="welcome-grid">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for idx, feature in enumerate(features):
        col = cols[idx % 3]

        with col:
            card_html = f"""
            <div class="feature-card slide-up" style="animation-delay: {idx * 0.08}s;">
                <span class="feature-card-icon" style="background: linear-gradient(135deg, {feature['color']} 0%, {feature['color']}99 100%);
                      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{feature['icon']}</span>
                <div class="feature-card-title" style="color: {feature['color']};">
                    {feature['title']}
                </div>
                <div class="feature-card-description">
                    {feature['description']}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_stats_cards():
    """Render statistics cards for the welcome screen."""
    stats = [
        {"value": "7+", "label": "Specialized Tools"},
        {"value": "3-5s", "label": "Avg Response Time"},
        {"value": "100%", "label": "Source Attribution"},
        {"value": "∞", "label": "Conversation Memory"}
    ]

    cols = st.columns(4)

    for idx, (col, stat) in enumerate(zip(cols, stats)):
        with col:
            card_html = f"""
            <div class="stats-card fade-in" style="animation-delay: {idx * 0.1}s;">
                <span class="stats-card-value">{stat['value']}</span>
                <span class="stats-card-label">{stat['label']}</span>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


def render_qa_action_card(icon: str, title: str, description: str, key: str) -> bool:
    """
    Render a QA action card with icon, title, and description.

    Args:
        icon: Emoji icon
        title: Card title
        description: Short description
        key: Unique button key

    Returns:
        True if clicked
    """
    card_html = f"""
    <div class="qa-action-card">
        <span class="qa-action-icon">{icon}</span>
        <div class="qa-action-content">
            <div class="qa-action-title">{title}</div>
            <div class="qa-action-description">{description}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    return st.button(f"Use {title}", key=key, use_container_width=True, type="secondary")


def render_onboarding_steps():
    """Render getting started onboarding steps."""
    steps = [
        {
            "title": "Upload Documents",
            "text": "Add PDFs, docs, or import from Confluence to build your knowledge base"
        },
        {
            "title": "Ask Questions",
            "text": "Chat naturally - I'll search your documents and the web for answers"
        },
        {
            "title": "Generate Tests",
            "text": "Use QA tools to create test cases, BDD scenarios, and test data"
        }
    ]

    st.markdown('<div class="quick-start-title">🚀 Quick Start</div>', unsafe_allow_html=True)

    for idx, step in enumerate(steps, 1):
        step_html = f"""
        <div class="onboarding-step fade-in" style="animation-delay: {idx * 0.1}s;">
            <span class="onboarding-number">{idx}</span>
            <div class="onboarding-content">
                <div class="onboarding-title">{step['title']}</div>
                <div class="onboarding-text">{step['text']}</div>
            </div>
        </div>
        """
        st.markdown(step_html, unsafe_allow_html=True)


def render_simple_prompts():
    """Render simple clickable prompt suggestions."""
    prompts = [
        {"icon": "📄", "text": "What documents are indexed?"},
        {"icon": "🧪", "text": "Generate test cases for user login"},
        {"icon": "🔍", "text": "Search for API documentation"},
        {"icon": "🐛", "text": "Help me write a bug report"},
    ]

    st.markdown("### 💡 Try asking...")

    cols = st.columns(2)
    selected = None

    for idx, prompt in enumerate(prompts):
        col = cols[idx % 2]
        with col:
            if st.button(
                f"{prompt['icon']} {prompt['text']}",
                key=f"simple_prompt_{idx}",
                use_container_width=True,
                type="secondary"
            ):
                selected = prompt['text']

    return selected


def render_qa_dashboard():
    """Render a user-friendly QA tools dashboard with selected state."""
    st.markdown("### 🎯 QA Tools")
    st.caption("Click a tool to get started")

    # Which tool is currently selected
    selected = st.session_state.get('qa_tool')

    # Tool definitions: (key, label, icon, tool_name)
    tools_left = [
        ('generate', 'Generate Tests', '📝', 'rag_query'),
        ('bdd', 'BDD Scenarios', '🥒', 'bdd_generator'),
        ('bug', 'Bug Report', '🐛', 'bug_report'),
    ]
    tools_right = [
        ('analyze', 'Analyze Coverage', '🔍', 'qa_analysis'),
        ('data', 'Test Data', '🎲', 'test_data_generator'),
        ('trace', 'Traceability', '📊', 'traceability_matrix'),
    ]

    actions = {}
    col1, col2 = st.columns(2)

    def _is_selected(tool_name):
        return selected == tool_name

    with col1:
        for key, label, icon, tool_name in tools_left:
            btn_type = "primary" if _is_selected(tool_name) else "secondary"
            display = f"{icon} {label} ✓" if _is_selected(tool_name) else f"{icon} {label}"
            if st.button(display, use_container_width=True, type=btn_type, key=f"qa_dash_{key}"):
                actions[key] = True

    with col2:
        for key, label, icon, tool_name in tools_right:
            btn_type = "primary" if _is_selected(tool_name) else "secondary"
            display = f"{icon} {label} ✓" if _is_selected(tool_name) else f"{icon} {label}"
            if st.button(display, use_container_width=True, type=btn_type, key=f"qa_dash_{key}"):
                actions[key] = True

    # Return which action was clicked
    for action, clicked in actions.items():
        if clicked:
            return action

    return None


def render_empty_chat_state():
    """Render an empty state for the chat area."""
    empty_html = """
    <div class="empty-state fade-in">
        <div class="empty-state-icon">💬</div>
        <div class="empty-state-title">Start a Conversation</div>
        <div class="empty-state-text">
            Ask me anything! I can search documents, generate test cases,
            browse the web, and help with QA tasks.
        </div>
    </div>
    """
    st.markdown(empty_html, unsafe_allow_html=True)


def render_mode_indicator(mode: str):
    """Render a visual mode indicator."""
    mode_html = f"""
    <div class="mode-indicator fade-in">
        <span>🎯</span>
        <span>{mode} Mode</span>
    </div>
    """
    st.markdown(mode_html, unsafe_allow_html=True)


def render_compact_sidebar_section(title: str, icon: str):
    """Render a compact sidebar section header."""
    header_html = f"""
    <div class="sidebar-section-title">
        <span>{icon}</span>
        <span>{title}</span>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_home_document_upload():
    """Render document upload section for home screen."""
    st.markdown("### 📁 Upload Documents")
    st.caption("Add files to your knowledge base")

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
        with st.expander("View files"):
            for file in uploaded_files:
                st.markdown(f"• {file.name} ({file.size / 1024:.1f} KB)")

    return uploaded_files


def render_home_confluence_import():
    """Render Confluence import section for home screen."""
    from src.confluence_loader import is_confluence_configured

    st.markdown("### 🔗 Confluence Import")

    if not is_confluence_configured():
        st.info("Confluence not configured. Set CONFLUENCE_ENABLED=true in .env")
        return None

    st.caption("Import pages from Confluence")

    from src.config import Config

    col1, col2 = st.columns(2)

    with col1:
        space_key = st.text_input(
            "Space Key",
            value=Config.CONFLUENCE_SPACE_KEY or "",
            placeholder="e.g., DOCS",
            key="home_confluence_space"
        )

    with col2:
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

    return {
        "space_key": space_key,
        "fetch_mode": fetch_mode,
        "search_query": search_query,
        "page_id": page_id,
        "limit": limit
    }


def render_home_test_generator():
    """Render test case generator section for home screen."""
    st.markdown("### 🧪 Test Case Generator")
    st.caption("Generate test cases from indexed requirements")

    tc_query = st.text_input(
        "Feature to test",
        placeholder="e.g., User Authentication, Shopping Cart...",
        key="home_tc_query"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        tc_format = st.selectbox(
            "Output",
            options=["Documentation", "Pytest Code", "Both"],
            key="home_tc_format"
        )

    with col2:
        tc_count = st.selectbox(
            "Depth",
            options=[5, 10, 15, 20],
            index=1,
            key="home_tc_count"
        )

    with col3:
        tc_priority = st.selectbox(
            "Focus",
            options=["All", "Functional", "Edge Cases", "Negative"],
            key="home_tc_priority"
        )

    return {
        "query": tc_query,
        "format": tc_format,
        "count": tc_count,
        "priority": tc_priority
    }


def render_home_qa_pipeline():
    """Render QA pipeline section for home screen."""
    st.markdown("### 🔄 Auto QA Pipeline")
    st.caption("Run full pipeline: Requirements → Tests → Gap Analysis")

    pipeline_topic = st.text_input(
        "Topic/Feature Area",
        placeholder="e.g., User Authentication",
        key="home_pipeline_topic"
    )

    auto_run = st.checkbox(
        "Auto-run after document import",
        key="home_auto_pipeline"
    )

    return {
        "topic": pipeline_topic,
        "auto_run": auto_run
    }


def render_home_action_card(icon: str, title: str, description: str, color: str = "#6366f1"):
    """Render an action card for home screen."""
    card_html = f"""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
         border: 1px solid {color}40; border-radius: 16px; padding: 1.5rem; margin: 0.5rem 0;
         transition: all 0.3s ease; border-left: 4px solid {color};">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
            <span style="font-size: 2rem;">{icon}</span>
            <h4 style="color: #f1f5f9; margin: 0; font-size: 1.1rem; font-weight: 600;">{title}</h4>
        </div>
        <p style="color: #94a3b8; margin: 0; font-size: 0.9rem; line-height: 1.5;">{description}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_home_settings():
    """Render AI settings section for home screen."""
    st.markdown("### 🧠 AI Features")

    col1, col2 = st.columns(2)

    with col1:
        memory = st.checkbox(
            "🧠 Memory System",
            value=st.session_state.get('enable_memory', True),
            help="Agent remembers conversation history",
            key="home_memory"
        )

    with col2:
        reflection = st.checkbox(
            "🔄 Self-Reflection",
            value=st.session_state.get('enable_reflection', True),
            help="Agent evaluates and learns from actions",
            key="home_reflection"
        )

    return {"memory": memory, "reflection": reflection}
