# BookingsScraper Justfile
# Run just --list to see available recipes

# System Python (use instead of Poetry which has SSL issues on this machine)
PYTHON := "/usr/bin/python3"
PYTHONPATH := "src"

# List all Python source files
list:
    @echo "=== Source Code ==="
    @find src -name "*.py" -type f | sort
    @echo ""
    @echo "=== Tests ==="
    @find tests -name "*.py" -type f | sort

# Run tests with pytest
test:
    PYTHONPATH={{PYTHONPATH}} {{PYTHON}} -m pytest tests/ -v

# Run tests with coverage
test-cov:
    PYTHONPATH={{PYTHONPATH}} {{PYTHON}} -m pytest --cov=src --cov-report=term-missing tests/

# Run the scraper (single check)
run:
    PYTHONPATH={{PYTHONPATH}} {{PYTHON}} -m bookings_scraper.main --once

# Run the scraper as a service (continuous)
serve:
    PYTHONPATH={{PYTHONPATH}} {{PYTHON}} -m bookings_scraper.main --service --interval 300

# Format code and check linting
lint:
    {{PYTHON}} -m ruff check src/ tests/
    {{PYTHON}} -m ruff format --check src/ tests/

# Format code (auto-fix issues)
fmt:
    {{PYTHON}} -m ruff format src/ tests/
    {{PYTHON}} -m ruff check --fix src/ tests/

# Install dependencies (using system Python)
install:
    {{PYTHON}} -m pip install cloudscraper tenacity pytest pytest-cov sqlalchemy pyyaml python-dotenv requests ruff

# Shell into Python REPL
shell:
    {{PYTHON}}
