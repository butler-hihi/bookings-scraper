"""WhatsApp notification handler."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WhatsAppNotifier:
    """Handle WhatsApp notifications via OpenClaw.
    
    Uses the OpenClaw WhatsApp gateway integration.
    """
    
    def __init__(self, channel: str = "main"):
        """Initialize the notifier.
        
        Args:
            channel: WhatsApp channel identifier
        """
        self.channel = channel
        logger.info(f"WhatsAppNotifier initialized with channel: {channel}")
    
    def send_whatsapp(self, message: str) -> bool:
        """Send a WhatsApp notification.
        
        Args:
            message: The message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            # Use OpenClaw's WhatsApp integration
            # The actual sending is handled by OpenClaw's WhatsApp gateway
            from openclaw import Gateway
            
            gateway = Gateway.get()
            
            # Prepare the message with metadata
            message_payload = {
                "text": message,
                "channel": self.channel
            }
            
            # Send via the WhatsApp channel
            result = gateway.post(f"/channels/{self.channel}/messages", 
                                 data=message_payload)
            
            if result.get("success"):
                logger.info(f"WhatsApp message sent successfully")
                return True
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"WhatsApp send failed: {error}")
                return False
                
        except ImportError:
            # Fallback: direct WhatsApp send if available
            return self._send_direct(message)
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def _send_direct(self, message: str) -> bool:
        """Direct WhatsApp send (fallback implementation).
        
        This is a placeholder - actual implementation depends on OpenClaw setup.
        
        Args:
            message: The message to send
            
        Returns:
            True if sent successfully
        """
        try:
            from openclaw import Gateway
            
            # This would use the actual WhatsApp API integration
            # For now, we'll use a simple print for demonstration
            print(message)  # In production, use actual WhatsApp API
            return True
            
        except Exception as e:
            logger.error(f"Direct WhatsApp send failed: {e}")
            return False
    
    def send_availability_update(
        self,
        trail_name: str,
        newly_available: list,
        newly_unavailable: list,
        checked_at: str
    ) -> bool:
        """Send formatted availability update message.
        
        Args:
            trail_name: Name of the trail
            newly_available: List of newly available dates
            newly_unavailable: List of newly unavailable dates
            checked_at: Timestamp of the check
            
        Returns:
            True if message was sent successfully
        """
        message = self._format_message(
            trail_name=trail_name,
            newly_available=newly_available,
            newly_unavailable=newly_unavailable,
            checked_at=checked_at
        )
        
        return self.send_whatsapp(message)
    
    def _format_message(
        self,
        trail_name: str,
        newly_available: list,
        newly_unavailable: list,
        checked_at: str
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
            for date in newly_available:
                lines.append(f"- {date}")
        else:
            lines.append("🟢 Newly Available: None")
        
        lines.append("")
        
        if newly_unavailable:
            lines.append("🔴 No Longer Available:")
            for date in newly_unavailable:
                lines.append(f"- {date}")
        else:
            lines.append("🔴 No Longer Available: None")
        
        lines.append("")
        lines.append(f"⏱ Checked at: {checked_at}")
        
        return "\n".join(lines)
