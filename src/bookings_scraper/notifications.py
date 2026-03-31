"""Notification configuration loader."""

from pathlib import Path
from typing import Optional

import yaml

from bookings_scraper.utils.logging import get_logger

logger = get_logger(__name__)


class NotificationConfig:
    """Configuration for notifications."""

    def __init__(self) -> None:
        """Initialize notification config from YAML file."""
        self.default_numbers: list[str] = []
        self.allow_self_subscribe: bool = False
        self.subscribe_password: str = ""
        self._load_config()

    def _load_config(self) -> None:
        """Load notification config from file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "notifications.yaml"

        if not config_path.exists():
            logger.warning(f"Notification config not found: {config_path}")
            return

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            self.default_numbers = data.get("default_numbers", [])
            self.allow_self_subscribe = data.get("allow_self_subscribe", False)
            self.subscribe_password = data.get("subscribe_password", "")

            logger.debug(f"Loaded notification config: {len(self.default_numbers)} default numbers")

        except Exception as e:
            logger.error(f"Failed to load notification config: {e}")

    def validate_password(self, password: str) -> bool:
        """Validate subscription password.

        Args:
            password: Password to validate

        Returns:
            True if password is valid
        """
        if not self.subscribe_password:
            return True
        return password == self.subscribe_password

    def get_default_numbers(self) -> list[str]:
        """Get default notification numbers.

        Returns:
            List of phone numbers
        """
        return self.default_numbers.copy()


# Global config instance
_notification_config: Optional[NotificationConfig] = None


def get_notification_config() -> NotificationConfig:
    """Get the notification config singleton.

    Returns:
        NotificationConfig instance
    """
    global _notification_config
    if _notification_config is None:
        _notification_config = NotificationConfig()
    return _notification_config
