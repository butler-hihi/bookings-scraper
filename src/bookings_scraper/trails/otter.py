"""Otter Trail scraper for SANParks."""

import json
import logging
import time
from datetime import date, datetime
from typing import Optional

import cloudscraper
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from bookings_scraper.trails.base import BaseTrail
from bookings_scraper.utils.logging import get_logger

logger = get_logger(__name__)


class OtterTrail(BaseTrail):
    """Scraper for SANParks Otter Trail availability.

    Uses the official SANParks API endpoint to extract availability.
    The API returns comma-separated availability data: "date_slots"
    """

    # SANParks API endpoint for Otter Trail (parkID=113 is Garden Route / Tsitsikamma)
    OTTER_API_URL = "https://www.sanparks.org/includes/SANParksApp/API/v1/bookings/activities/getTrails.php?parkID=113"

    def __init__(self, config: dict) -> None:
        """Initialize OtterTrail scraper.

        Args:
            config: Trail configuration dictionary
        """
        super().__init__(config)
        self.default_date_range = 180  # Days

    def get_config(self) -> dict:
        """Get configuration for this trail.

        Returns:
            Trail configuration dictionary
        """
        return self.config

    # Class-level scraper instance to persist Cloudflare clearance
    _scraper: cloudscraper.CloudScraper | None = None

    def _get_scraper(self) -> cloudscraper.CloudScraper:
        """Get or create a cloudscraper instance with Cloudflare clearance.

        Returns:
            Configured cloudscraper instance with Cloudflare clearance
        """
        if self._scraper is None:
            self._scraper = cloudscraper.create_scraper(
                browser={
                    "browser": "chrome",
                    "platform": "darwin",
                    "desktop": True,
                    "mobile": False,
                }
            )
            # First visit the main site to get Cloudflare clearance
            self._scraper.get("https://www.sanparks.org/", timeout=30)
        return self._scraper

    @retry(
        retry=retry_if_exception_type((json.JSONDecodeError, Exception)),
        stop=stop_after_attempt(5),
    )
    def _get_availability_raw(self) -> str:
        """Fetch raw availability data from SANParks API.

        Returns:
            Comma-separated availability string from API
        """
        scraper = self._get_scraper()
        time.sleep(1)  # Add delay to avoid rate limiting

        response = scraper.get(self.OTTER_API_URL, timeout=30)
        response.raise_for_status()

        return response.json().get("DATA", [])[0].get("Availability", [])

    def fetch_availability(self) -> list[dict]:
        """Fetch availability data from the Otter Trail API.

        Returns:
            List of availability records with keys:
            - date: Date string in YYYY-MM-DD format
            - available: Boolean availability status
            - metadata: Additional metadata
        """
        try:
            logger.info("Attempting to retrieve availability from SANParks...")

            availability_raw = self._get_availability_raw()
            availability_parsed = sorted(availability_raw.split(","))

            if not availability_parsed or availability_parsed == [""]:
                logger.warning("No availability data returned from API")
                return []

            availability_records = []
            for availability in availability_parsed:
                if not availability:
                    continue
                parts = availability.split("_")
                if len(parts) >= 2:
                    date_str = parts[0]
                    slots = int(parts[1])
                    availability_records.append(
                        {"date": date_str, "available": slots > 0, "metadata": {"slots": slots}}
                    )

            logger.info(f"Successfully parsed {len(availability_records)} availability records")
            return availability_records

        except Exception as e:
            logger.error(f"Error fetching Otter Trail availability: {e}")
            return []

    def get_availability_by_date(self) -> dict[date, int]:
        """Get availability as a dictionary mapping dates to slot counts.

        Returns:
            Dictionary mapping dates to number of available slots
        """
        availability = self.fetch_availability()
        result = {}
        for record in availability:
            try:
                date_obj = datetime.strptime(record["date"], "%Y-%m-%d").date()
                result[date_obj] = record["metadata"]["slots"]
            except (ValueError, KeyError):
                continue
        return result
