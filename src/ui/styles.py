"""Modern CSS styles for the RAG Agent UI."""

def get_modern_css() -> str:
    """Return modern CSS styling for the Streamlit app."""
    return """
    <style>
    /* ========== MODERN COLOR SCHEME ========== */
    :root {
        --primary-color: #6366f1;
        --primary-dark: #4f46e5;
        --primary-light: #818cf8;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #334155;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* ========== GLOBAL STYLES ========== */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ========== CUSTOM HEADER ========== */
    .custom-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 2rem 2rem 2.5rem 2rem;
        border-radius: 0 0 24px 24px;
        margin: -1rem -1rem 2rem -1rem;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
    }

    .custom-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.5;
    }

    .custom-header h1 {
        color: white !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .custom-header p {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1.1rem !important;
        margin: 0.5rem 0 0 0 !important;
        position: relative;
        z-index: 1;
    }

    /* ========== CHAT MESSAGES ========== */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }

    .stChatMessage:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    /* User messages */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
        border-color: var(--primary-color) !important;
    }

    /* Assistant messages */
    .stChatMessage[data-testid*="assistant"] {
        background: rgba(30, 41, 59, 0.8) !important;
    }

    /* Message text */
    .stChatMessage p {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }

    /* ========== CHAT INPUT ========== */
    .stChatInputContainer {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 0.5rem !important;
        box-shadow: var(--shadow-lg);
    }

    .stChatInputContainer:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }

    .stChatInput textarea {
        color: var(--text-primary) !important;
        background: transparent !important;
        font-size: 1rem !important;
    }

    .stChatInput textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary) !important;
    }

    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* ========== BUTTONS ========== */
    .stButton button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-md);
        text-transform: none !important;
    }

    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-color) 100%) !important;
    }

    .stButton button:active {
        transform: translateY(0) !important;
    }

    /* Secondary buttons */
    .stButton button[kind="secondary"] {
        background: rgba(51, 65, 85, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
    }

    /* ========== METRICS ========== */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        box-shadow: var(--shadow-sm);
        min-height: 80px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: block !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }

    /* Sidebar metrics - more compact */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        padding: 0.5rem !important;
        min-height: 70px;
    }

    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }

    /* ========== EXPANDERS ========== */
    .streamlit-expanderHeader {
        background: rgba(51, 65, 85, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(51, 65, 85, 0.6) !important;
        border-color: var(--primary-color) !important;
    }

    .streamlit-expanderContent {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        backdrop-filter: blur(10px);
    }

    /* ========== CODE BLOCKS ========== */
    code {
        background: rgba(15, 23, 42, 0.8) !important;
        color: var(--primary-light) !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 6px !important;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
        font-size: 0.9rem !important;
    }

    pre {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        box-shadow: var(--shadow-md);
    }

    pre code {
        background: transparent !important;
        padding: 0 !important;
    }

    /* ========== FILE UPLOADER ========== */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color) !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }

    /* ========== PROGRESS BARS ========== */
    .stProgress > div {
        background: rgba(51, 65, 85, 0.4) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        border-radius: 10px !important;
        height: 10px !important;
        transition: width 0.3s ease !important;
    }

    /* Progress bar in sidebar - more compact */
    [data-testid="stSidebar"] .stProgress > div > div {
        height: 8px !important;
    }

    /* ========== CHECKBOXES ========== */
    .stCheckbox {
        color: var(--text-primary) !important;
    }

    .stCheckbox label {
        color: var(--text-primary) !important;
    }

    /* ========== SUCCESS/WARNING/ERROR MESSAGES ========== */
    .stAlert {
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
        border: 1px solid !important;
    }

    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border-color: var(--success-color) !important;
        color: var(--success-color) !important;
    }

    .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        border-color: var(--warning-color) !important;
        color: var(--warning-color) !important;
    }

    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: var(--error-color) !important;
        color: var(--error-color) !important;
    }

    .stInfo {
        background: rgba(99, 102, 241, 0.1) !important;
        border-color: var(--primary-color) !important;
        color: var(--primary-light) !important;
    }

    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.1) !important;
        color: var(--primary-light) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        color: white !important;
    }

    /* ========== SPINNERS ========== */
    .stSpinner > div {
        border-top-color: var(--primary-color) !important;
    }

    /* ========== TOOLTIPS ========== */
    [data-testid="stTooltipIcon"] {
        color: var(--primary-light) !important;
    }

    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.4);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-color) 100%);
    }

    /* ========== ANIMATIONS ========== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideIn {
        from {
            transform: translateX(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideUp {
        from {
            transform: translateY(20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    @keyframes float {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-10px);
        }
    }

    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 5px rgba(99, 102, 241, 0.5);
        }
        50% {
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.8);
        }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    .slide-in {
        animation: slideIn 0.5s ease-out;
    }

    .slide-up {
        animation: slideUp 0.6s ease-out;
    }

    .float {
        animation: float 3s ease-in-out infinite;
    }

    .glow {
        animation: glow 2s ease-in-out infinite;
    }

    /* ========== TYPING INDICATOR ========== */
    .typing-indicator {
        display: inline-flex;
        gap: 4px;
        padding: 1rem;
    }

    .typing-indicator span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--primary-color);
        animation: pulse 1.4s ease-in-out infinite;
    }

    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }

    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }

    /* ========== COPY BUTTON ========== */
    .copy-button {
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(99, 102, 241, 0.8);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .copy-button:hover {
        background: var(--primary-color);
        transform: scale(1.05);
    }

    /* ========== STATUS BADGES ========== */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-badge.success {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
        border: 1px solid var(--success-color);
    }

    .status-badge.error {
        background: rgba(239, 68, 68, 0.2);
        color: var(--error-color);
        border: 1px solid var(--error-color);
    }

    .status-badge.warning {
        background: rgba(245, 158, 11, 0.2);
        color: var(--warning-color);
        border: 1px solid var(--warning-color);
    }

    .status-badge.info {
        background: rgba(99, 102, 241, 0.2);
        color: var(--primary-light);
        border: 1px solid var(--primary-color);
    }

    /* ========== SUGGESTED PROMPTS ========== */
    .suggested-prompt {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .suggested-prompt:hover {
        background: rgba(99, 102, 241, 0.2);
        border-color: var(--primary-color);
        transform: translateX(5px);
        box-shadow: var(--shadow-lg);
    }

    .suggested-prompt-icon {
        font-size: 1.5rem;
        flex-shrink: 0;
    }

    .suggested-prompt-text {
        color: var(--text-primary);
        font-size: 0.95rem;
        font-weight: 500;
    }

    /* ========== FEATURE CARDS ========== */
    .feature-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-5px);
        box-shadow: var(--shadow-xl);
    }

    .feature-card-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        display: block;
    }

    .feature-card-title {
        color: var(--text-primary);
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .feature-card-description {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* ========== STATS CARD ========== */
    .stats-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid var(--primary-color);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .stats-card:hover {
        transform: scale(1.05);
        box-shadow: var(--shadow-lg);
    }

    .stats-card-value {
        color: var(--primary-light);
        font-size: 2rem;
        font-weight: 700;
        display: block;
        margin-bottom: 0.5rem;
    }

    .stats-card-label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ========== LOADING SKELETON ========== */
    .skeleton {
        background: linear-gradient(
            90deg,
            rgba(51, 65, 85, 0.4) 0%,
            rgba(71, 85, 105, 0.6) 50%,
            rgba(51, 65, 85, 0.4) 100%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }

    /* ========== TOOL BADGE ========== */
    .tool-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.2);
        border: 1px solid var(--primary-color);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--primary-light);
        margin: 4px;
        transition: all 0.2s ease;
    }

    .tool-badge:hover {
        background: rgba(99, 102, 241, 0.3);
        transform: scale(1.05);
    }

    /* ========== WELCOME SCREEN ========== */
    .welcome-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }

    .welcome-title {
        text-align: center;
        margin-bottom: 3rem;
    }

    .welcome-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }

    /* ========== RESPONSIVE DESIGN ========== */
    @media (max-width: 768px) {
        .custom-header h1 {
            font-size: 2rem !important;
        }

        .stChatMessage {
            padding: 1rem !important;
        }

        .welcome-grid {
            grid-template-columns: 1fr;
        }

        .feature-card {
            padding: 1rem;
        }

        .suggested-prompt {
            padding: 0.75rem 1rem;
        }
    }
    </style>
    """


def get_typing_indicator_html() -> str:
    """Return HTML for typing indicator animation."""
    return """
    <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
    </div>
    """


def get_status_badge_html(status: str, text: str) -> str:
    """
    Return HTML for status badge.

    Args:
        status: Badge status (success, error, warning, info)
        text: Badge text

    Returns:
        HTML string for status badge
    """
    return f'<span class="status-badge {status}">{text}</span>'


def get_custom_header_html(title: str, subtitle: str) -> str:
    """
    Return HTML for custom header.

    Args:
        title: Header title
        subtitle: Header subtitle

    Returns:
        HTML string for custom header
    """
    return f"""
    <div class="custom-header fade-in">
        <h1>🤖 {title}</h1>
        <p>{subtitle}</p>
    </div>
    """
