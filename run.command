#!/bin/bash

# RAG Agent Assistant - macOS Launcher
# Double-click this file in Finder to start the app

# Navigate to the project directory (where this script lives)
cd "$(dirname "$0")"

echo "=========================================="
echo "  RAG Agent Assistant - Starting..."
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Run setup first:  chmod +x setup.sh && ./setup.sh"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the Streamlit app
streamlit run src/ui/streamlit_app_agent.py
