#!/usr/bin/env python3
"""Run the BookingsScraper using system Python.

This script bypasses Poetry's Python 3.14 which has SSL issues,
and uses system Python 3.9 which works correctly with cloudscraper.
"""

import subprocess
import sys

# Ensure we're using system Python 3.9
SYSTEM_PYTHON = "/usr/bin/python3"

def main():
    """Run the scraper test with system Python."""
    print(f"Using Python: {SYSTEM_PYTHON}")
    print(f"Version: {subprocess.check_output([SYSTEM_PYTHON, '--version'], text=True).strip()}")
    print()

    # Run the test
    result = subprocess.run(
        [SYSTEM_PYTHON, "test_scraper_system.py"],
        cwd="/Users/alistairyan/.openclaw/workspace/BookingsScraperV1"
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
