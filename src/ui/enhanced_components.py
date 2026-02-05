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
        # Performance metrics
        metrics_cols = st.columns(4)

        with metrics_cols[0]:
            tool = result.get('selected_tool', 'N/A')
            st.metric("Tool Used", tool if tool != 'N/A' else "Direct Answer")

        with metrics_cols[1]:
            phase = result.get('current_phase', 'completed')
            st.metric("Phase", phase.title())

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
            st.markdown("**🛠️ Tool Execution Results**")

            for i, tool_result in enumerate(result['tool_results'], 1):
                success = tool_result.get('success', False)
                tool_name = tool_result.get('tool', 'unknown')
                duration = tool_result.get('duration', 0)
                error = tool_result.get('error')

                # Status badge
                status = "✅ Success" if success else "❌ Failed"
                badge_html = f"""
                <div style="display: inline-flex; align-items: center; gap: 8px;
                     padding: 8px 12px; background: {'rgba(16, 185, 129, 0.1)' if success else 'rgba(239, 68, 68, 0.1)'};
                     border: 1px solid {'#10b981' if success else '#ef4444'};
                     border-radius: 8px; margin: 4px 0;">
                    <strong>{status}</strong>
                    <span style="color: #cbd5e1;">{tool_name}</span>
                    <span style="color: #94a3b8;">({duration:.2f}s)</span>
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
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155;
                 border-radius: 12px; padding: 1rem; margin: 0.5rem 0;
                 backdrop-filter: blur(10px);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.2rem;">📄</span>
                        <strong style="color: #f1f5f9;">{source_name}</strong>
                    </div>
                    <span style="background: rgba(99, 102, 241, 0.2); color: #818cf8;
                         padding: 4px 12px; border-radius: 12px; font-size: 0.85rem;">
                        {topic}
                    </span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.9rem; margin: 0; line-height: 1.5;">
                    {content_preview}
                </p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


def render_typing_indicator():
    """Render a typing indicator animation."""
    typing_html = """
    <div style="display: flex; align-items: center; gap: 4px; padding: 1rem;">
        <span style="width: 8px; height: 8px; border-radius: 50%; background: #6366f1;
              animation: pulse 1.4s ease-in-out infinite;"></span>
        <span style="width: 8px; height: 8px; border-radius: 50%; background: #6366f1;
              animation: pulse 1.4s ease-in-out 0.2s infinite;"></span>
        <span style="width: 8px; height: 8px; border-radius: 50%; background: #6366f1;
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
    <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
         padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;
         box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
        <h2 style="color: white; margin: 0; font-size: 1.5rem; font-weight: 700;">
            ⚙️ Agent Controls
        </h2>
        <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Configure agent behavior and features
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
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155;
         border-radius: 12px; padding: 1rem; margin: 0.5rem 0; backdrop-filter: blur(10px);">
        <strong style="color: #f1f5f9; font-size: 1rem;">{title}</strong>
        <p style="color: #cbd5e1; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
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
        <pre style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155;
             border-radius: 12px; padding: 1rem; overflow-x: auto;">
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
            "description": "I remember our conversations and learn from past interactions to provide better answers over time.",
            "color": "#6366f1"
        },
        {
            "icon": "🔍",
            "title": "Smart Search",
            "description": "Search through uploaded documents and web sources with advanced RAG technology for accurate answers.",
            "color": "#8b5cf6"
        },
        {
            "icon": "🛠️",
            "title": "Multi-Tool Agent",
            "description": "Access to 7+ specialized tools including web search, code execution, calculations, and file operations.",
            "color": "#10b981"
        },
        {
            "icon": "🌐",
            "title": "Web Browsing",
            "description": "Autonomous web agent that can fetch and analyze content from websites in real-time.",
            "color": "#f59e0b"
        },
        {
            "icon": "🔄",
            "title": "Self-Reflection",
            "description": "Evaluates its own decisions and learns from mistakes to continuously improve performance.",
            "color": "#ec4899"
        },
        {
            "icon": "⚡",
            "title": "Fast & Reliable",
            "description": "Optimized for speed with 3-5 second response times and async database operations.",
            "color": "#06b6d4"
        }
    ]

    st.markdown('<div class="welcome-grid">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for idx, feature in enumerate(features):
        col = cols[idx % 3]

        with col:
            card_html = f"""
            <div class="feature-card slide-up" style="animation-delay: {idx * 0.1}s;">
                <span class="feature-card-icon float" style="animation-delay: {idx * 0.2}s;">{feature['icon']}</span>
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
