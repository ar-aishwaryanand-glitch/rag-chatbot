"""
Streamlit UI launcher for RAG Agent POC.

This script launches the Streamlit web interface for the RAG system.

Usage:
    streamlit run run_ui.py

    Or with custom settings:
    streamlit run run_ui.py --server.port 8502
    streamlit run run_ui.py --server.address 0.0.0.0
"""

import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main Streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main()
