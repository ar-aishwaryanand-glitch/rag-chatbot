#!/bin/bash

# RAG Agent Assistant - Setup Script for Linux/Mac
# Usage: chmod +x setup.sh && ./setup.sh

set -e

echo "=========================================="
echo "  RAG Agent Assistant - Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}Error: Python not found. Please install Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

# Check if version is 3.9+
MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
    echo -e "${RED}Error: Python 3.9+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping creation.${NC}"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo -e "${GREEN}Dependencies installed.${NC}"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# RAG Agent Assistant - Environment Variables
# Fill in your API keys below

# Required: OpenAI API Key
# Get your key at: https://platform.openai.com/api-keys
OPENAI_API_KEY=

# Optional: Web Search (Tavily)
# Get your key at: https://tavily.com
TAVILY_API_KEY=

# Optional: News API
# Get your key at: https://newsapi.org
NEWSAPI_KEY=

# Optional: Confluence Integration
# CONFLUENCE_URL=https://your-domain.atlassian.net
# CONFLUENCE_USERNAME=your-email@example.com
# CONFLUENCE_API_TOKEN=your-api-token

# Optional: PostgreSQL Database (default: SQLite)
# DATABASE_URL=postgresql://user:password@host:5432/database

# Feature Flags
CODE_EXECUTOR_ENABLED=false
FILE_OPS_ENABLED=false
EOF
    echo -e "${GREEN}.env file created.${NC}"
    echo -e "${YELLOW}Please edit .env and add your OPENAI_API_KEY${NC}"
else
    echo -e "${YELLOW}.env file already exists. Skipping.${NC}"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/documents
mkdir -p data/vectorstore
mkdir -p data/checkpoints
echo -e "${GREEN}Data directories created.${NC}"

# Verify installation
echo ""
echo "Verifying installation..."
$PYTHON_CMD -c "from src.agent import AgentExecutor; print('Agent module OK')" 2>/dev/null && \
    echo -e "${GREEN}Installation verified.${NC}" || \
    echo -e "${YELLOW}Warning: Could not verify installation. Check .env file.${NC}"

# Done
echo ""
echo "=========================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env file and add your OPENAI_API_KEY"
echo "  2. Activate the environment: source venv/bin/activate"
echo "  3. Run the app: make run"
echo ""
echo "Or run directly:"
echo "  source venv/bin/activate && streamlit run src/ui/streamlit_app_agent.py"
echo ""
