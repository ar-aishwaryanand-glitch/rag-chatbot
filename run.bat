@echo off
REM RAG Agent Assistant - Run Script for Windows
REM Usage: Double-click run.bat

echo Starting RAG Agent Assistant...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the app
streamlit run src/ui/streamlit_app_agent.py

pause
