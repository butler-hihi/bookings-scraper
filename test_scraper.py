#!/usr/bin/env python3
"""Test script for the BookingsScraper."""

import sys
import time
sys.path.insert(0, "src")

import cloudscraper
from bookings_scraper.trails.otter import OtterTrail


def test_otter_scraper():
    """Test the Otter Trail scraper."""
    print("Testing Otter Trail scraper...")
    print()

    # First, get Cloudflare clearance using cloudscraper directly
    print("Getting Cloudflare clearance...")
    clearance_scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "darwin",
            "desktop": True,
            "mobile": False,
        }
    )
    response = clearance_scraper.get("https://www.sanparks.org/", timeout=30)
    print(f"Clearance status: {response.status_code}")
    time.sleep(2)  # Wait for clearance to settle
    print()

    # Now create the scraper and test
    config = {"name": "otter", "enabled": True}
    scraper = OtterTrail(config)

    # Use the same scraper instance for clearance
    OtterTrail._scraper = clearance_scraper

    print(f"Scraper created: {scraper}")
    print(f"API URL: {scraper.OTTER_API_URL}")
    print()

    # Fetch availability
    print("Fetching availability...")
    availability = scraper.fetch_availability()

    print(f"Got {len(availability)} records")
    print()

    # Show available dates
    available_dates = [r for r in availability if r.get("available")]
    print(f"Available dates: {len(available_dates)}")

    if available_dates:
        print("\nAvailable bookings:")
        for record in available_dates[:10]:
            print(f"  {record['date']}: {record['metadata']['slots']} slots")

    if len(available_dates) > 10:
        print(f"  ... and {len(available_dates) - 10} more")

    # Test get_availability_by_date
    print()
    print("Testing get_availability_by_date()...")
    by_date = scraper.get_availability_by_date()
    print(f"Got {len(by_date)} dates with slots > 0")

    return True


if __name__ == "__main__":
    try:
        success = test_otter_scraper()
        print()
        print("✅ Test passed!" if success else "❌ Test failed")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
