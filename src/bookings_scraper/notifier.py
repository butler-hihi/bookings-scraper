"""WhatsApp notification handler."""

import logging
from typing import Optional

from bookings_scraper.database import get_active_subscribers, get_subscriber_count
from bookings_scraper.notifications import get_notification_config
from bookings_scraper.utils.logging import get_logger

logger = logging.getLogger(__name__)


class WhatsAppNotifier:
    """Handle WhatsApp notifications via OpenClaw.

    Uses the OpenClaw WhatsApp gateway integration.
    Supports multiple recipients from config and database subscribers.
    """

    def __init__(self, channel: str = "main"):
        """Initialize the notifier.

        Args:
            channel: WhatsApp channel identifier
        """
        self.channel = channel
        self.config = get_notification_config()
        logger.info(f"WhatsAppNotifier initialized with channel: {channel}")

    def get_recipients(self) -> list[str]:
        """Get list of notification recipients.

        Combines default numbers from config with active subscribers from database.

        Returns:
            List of phone numbers
        """
        recipients = set()

        # Add default numbers from config
        for number in self.config.get_default_numbers():
            recipients.add(number)

        # Add active subscribers from database
        try:
            subscribers = get_active_subscribers()
            for sub in subscribers:
                recipients.add(sub.phone_number)
        except Exception as e:
            logger.warning(f"Could not load subscribers from database: {e}")

        logger.info(f"Notifications will be sent to {len(recipients)} recipients")
        return list(recipients)

    def send_whatsapp(
        self, message: str, recipients: Optional[list[str]] = None
    ) -> dict[str, bool]:
        """Send a WhatsApp notification to recipients.

        Args:
            message: The message to send
            recipients: Optional list of specific recipients. If None, uses all recipients.

        Returns:
            Dict mapping phone numbers to their send status
        """
        if recipients is None:
            recipients = self.get_recipients()

        results = {}
        successful = 0
        failed = 0

        for phone_number in recipients:
            success = self._send_single(phone_number, message)
            results[phone_number] = success
            if success:
                successful += 1
            else:
                failed += 1

        logger.info(f"Sent notification to {successful}/{len(recipients)} recipients")

        if failed > 0:
            logger.warning(f"Failed to send to {failed} recipients")

        return results

    def _send_single(self, phone_number: str, message: str) -> bool:
        """Send a WhatsApp message to a single recipient.

        Args:
            phone_number: Recipient's phone number
            message: Message to send

        Returns:
            True if sent successfully
        """
        try:
            # Use OpenClaw's messaging API to send WhatsApp message
            from openclaw import Gateway

            gateway = Gateway.get()

            # Send via the WhatsApp channel
            result = gateway.post(
                f"/channels/{self.channel}/messages",
                data={
                    "to": phone_number,
                    "text": message,
                },
            )

            if result.get("success"):
                logger.debug(f"WhatsApp message sent to {phone_number}")
                return True
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"WhatsApp send to {phone_number} failed: {error}")
                return False

        except ImportError:
            # Fallback: print to console
            logger.warning(f"OpenClaw not available, printing message to {phone_number}:")
            print(f"[To: {phone_number}] {message}")
            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {phone_number}: {e}")
            return False

    def send_availability_update(
        self,
        trail_name: str,
        newly_available: Optional[list] = None,
        newly_unavailable: Optional[list] = None,
        checked_at: Optional[str] = None,
    ) -> dict[str, bool]:
        """Send formatted availability update message to all recipients.

        Args:
            trail_name: Name of the trail
            newly_available: List of newly available dates
            newly_unavailable: List of newly unavailable dates
            checked_at: Timestamp of the check

        Returns:
            Dict mapping phone numbers to their send status
        """
        if newly_available is None:
            newly_available = []
        if newly_unavailable is None:
            newly_unavailable = []

        message = self._format_message(
            trail_name=trail_name,
            newly_available=newly_available,
            newly_unavailable=newly_unavailable,
            checked_at=checked_at or "",
        )

        return self.send_whatsapp(message)

    def _format_message(
        self,
        trail_name: str,
        newly_available: list,
        newly_unavailable: list,
        checked_at: str,
    ) -> str:
        """Format the availability update message.

        Args:
            trail_name: Name of the trail
            newly_available: List of newly available dates
            newly_unavailable: List of newly unavailable dates
            checked_at: Timestamp of the check

        Returns:
            Formatted message string
        """
        lines = [
            f"📍 {trail_name.title()} Trail Availability Update",
            "",
        ]

        if newly_available:
            lines.append("🟢 Newly Available:")
            for date in sorted(newly_available):
                lines.append(f"  • {date}")
        else:
            lines.append("🟢 Newly Available: None")

        lines.append("")

        if newly_unavailable:
            lines.append("🔴 No Longer Available:")
            for date in sorted(newly_unavailable):
                lines.append(f"  • {date}")
        else:
            lines.append("🔴 No Longer Available: None")

        lines.append("")
        lines.append(f"⏱ Checked at: {checked_at}")

        subscriber_count = get_subscriber_count()
        if subscriber_count > 0:
            lines.append("")
            lines.append(f"📊 {subscriber_count} subscriber(s)")

        return "\n".join(lines)


def handle_subscribe_command(phone_number: str, password: Optional[str] = None) -> str:
    """Handle a subscription request.

    Args:
        phone_number: Subscriber's phone number
        password: Optional subscription password

    Returns:
        Response message
    """
    from bookings_scraper.database import add_subscriber
    from bookings_scraper.notifications import get_notification_config

    config = get_notification_config()

    # Validate password if required
    if config.allow_self_subscribe:
        if config.subscribe_password and not config.validate_password(password or ""):
            return "❌ Invalid subscription password. Please try again."

    try:
        subscriber = add_subscriber(phone_number=phone_number)
        if subscriber:
            logger.info(f"New subscriber: {phone_number}")
            return (
                "✅ Successfully subscribed to booking notifications!\n\n"
                "You will receive alerts when new availability is found.\n"
                "To unsubscribe, send /unsubscribe"
            )
        else:
            return "❌ Subscription failed. Please try again."

    except Exception as e:
        logger.error(f"Subscription error: {e}")
        return "❌ An error occurred. Please try again later."


def handle_unsubscribe_command(phone_number: str) -> str:
    """Handle an unsubscription request.

    Args:
        phone_number: Subscriber's phone number

    Returns:
        Response message
    """
    from bookings_scraper.database import remove_subscriber

    try:
        removed = remove_subscriber(phone_number)
        if removed:
            logger.info(f"Unsubscribed: {phone_number}")
            return (
                "✅ Successfully unsubscribed from booking notifications.\n\n"
                "You will no longer receive alerts."
            )
        else:
            return "❌ You were not subscribed. Nothing to unsubscribe."

    except Exception as e:
        logger.error(f"Unsubscription error: {e}")
        return "❌ An error occurred. Please try again later."
