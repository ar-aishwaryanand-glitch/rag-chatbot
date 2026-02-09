# QA RAG System - Makefile
# Run common tasks easily

.PHONY: run test clean setup help

# Default target
help:
	@echo "QA RAG System - Available commands:"
	@echo ""
	@echo "  make run          - Start the Streamlit app"
	@echo "  make test         - Run all tests"
	@echo "  make test-quick   - Run quick unit tests only"
	@echo "  make setup        - Initialize database"
	@echo "  make reindex      - Reindex all documents"
	@echo "  make check        - Check backend status"
	@echo "  make clean        - Clean cache files"
	@echo "  make lint         - Check code style"
	@echo ""

# Start the application
run:
	streamlit run src/ui/streamlit_app_agent.py

# Run all tests
test:
	pytest tests/ -v

# Run quick tests only
test-quick:
	pytest tests/unit/ -v --tb=short

# Setup database
setup:
	python scripts/setup/init_database.py

# Reindex documents
reindex:
	python scripts/maintenance/reindex_documents.py

# Check backend status
check:
	python scripts/monitoring/check_backend_status.py

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true

# Check code style
lint:
	python -m py_compile src/ui/streamlit_app_agent.py
	python -m py_compile src/agent/manager_agent.py
	python -m py_compile src/agent/specialized_agents.py
	@echo "Syntax check passed"
