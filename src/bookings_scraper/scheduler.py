"""Scheduler for the booking availability checker."""

import logging
import time
from typing import List, Optional
from datetime import datetime

from bookings_scraper.trails.base import BaseTrail
from bookings_scraper.utils.logging import get_logger

logger = get_logger(__name__)


class Scheduler:
    """Schedule and orchestrate trail availability checks.
    
    Runs checks at configured intervals and processes results.
    """
    
    def __init__(self, trails: List[BaseTrail]) -> None:
        """Initialize the scheduler.
        
        Args:
            trails: List of Trail objects to check
        """
        self.trails = trails
        self.running = False
        self.last_check_time: Optional[datetime] = None
        
        logger.info(f"Scheduler initialized with {len(trails)} trails")
    
    def run_once(self) -> dict:
        """Run a single availability check cycle.
        
        Returns:
            Dict with check results and changes
        """
        self.last_check_time = datetime.now()
        
        results = {}
        all_changes = {
            "newly_available": [],
            "newly_unavailable": [],
            "trail_names": []
        }
        
        # Check each trail
        for trail in self.trails:
            logger.info(f"Checking availability for {trail.display_name}")
            
            trail_result = trail.check_availability()
            
            if trail_result:
                trail_name = trail.get_name()
                results[trail_name] = trail_result
                
                # Extract changes if successful
                status = trail_result.get("status")
                
                if status == "success":
                    trail_changes = self._extract_changes(
                        trail_name=trail_name,
                        results=trail_result
                    )
                    
                    # Merge into overall changes
                    all_changes["trail_names"].append(trail_name)
                    all_changes["newly_available"].extend(trail_changes.get("newly_available", []))
                    all_changes["newly_unavailable"].extend(trail_changes.get("newly_unavailable", []))
                elif status in ["error", "no_data"]:
                    logger.warning(f"Skipping {trail_name}: {status}")
            
            results[trail_name] = trail_result
        
        return {
            "timestamp": self.last_check_time.isoformat() if self.last_check_time else None,
            "results": results,
            "changes": all_changes,
            "trails_checked": len(self.trails),
            "success_count": len([r for r in results.values() if r.get("status") == "success"])
        }
    
    def _extract_changes(self, trail_name: str, results: dict) -> dict:
        """Extract availability changes from results.
        
        This would compare current results with stored database state.
        For now, we return a placeholder that the actual database layer will handle.
        
        Args:
            trail_name: Name of the trail
            results: Results from the check
            
        Returns:
            Dict with 'newly_available' and 'newly_unavailable'
        """
        # In production, this would compare with database
        # For now, return empty changes
        return {
            "newly_available": [],
            "newly_unavailable": []
        }
    
    def run_loop(self, interval_seconds: int = 60) -> None:
        """Run the scheduler in a loop.
        
        Args:
            interval_seconds: Check interval in seconds
        """
        self.running = True
        logger.info(f"Scheduler starting with interval: {interval_seconds}s")
        
        while self.running:
            try:
                result = self.run_once()
                
                logger.info(f"Check completed: {result['success_count']}/{len(self.trails)} trails successful")
                
                # Sleep until next interval
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                self.running = False
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Continue loop on error
                time.sleep(interval_seconds)
    
    def stop(self) -> None:
        """Stop the scheduler loop."""
        self.running = False
        logger.info("Scheduler stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status.
        
        Returns:
            Dict with scheduler status information
        """
        return {
            "running": self.running,
            "trails_count": len(self.trails),
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }
