#!/bin/bash
# Streamlit UI Launcher for RAG Agent
# Usage: ./launch_ui.sh [port]

# Set default port
PORT=${1:-8501}

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  RAG Chat Assistant - Web UI  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit not found. Installing...${NC}"
    pip3 install streamlit
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "   Create .env from .env.example and add your GOOGLE_API_KEY"
    echo ""
fi

# Launch Streamlit
echo -e "${GREEN}🚀 Launching Streamlit UI on port ${PORT}...${NC}"
echo -e "${GREEN}📱 Opening browser at: http://localhost:${PORT}${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

streamlit run run_ui.py --server.port $PORT
