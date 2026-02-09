"""Modern CSS styles for the RAG Agent UI."""

def get_modern_css() -> str:
    """Return modern CSS styling for the Streamlit app."""
    return """
    <style>
    /* ========== MODERN COLOR SCHEME - Teal/Cyan ========== */
    :root {
        --primary-color: #06b6d4;
        --primary-dark: #0891b2;
        --primary-light: #22d3ee;
        --secondary-color: #14b8a6;
        --accent-color: #f472b6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --bg-primary: #0c1222;
        --bg-secondary: #162032;
        --bg-tertiary: #1e3a5f;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #1e3a5f;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* ========== GLOBAL STYLES ========== */
    .stApp {
        background: linear-gradient(135deg, #0c1222 0%, #162032 100%);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ========== CUSTOM HEADER ========== */
    .custom-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 1rem 1.5rem 1.25rem 1.5rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 1rem -1rem;
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
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .custom-header p {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1rem !important;
        margin: 0.25rem 0 0 0 !important;
        position: relative;
        z-index: 1;
    }

    /* ========== CHAT MESSAGES ========== */
    .stChatMessage {
        background: rgba(22, 32, 50, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }

    .stChatMessage:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    /* User messages */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(20, 184, 166, 0.15) 100%) !important;
        border-color: var(--primary-color) !important;
    }

    /* Assistant messages */
    .stChatMessage[data-testid*="assistant"] {
        background: rgba(22, 32, 50, 0.8) !important;
    }

    /* Message text */
    .stChatMessage p {
        color: var(--text-primary) !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }

    /* ========== CHAT INPUT ========== */
    .stChatInputContainer {
        background: rgba(22, 32, 50, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
        box-shadow: var(--shadow-lg);
    }

    .stChatInputContainer:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15);
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
        background: linear-gradient(180deg, #162032 0%, #0c1222 100%) !important;
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
        border-radius: 10px !important;
        padding: 0.6rem 1.25rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
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
        background: rgba(22, 32, 50, 0.6) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.6rem !important;
        box-shadow: var(--shadow-sm);
        min-height: 70px;
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
        padding: 0.4rem !important;
        min-height: 60px;
    }

    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }

    /* ========== EXPANDERS ========== */
    .streamlit-expanderHeader {
        background: rgba(30, 58, 95, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(30, 58, 95, 0.6) !important;
        border-color: var(--primary-color) !important;
    }

    .streamlit-expanderContent {
        background: rgba(22, 32, 50, 0.4) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        backdrop-filter: blur(10px);
    }

    /* ========== CODE BLOCKS ========== */
    code {
        background: rgba(12, 18, 34, 0.8) !important;
        color: var(--primary-light) !important;
        padding: 0.15rem 0.4rem !important;
        border-radius: 4px !important;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    pre {
        background: rgba(12, 18, 34, 0.8) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.75rem !important;
        box-shadow: var(--shadow-md);
    }

    pre code {
        background: transparent !important;
        padding: 0 !important;
    }

    /* ========== FILE UPLOADER ========== */
    [data-testid="stFileUploader"] {
        background: rgba(22, 32, 50, 0.4) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color) !important;
        background: rgba(6, 182, 212, 0.05) !important;
    }

    /* ========== PROGRESS BARS ========== */
    .stProgress > div {
        background: rgba(30, 58, 95, 0.4) !important;
        border-radius: 8px !important;
        overflow: hidden;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
        border-radius: 8px !important;
        height: 8px !important;
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
        background: rgba(6, 182, 212, 0.1) !important;
        border-color: var(--primary-color) !important;
        color: var(--primary-light) !important;
    }

    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(22, 32, 50, 0.4) !important;
        border-radius: 10px !important;
        padding: 0.4rem !important;
        gap: 0.4rem;
        overflow-x: auto;
        flex-wrap: nowrap;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 6px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        transition: all 0.3s ease;
        white-space: nowrap;
        flex-shrink: 0;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(6, 182, 212, 0.1) !important;
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
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(12, 18, 34, 0.4);
        border-radius: 8px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: 8px;
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
            box-shadow: 0 0 5px rgba(6, 182, 212, 0.5);
        }
        50% {
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
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
        top: 6px;
        right: 6px;
        background: rgba(6, 182, 212, 0.8);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 3px 6px;
        font-size: 11px;
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
        background: rgba(6, 182, 212, 0.2);
        color: var(--primary-light);
        border: 1px solid var(--primary-color);
    }

    /* ========== SUGGESTED PROMPTS ========== */
    .suggested-prompt {
        background: rgba(22, 32, 50, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.35rem;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .suggested-prompt:hover {
        background: rgba(6, 182, 212, 0.2);
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
        background: rgba(22, 32, 50, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-3px);
        box-shadow: var(--shadow-xl);
    }

    .feature-card-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
        display: block;
    }

    .feature-card-title {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }

    .feature-card-description {
        color: var(--text-secondary);
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* ========== STATS CARD ========== */
    .stats-card {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%);
        border: 1px solid var(--primary-color);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .stats-card:hover {
        transform: scale(1.03);
        box-shadow: var(--shadow-lg);
    }

    .stats-card-value {
        color: var(--primary-light);
        font-size: 1.75rem;
        font-weight: 700;
        display: block;
        margin-bottom: 0.35rem;
    }

    .stats-card-label {
        color: var(--text-secondary);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ========== LOADING SKELETON ========== */
    .skeleton {
        background: linear-gradient(
            90deg,
            rgba(30, 58, 95, 0.4) 0%,
            rgba(22, 32, 50, 0.6) 50%,
            rgba(30, 58, 95, 0.4) 100%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 6px;
    }

    /* ========== TOOL BADGE ========== */
    .tool-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(6, 182, 212, 0.2);
        border: 1px solid var(--primary-color);
        border-radius: 16px;
        padding: 3px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--primary-light);
        margin: 3px;
        transition: all 0.2s ease;
    }

    .tool-badge:hover {
        background: rgba(6, 182, 212, 0.3);
        transform: scale(1.05);
    }

    /* ========== WELCOME SCREEN ========== */
    .welcome-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
    }

    .welcome-title {
        text-align: center;
        margin-bottom: 1.5rem;
    }

    .welcome-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    /* ========== RESPONSIVE DESIGN ========== */

    /* Tablet breakpoint */
    @media (max-width: 1024px) {
        .custom-header {
            padding: 0.875rem 1.25rem 1rem 1.25rem;
        }

        .custom-header h1 {
            font-size: 1.75rem !important;
        }

        .welcome-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }

        .feature-card {
            padding: 0.875rem;
        }

        [data-testid="stMetric"] {
            padding: 0.5rem !important;
            min-height: 65px;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
    }

    /* Mobile landscape breakpoint */
    @media (max-width: 768px) {
        .custom-header {
            padding: 0.75rem 1rem;
            border-radius: 0 0 16px 16px;
        }

        .custom-header h1 {
            font-size: 1.5rem !important;
        }

        .custom-header p {
            font-size: 0.9rem !important;
        }

        .stChatMessage {
            padding: 0.75rem !important;
            margin: 0.35rem 0 !important;
            border-radius: 10px !important;
        }

        .welcome-grid {
            grid-template-columns: 1fr;
            gap: 0.6rem;
        }

        .feature-card {
            padding: 0.75rem;
            margin: 0.35rem 0;
        }

        .suggested-prompt {
            padding: 0.6rem 0.75rem;
            margin: 0.25rem;
        }

        .stButton button {
            width: 100% !important;
            padding: 0.6rem 1rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }

        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
            display: none;
        }

        .quick-start-container {
            padding: 1rem;
            margin: 1rem 0;
        }

        .onboarding-step {
            padding: 0.6rem;
        }

        [data-testid="stMetric"] {
            padding: 0.4rem !important;
            min-height: 60px;
        }
    }

    /* Mobile portrait breakpoint */
    @media (max-width: 480px) {
        .custom-header {
            padding: 0.6rem 0.75rem;
            margin: -1rem -1rem 0.75rem -1rem;
            border-radius: 0 0 12px 12px;
        }

        .custom-header h1 {
            font-size: 1.25rem !important;
        }

        .custom-header p {
            font-size: 0.8rem !important;
            margin-top: 0.15rem !important;
        }

        .stChatMessage {
            padding: 0.6rem !important;
            margin: 0.25rem 0 !important;
            border-radius: 8px !important;
        }

        .stChatMessage p {
            font-size: 0.9rem !important;
        }

        .feature-card {
            padding: 0.6rem;
        }

        .feature-card-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }

        .feature-card-title {
            font-size: 1rem;
        }

        .feature-card-description {
            font-size: 0.85rem;
        }

        .suggested-prompt {
            padding: 0.5rem 0.6rem;
        }

        .suggested-prompt-icon {
            font-size: 1.25rem;
        }

        .suggested-prompt-text {
            font-size: 0.85rem;
        }

        .welcome-container {
            padding: 0.5rem;
        }

        .welcome-title {
            margin-bottom: 1rem;
        }

        .stats-card {
            padding: 0.75rem;
        }

        .stats-card-value {
            font-size: 1.5rem;
        }

        .stats-card-label {
            font-size: 0.75rem;
        }

        .quick-start-container {
            padding: 0.75rem;
            border-radius: 12px;
        }

        .quick-start-title {
            font-size: 1rem;
        }

        .onboarding-step {
            padding: 0.5rem;
            gap: 0.6rem;
        }

        .onboarding-number {
            width: 24px;
            height: 24px;
            font-size: 0.8rem;
        }

        .onboarding-title {
            font-size: 0.9rem;
        }

        .onboarding-text {
            font-size: 0.8rem;
        }

        [data-testid="stSidebar"] {
            width: 100% !important;
        }

        [data-testid="stMetric"] {
            padding: 0.35rem !important;
            min-height: 55px;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.7rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1rem !important;
        }
    }

    /* ========== QA ACTION CARDS ========== */
    .qa-action-card {
        background: linear-gradient(135deg, rgba(22, 32, 50, 0.8) 0%, rgba(30, 58, 95, 0.6) 100%);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.35rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .qa-action-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.2);
    }

    .qa-action-icon {
        font-size: 2rem;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .qa-action-content {
        flex: 1;
    }

    .qa-action-title {
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .qa-action-description {
        color: var(--text-muted);
        font-size: 0.85rem;
        line-height: 1.4;
    }

    /* ========== QUICK START SECTION ========== */
    .quick-start-container {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(20, 184, 166, 0.05) 100%);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 1rem 0;
    }

    .quick-start-title {
        color: var(--primary-light);
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ========== HELP TOOLTIP ========== */
    .help-bubble {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        background: rgba(6, 182, 212, 0.2);
        border-radius: 50%;
        color: var(--primary-light);
        font-size: 0.7rem;
        cursor: help;
        margin-left: 0.4rem;
    }

    .help-bubble:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        padding: 0.5rem 1rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 0.85rem;
        white-space: nowrap;
        z-index: 1000;
        box-shadow: var(--shadow-lg);
    }

    /* ========== COMPACT SIDEBAR SECTIONS ========== */
    .sidebar-section {
        background: rgba(22, 32, 50, 0.4);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }

    .sidebar-section-title {
        color: var(--text-primary);
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* ========== SIMPLE PROMPT CARDS ========== */
    .prompt-card {
        background: rgba(22, 32, 50, 0.6);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .prompt-card:hover {
        background: rgba(6, 182, 212, 0.15);
        border-color: var(--primary-color);
    }

    .prompt-card-text {
        color: var(--text-primary);
        font-size: 0.95rem;
    }

    /* ========== ONBOARDING STEPS ========== */
    .onboarding-step {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem;
        background: rgba(22, 32, 50, 0.4);
        border-radius: 10px;
        margin: 0.35rem 0;
    }

    .onboarding-number {
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 0.9rem;
        flex-shrink: 0;
    }

    .onboarding-content {
        flex: 1;
    }

    .onboarding-title {
        color: var(--text-primary);
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .onboarding-text {
        color: var(--text-muted);
        font-size: 0.9rem;
    }

    /* ========== COMPACT BUTTONS ========== */
    .compact-btn-group {
        display: flex;
        gap: 0.4rem;
        flex-wrap: wrap;
    }

    .compact-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.75rem;
        background: rgba(30, 58, 95, 0.6);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        color: var(--text-primary);
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .compact-btn:hover {
        background: rgba(6, 182, 212, 0.2);
        border-color: var(--primary-color);
    }

    /* ========== MODE INDICATOR ========== */
    .mode-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: 20px;
        color: white;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* ========== EMPTY STATE ========== */
    .empty-state {
        text-align: center;
        padding: 2rem 1.5rem;
        color: var(--text-muted);
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 0.75rem;
        opacity: 0.5;
    }

    .empty-state-title {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    .empty-state-text {
        font-size: 0.9rem;
        max-width: 400px;
        margin: 0 auto;
    }

    /* ========== GLASSMORPHISM CARDS ========== */
    .glass-card {
        background: rgba(22, 32, 50, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        background: rgba(22, 32, 50, 0.6);
        border-color: rgba(6, 182, 212, 0.4);
        box-shadow: 0 8px 32px rgba(6, 182, 212, 0.15);
    }

    /* ========== GRADIENT TEXT ========== */
    .gradient-text {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ========== ACCENT HIGHLIGHT ========== */
    .accent-highlight {
        position: relative;
    }

    .accent-highlight::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 2px;
    }

    /* ========== PULSE INDICATOR ========== */
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--success-color);
        position: relative;
    }

    .pulse-dot::before {
        content: '';
        position: absolute;
        top: -4px;
        left: -4px;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: var(--success-color);
        opacity: 0.3;
        animation: pulse-ring 1.5s ease-out infinite;
    }

    @keyframes pulse-ring {
        0% {
            transform: scale(0.5);
            opacity: 0.5;
        }
        100% {
            transform: scale(1.5);
            opacity: 0;
        }
    }

    /* ========== IMPROVED SELECT BOXES ========== */
    .stSelectbox > div > div {
        background: rgba(22, 32, 50, 0.6) !important;
        border-color: var(--border-color) !important;
        border-radius: 8px !important;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--primary-color) !important;
    }

    /* ========== IMPROVED TEXT INPUTS ========== */
    .stTextInput > div > div > input {
        background: rgba(22, 32, 50, 0.6) !important;
        border-color: var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.15) !important;
    }

    .stTextArea > div > div > textarea {
        background: rgba(22, 32, 50, 0.6) !important;
        border-color: var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }

    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.15) !important;
    }

    /* ========== IMPROVED SLIDERS ========== */
    .stSlider > div > div > div > div {
        background: var(--primary-color) !important;
    }

    /* ========== DOWNLOAD BUTTONS ========== */
    .stDownloadButton button {
        background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%) !important;
        border: none !important;
        border-radius: 8px !important;
    }

    .stDownloadButton button:hover {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary-color) 100%) !important;
        transform: translateY(-1px) !important;
    }

    /* ========== DIVIDER STYLING ========== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        margin: 1rem 0;
    }

    /* ========== BADGE PILL ========== */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge-pill.primary {
        background: rgba(6, 182, 212, 0.2);
        color: var(--primary-light);
    }

    .badge-pill.success {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success-color);
    }

    .badge-pill.warning {
        background: rgba(245, 158, 11, 0.2);
        color: var(--warning-color);
    }

    .badge-pill.accent {
        background: rgba(244, 114, 182, 0.2);
        color: var(--accent-color);
    }

    /* ========== ICON BUTTON ========== */
    .icon-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: rgba(22, 32, 50, 0.6);
        border: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .icon-btn:hover {
        background: rgba(6, 182, 212, 0.2);
        border-color: var(--primary-color);
    }

    /* ========== NOTIFICATION DOT ========== */
    .notification-dot {
        position: absolute;
        top: -2px;
        right: -2px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-color);
        border: 2px solid var(--bg-primary);
    }

    /* ========== SMOOTH TRANSITIONS FOR ALL ========== */
    * {
        transition-property: background-color, border-color, box-shadow, transform;
        transition-duration: 0.2s;
        transition-timing-function: ease;
    }

    /* Exclude animations from transition */
    .fade-in, .slide-in, .slide-up, .float, .glow {
        transition: none;
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
