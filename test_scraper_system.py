#!/usr/bin/env python3
"""Test script for the BookingsScraper - runs with system Python."""

import sys
import time

# Ensure we're using system Python
assert "/usr/bin/python3" in sys.executable, f"Expected system Python, got {sys.executable}"

import cloudscraper


def test_otter_scraper():
    """Test the Otter Trail scraper using cloudscraper."""
    print("Testing Otter Trail scraper with system Python...")
    print(f"Python: {sys.version}")
    print()

    url = "https://www.sanparks.org/includes/SANParksApp/API/v1/bookings/activities/getTrails.php?parkID=113"

    # Create scraper with browser emulation
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "darwin",
            "desktop": True,
            "mobile": False,
        }
    )

    # First visit main site to get Cloudflare clearance
    print("Getting Cloudflare clearance...")
    response = scraper.get("https://www.sanparks.org/", timeout=30)
    print(f"Clearance status: {response.status_code}")

    if response.status_code != 200:
        print("Failed to get Cloudflare clearance!")
        return False

    time.sleep(2)  # Wait for clearance to settle

    # Now fetch the API
    print()
    print("Fetching availability from API...")
    response = scraper.get(url, timeout=30)
    print(f"API status: {response.status_code}")

    if response.status_code != 200:
        print(f"API request failed with status {response.status_code}")
        return False

    data = response.json()

    if data.get("STATUS") != "OK":
        print(f"API Error: {data.get('MESSAGE')}")
        return False

    # Parse availability
    availability_raw = data["DATA"][0]["Availability"]
    availability_parsed = sorted(availability_raw.split(","))

    print(f"Total dates in system: {len(availability_parsed)}")
    print()

    # Find available dates (slots > 0)
    available = []
    for item in availability_parsed:
        parts = item.split("_")
        if len(parts) == 2 and int(parts[1]) > 0:
            available.append((parts[0], int(parts[1])))

    print(f"Available dates: {len(available)}")
    if available:
        print()
        print("Available bookings:")
        for date_str, slots in available[:10]:
            print(f"  {date_str}: {slots} slots")
        if len(available) > 10:
            print(f"  ... and {len(available) - 10} more")
    else:
        print("No availability at the moment.")

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
