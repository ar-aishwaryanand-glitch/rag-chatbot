@echo off
REM RAG Agent Assistant - Setup Script for Windows
REM Usage: Double-click setup.bat or run from command prompt

echo ==========================================
echo   RAG Agent Assistant - Setup
echo ==========================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip -q

REM Install dependencies
echo.
echo Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt -q
echo Dependencies installed.

REM Create .env file if it doesn't exist
echo.
if not exist ".env" (
    echo Creating .env file...
    (
        echo # RAG Agent Assistant - Environment Variables
        echo # Fill in your API keys below
        echo.
        echo # Required: OpenAI API Key
        echo # Get your key at: https://platform.openai.com/api-keys
        echo OPENAI_API_KEY=
        echo.
        echo # Optional: Web Search ^(Tavily^)
        echo # Get your key at: https://tavily.com
        echo TAVILY_API_KEY=
        echo.
        echo # Optional: News API
        echo # Get your key at: https://newsapi.org
        echo NEWSAPI_KEY=
        echo.
        echo # Optional: Confluence Integration
        echo # CONFLUENCE_URL=https://your-domain.atlassian.net
        echo # CONFLUENCE_USERNAME=your-email@example.com
        echo # CONFLUENCE_API_TOKEN=your-api-token
        echo.
        echo # Optional: PostgreSQL Database ^(default: SQLite^)
        echo # DATABASE_URL=postgresql://user:password@host:5432/database
        echo.
        echo # Feature Flags
        echo CODE_EXECUTOR_ENABLED=false
        echo FILE_OPS_ENABLED=false
    ) > .env
    echo .env file created.
    echo IMPORTANT: Please edit .env and add your OPENAI_API_KEY
) else (
    echo .env file already exists. Skipping.
)

REM Create data directories
echo.
echo Creating data directories...
if not exist "data\documents" mkdir data\documents
if not exist "data\vectorstore" mkdir data\vectorstore
if not exist "data\checkpoints" mkdir data\checkpoints
echo Data directories created.

REM Verify installation
echo.
echo Verifying installation...
python -c "from src.agent import AgentExecutor; print('Agent module OK')" 2>nul
if errorlevel 1 (
    echo Warning: Could not verify installation. Check .env file.
) else (
    echo Installation verified.
)

REM Done
echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Edit .env file and add your OPENAI_API_KEY
echo   2. Run the app: run.bat
echo.
echo Or run directly:
echo   venv\Scripts\activate.bat
echo   streamlit run src/ui/streamlit_app_agent.py
echo.

pause
