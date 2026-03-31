"""Abstract base class for trail implementations."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from bookings_scraper.utils.logging import get_logger

logger = get_logger(__name__)


class BaseTrail(ABC):
    """Abstract base class for trail scrapers.

    Each trail subclass must implement:
    - get_config() -> TrailConfig
    - fetch_availability() -> List[AvailabilityRecord]
    """

    def __init__(self, config: dict) -> None:
        """Initialize the trail scraper.

        Args:
            config: Configuration dictionary for this trail
        """
        self.config = config
        self.name = config.get("slug", config.get("name", "unknown"))
        self.display_name = config.get("display_name", self.name.title())
        self.enabled = config.get("enabled", True)
        self.endpoint = config.get("endpoint", "auto")
        self.check_interval = config.get("check_interval", 300)

        logger.info(f"Initialized {self.display_name} (slug: {self.name})")

    @abstractmethod
    def get_config(self) -> dict:
        """Get configuration for this trail.

        Returns:
            Dictionary with trail configuration
        """
        pass

    @abstractmethod
    def fetch_availability(self) -> list[dict]:
        """Fetch availability data from the trail's source.

        Returns:
            List of availability records with keys:
            - date: Date string in YYYY-MM-DD format
            - available: Boolean availability status
            - metadata: Additional metadata
        """
        pass

    def check_availability(self) -> Optional[dict]:
        """Main check method - calls fetch_availability and returns results.

        Returns:
            Dict with 'trail', 'status', 'results' keys, or None if disabled
        """
        if not self.enabled:
            logger.debug(f"Skipping {self.display_name} (disabled)")
            return None

        try:
            logger.info(f"Fetching availability for {self.display_name}")
            results = self.fetch_availability()

            if results:
                return {
                    "trail": self.name,
                    "status": "success",
                    "count": len(results),
                    "results": results,
                }
            else:
                logger.warning(f"No availability data for {self.display_name}")
                return {"trail": self.name, "status": "no_data", "count": 0}

        except Exception as e:
            logger.error(f"Error checking {self.display_name}: {e}")
            return {"trail": self.name, "status": "error", "error": str(e)}

    def get_name(self) -> str:
        """Get the trail name.

        Returns:
            Trail name
        """
        return self.name
