# BookingsScraper Justfile
# Run just --list to see available recipes

# List all Python source files
list:
    @echo "=== Source Code ==="
    @find src -name "*.py" -type f
    @echo ""
    @echo "=== Tests ==="
    @find tests -name "*.py" -type f

# Run tests with pytest
test:
    poetry run pytest -v

# Run tests with coverage
test-cov:
    poetry run pytest --cov=src --cov-report=term-missing

# Run the scraper
run:
    poetry run python -m bookings_scraper.main

# Format code and check linting
lint:
    poetry run ruff check src/ tests/
    poetry run ruff format --check src/ tests/

# Format code (auto-fix issues)
fmt:
    poetry run ruff format src/ tests/
    poetry run ruff check --fix src/ tests/

# Install dependencies
install:
    poetry install

# Shell into the virtual environment
shell:
    poetry shell
