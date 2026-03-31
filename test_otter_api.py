#!/usr/bin/env python3
"""Test script for SANParks Otter Trail API."""

import json
import sys
import time

import cloudscraper


def test_otter_availability():
    """Test the Otter Trail availability endpoint."""
    url = "https://www.sanparks.org/includes/SANParksApp/API/v1/bookings/activities/getTrails.php?parkID=113"

    print("Testing SANParks Otter Trail API...")
    print(f"URL: {url}")
    print()

    # Create scraper
    scraper = cloudscraper.create_scraper()

    # Add delay to avoid rate limiting
    time.sleep(1)

    try:
        # Make request
        response = scraper.get(url, timeout=30)
        response.raise_for_status()

        print(f"Status: {response.status_code}")
        print()

        # Parse JSON
        data = response.json()

        if data.get("STATUS") != "OK":
            print(f"API Error: {data.get('MESSAGE')}")
            return False

        # Extract availability data
        availability_raw = data["DATA"][0]["Availability"]
        availability_parsed = sorted(availability_raw.split(","))

        print(f"Total dates in system: {len(availability_parsed)}")
        print()

        # Find available dates (slots > 0)
        available = []
        for item in availability_parsed:
            parts = item.split("_")
            if len(parts) == 2:
                date_str, slots_str = parts
                slots = int(slots_str)
                if slots > 0:
                    available.append((date_str, slots))

        print(f"Available dates: {len(available)}")
        if available:
            print()
            print("Available Bookings:")
            for date_str, slots in available:
                print(f"  {date_str}: {slots} slots")
        else:
            print("No availability at the moment.")

        return True

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = test_otter_availability()
    sys.exit(0 if success else 1)
