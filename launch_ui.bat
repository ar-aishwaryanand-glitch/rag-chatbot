@echo off
REM Streamlit UI Launcher for RAG Agent (Windows)
REM Usage: launch_ui.bat [port]

SET PORT=%1
IF "%PORT%"=="" SET PORT=8501

echo ================================
echo   RAG Chat Assistant - Web UI
echo ================================
echo.

REM Check if streamlit is installed
streamlit --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Installing Streamlit...
    pip install streamlit
    echo.
)

REM Check if .env file exists
IF NOT EXIST ".env" (
    echo Warning: .env file not found
    echo Create .env from .env.example and add your GOOGLE_API_KEY
    echo.
)

REM Launch Streamlit
echo Launching Streamlit UI on port %PORT%...
echo Opening browser at: http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run run_ui.py --server.port %PORT%
