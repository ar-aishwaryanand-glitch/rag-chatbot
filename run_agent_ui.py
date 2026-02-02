"""
Streamlit UI launcher for RAG Agent with Phase 3 features.

This script launches the enhanced Streamlit web interface with:
- Memory-enabled agent
- Self-reflection capabilities
- Multi-tool intelligent routing
- Learning and performance tracking

Usage:
    streamlit run run_agent_ui.py

    Or with custom settings:
    streamlit run run_agent_ui.py --server.port 8502
    streamlit run run_agent_ui.py --server.address 0.0.0.0
"""

import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the agent Streamlit app
from src.ui.streamlit_app_agent import main

if __name__ == "__main__":
    main()
