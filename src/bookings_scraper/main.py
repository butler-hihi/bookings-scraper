"""Main entry point for the BookingsScraper application."""

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from bookings_scraper.config import load_trail_configs
from bookings_scraper.database import get_availability, init_database
from bookings_scraper.notifier import WhatsAppNotifier
from bookings_scraper.scheduler import Scheduler
from bookings_scraper.trails.base import BaseTrail

# Import trail implementations
from bookings_scraper.trails.otter import OtterTrail
from bookings_scraper.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SANParks Booking Availability Monitor")
    parser.add_argument(
        "--trails-config",
        type=str,
        default="config/trails.yaml",
        help="Path to trails configuration file",
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Check interval in seconds (default: 60)"
    )
    parser.add_argument("--service", action="store_true", help="Run as a background service")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    parser.add_argument(
        "--db-path", type=str, default=None, help="Path to database file (overrides config)"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.service else "INFO"
    setup_logging(log_level)

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Load trail configurations
    trails_config = load_trail_configs(args.trails_config)

    # Create trail instances
    trails: list[BaseTrail] = []

    for trail_config in trails_config:
        if trail_config.get("enabled", True):
            try:
                trail = OtterTrail(trail_config)
                trails.append(trail)
                logger.info(f"Loaded trail: {trail.display_name}")
            except Exception as e:
                logger.error(f"Failed to initialize trail {trail_config.get('name')}: {e}")

    if not trails:
        logger.error("No trails loaded - check configuration file")
        return

    # Initialize database
    db_path = Path(args.db_path) if args.db_path else Path("data/bookings.db")
    init_database(db_path)
    logger.info(f"Database initialized: {db_path}")

    # Create notifier
    notifier = WhatsAppNotifier()
    logger.info("WhatsApp notifier initialized")

    # Create scheduler
    scheduler = Scheduler(trails)

    # Run once or in loop
    if args.once:
        result = scheduler.run_once()
        _handle_result(result, notifier)
        logger.info("Single check completed")

    else:
        # Run in loop
        scheduler.run_loop(interval_seconds=args.interval)
        logger.info("Scheduler running in background")


def _handle_result(result: dict, notifier: WhatsAppNotifier) -> None:
    """Handle the result of an availability check.

    Args:
        result: Result dictionary from scheduler
        notifier: WhatsApp notifier instance
    """
    changes = result.get("changes", {})

    if changes.get("newly_available") or changes.get("newly_unavailable"):
        # Send notification
        trail_name = result.get("trail", "unknown")
        newly_available = changes.get("newly_available", [])
        newly_unavailable = changes.get("newly_unavailable", [])

        if newly_available:
            newly_available.sort()
        if newly_unavailable:
            newly_unavailable.sort()

        from datetime import datetime

        checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Sending notification for {trail_name}")

        # Use the database change detection
        db_changes = get_availability(
            trail_name=trail_name, date=changes.get("date", ""), db_path=Path("data/bookings.db")
        )

        if db_changes:
            # Extract actual changes
            notification_changes = _detect_actual_changes(
                trail_name=trail_name,
                results=result.get("results", {}),
                db_path=Path("data/bookings.db"),
            )

            # Send notification if there are changes
            if notification_changes:
                message = notifier.send_whatsapp(notification_changes)

                if message:
                    logger.info("WhatsApp notification sent")
                else:
                    logger.warning("Failed to send WhatsApp notification")


def _detect_actual_changes(trail_name: str, results: dict, db_path: Path) -> str:
    """Detect actual availability changes for notification.

    Args:
        trail_name: Name of the trail
        results: Results from the check
        db_path: Path to database

    Returns:
        Formatted message string
    """
    changes = {"newly_available": [], "newly_unavailable": []}

    # Get stored records
    stored_records = get_availability(trail_name=trail_name, db_path=db_path)

    stored_dates = {record.date: record.available for record in stored_records}

    # Get current availability from results
    current_dates = results.get("results", [])
    current_availability = {item["date"]: item["available"] for item in current_dates}

    # Compare and detect changes
    for date, available in current_availability.items():
        if date not in stored_dates:
            if available:
                changes["newly_available"].append(date)
            else:
                changes["newly_unavailable"].append(date)

    for date, available in stored_dates.items():
        if date in current_availability:
            if current_availability[date] != available:
                if available:
                    changes["newly_unavailable"].append(f"{date} (was available)")
                else:
                    changes["newly_available"].append(f"{date} (was unavailable)")

    # Format message
    if changes["newly_available"] or changes["newly_unavailable"]:
        message = f"📍 {trail_name.title()} Trail Availability Update\n\n"

        if changes["newly_available"]:
            message += "🟢 Newly Available:\n"
            for date in sorted(changes["newly_available"]):
                message += f"- {date}\n"

        if changes["newly_unavailable"]:
            message += "\n🔴 No Longer Available:\n"
            for date in sorted(changes["newly_unavailable"]):
                message += f"- {date}\n"

        message += f"\n⏱ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return message

    return ""


if __name__ == "__main__":
    main()
