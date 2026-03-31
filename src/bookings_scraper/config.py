"""Configuration loader for trail definitions."""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from bookings_scraper.utils.logging import get_logger

logger = get_logger(__name__)


def load_trail_configs(config_path: str) -> list[dict]:
    """Load trail configurations from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        List of trail configuration dictionaries
    """
    # Get absolute path
    base_dir = Path(__file__).parent.parent.parent
    config_file = base_dir / config_path

    if not config_file.exists():
        logger.warning(f"Config file not found: {config_file}")
        return []

    with open(config_file) as f:
        data = yaml.safe_load(f)

    trails = data.get("trails", [])

    # Normalize each trail config
    configs = []
    for trail in trails:
        config = {
            "name": trail.get("name"),
            "enabled": trail.get("enabled", True),
            "type": trail.get("type", "sanparks"),
            "slug": trail.get("slug", trail.get("name", "unknown")),
            "display_name": trail.get("display_name", trail.get("name", "Trail")),
            "endpoint": trail.get("endpoint", "auto"),
            "check_interval": trail.get("check_interval", 300),
            "priority": trail.get("priority", 1),
        }
        configs.append(config)
        logger.debug(f"Loaded config for trail: {config['name']}")

    return configs


def get_trail_by_slug(slug: str) -> Optional[dict]:
    """Get trail configuration by slug.

    Args:
        slug: Trail slug identifier

    Returns:
        Trail configuration dict or None if not found
    """
    # Load configs
    configs = load_trail_configs("config/trails.yaml")

    for config in configs:
        if config.get("slug") == slug:
            return config

    return None
