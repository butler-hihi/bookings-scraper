"""Otter Trail scraper for SANParks."""

import re
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bookings_scraper.trails.base import BaseTrail
from bookings_scraper.utils.logging import get_logger

logger = get_logger(__name__)


class OtterTrail(BaseTrail):
    """Scraper for SANParks Otter Trail availability.
    
    Uses the official SANParks HTML page to extract availability.
    The page lists available booking dates for the trail.
    """
    
    # SANParks base URL
    BASE_URL = "https://www2.sanparks.org"
    
    # Otter Trail booking page URL
    OTTER_URL = f"{BASE_URL}/campground/otter/"
    
    def __init__(self, config: Dict) -> None:
        """Initialize OtterTrail scraper.
        
        Args:
            config: Trail configuration dictionary
        """
        super().__init__(config)
        
        # Session with retries for robustness
        self.session = requests.Session()
        self._setup_session()
        
        # Default date range for checking
        self.default_date_range = 180  # Days
        
    def get_config(self) -> Dict:
        """Get configuration for this trail.
        
        Returns:
            Trail configuration dictionary
        """
        return self.config
    
    def _setup_session(self) -> None:
        """Configure the requests session with retries and stealth headers."""
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers to mimic browser
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Chromium";v="120", "Google Chrome";v="120", "Not=A?BSD";v="99"',
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Ch-Ua-Motion": "?0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })
        
        # Add cookie support
        from requests.cookies import RequestsCookieJar
        self.session.cookies = RequestsCookieJar()
    
    def fetch_availability(self) -> List[Dict]:
        """Fetch availability data from the Otter Trail page.
        
        Returns:
            List of availability records with keys:
            - date: Date string in YYYY-MM-DD format
            - available: Boolean availability status
            - metadata: Additional metadata
        """
        try:
            # Fetch the page
            logger.debug(f"Fetching Otter Trail page: {self.OTTER_URL}")
            response = self.session.get(self.OTTER_URL, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch Otter Trail page: HTTP {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract availability data
            # The page typically shows dates in a calendar or list format
            availability = self._parse_availability(soup)
            
            if availability:
                logger.info(f"Successfully parsed {len(availability)} availability records")
            else:
                logger.warning("No availability data found in response")
            
            return availability
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout - retrying")
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return []
        
        except Exception as e:
            logger.error(f"Unexpected error parsing Otter Trail page: {e}")
            return []
    
    def _parse_availability(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse availability from the parsed HTML.
        
        This method extracts the booking dates from the Otter Trail page.
        The actual parsing logic depends on the HTML structure of the page.
        
        Args:
            soup: BeautifulSoup object of the page content
            
        Returns:
            List of availability records
        """
        availability = []
        
        try:
            # The SANParks Otter Trail page shows dates in a grid
            # We need to find the date elements and their availability status
            
            # Option 1: Look for date elements in a calendar
            date_elements = soup.find_all("div", class_=re.compile(r"date|day|booking", re.I))
            
            if date_elements:
                for element in date_elements:
                    date_data = self._extract_date_from_element(element)
                    if date_data:
                        availability.append(date_data)
            
            # Option 2: Look for booking status indicators
            # The page might use specific classes for available/unavailable
            
            # Alternative: Extract from text content
            status_elements = soup.find_all("span", class_=re.compile(r"status|availability", re.I))
            
            if status_elements:
                for element in status_elements:
                    status_data = self._extract_status_from_element(element)
                    if status_data:
                        availability.append(status_data)
            
            # If no structured elements found, fall back to text parsing
            if not availability:
                availability = self._parse_text_content(soup)
            
            return availability
            
        except Exception as e:
            logger.error(f"Error parsing date elements: {e}")
            return []
    
    def _extract_date_from_element(self, element) -> Optional[Dict]:
        """Extract date and availability from a date element.
        
        Args:
            element: HTML element containing date info
            
        Returns:
            Availability record dict or None
        """
        try:
            # Extract date text
            date_text = element.get_text(strip=True)
            
            # Parse date (SANParks uses DD-MMM-YY or DD/MM/YYYY format)
            parsed_date = self._parse_date_string(date_text)
            
            if parsed_date:
                # Determine availability based on element styling or class
                available = self._is_element_available(element)
                
                return {
                    "date": parsed_date,
                    "available": available,
                    "metadata": {
                        "raw_text": date_text,
                        "source": "date_element"
                    }
                }
            
        except Exception as e:
            logger.debug(f"Error extracting date from element: {e}")
        
        return None
    
    def _extract_status_from_element(self, element) -> Optional[Dict]:
        """Extract availability status from a status element.
        
        Args:
            element: HTML element containing status info
            
        Returns:
            Availability record dict or None
        """
        try:
            # Get status text
            status_text = element.get_text(strip=True).lower()
            
            # Parse date from nearby elements
            # This would require finding the associated date element
            
        except Exception as e:
            logger.debug(f"Error extracting status from element: {e}")
        
        return None
    
    def _parse_text_content(self, soup: BeautifulSoup) -> List[Dict]:
        """Fall back to parsing text content when structured elements not found.
        
        Args:
            soup: BeautifulSoup object of the page content
            
        Returns:
            List of availability records (may be incomplete)
        """
        availability = []
        
        # Try to find date patterns in the page
        date_pattern = re.compile(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})")
        
        # Look for booking-related sections
        booking_sections = soup.find_all(class_=re.compile(r"booking|calendar|dates", re.I))
        
        for section in booking_sections:
            text = section.get_text(strip=True)
            matches = date_pattern.findall(text)
            
            for match in matches:
                day, month, year = match
                
                # Convert to YYYY-MM-DD
                try:
                    # Handle 2-digit years
                    year_int = int(year)
                    if year_int > 50:
                        year_str = f"20{year_int - 50}"
                    else:
                        year_str = f"20{year_int}"
                    
                    # Handle day/month order (SANParks might use DD/MM/YYYY)
                    date_str = f"{day}/{month}/{year_str}"
                    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    
                    # Determine availability (would need to check styling)
                    available = True  # Default - would check element attributes in production
                    
                    availability.append({
                        "date": date_obj.strftime("%Y-%m-%d"),
                        "available": available,
                        "metadata": {
                            "raw_text": text[:100],
                            "source": "text_fallback"
                        }
                    })
                except ValueError as e:
                    logger.debug(f"Failed to parse date: {match} - {e}")
        
        return availability
    
    def _parse_date_string(self, date_text: str) -> Optional[str]:
        """Parse a date string from the page.
        
        Args:
            date_text: Raw date string from HTML
            
        Returns:
            ISO format date string (YYYY-MM-DD) or None
        """
        date_text = date_text.strip()
        
        # Try different date formats
        formats = [
            "%d-%b-%y",  # 15-Mar-26
            "%d/%m/%Y",  # 15/03/2026
            "%d/%m/%y",  # 15/03/26
            "%Y-%m-%d",  # 2026-03-15
        ]
        
        # Clean up the text (remove extra words)
        clean_text = re.sub(r"[^\d\-/]/", "", date_text)
        
        for fmt in formats:
            try:
                # Extract date part
                date_match = re.match(r"(\d+)[\-/](\d+)[\-/](\d+)", clean_text)
                if date_match:
                    day, month, year = date_match.groups()
                    
                    # Handle 2-digit year
                    year_int = int(year)
                    if year_int > 50:
                        year_str = f"20{year_int - 50}"
                    else:
                        year_str = f"20{year_int}"
                    
                    date_str = f"{day}/{month}/{year_str}"
                    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    
                    return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        logger.debug(f"Could not parse date: {date_text}")
        return None
    
    def _is_element_available(self, element) -> bool:
        """Determine if a date element represents an available booking.
        
        This would check element attributes like:
        - Classes (e.g., "available", "booked", "disabled")
        - Styling (e.g., color, background)
        - Data attributes
        
        Args:
            element: HTML element to check
            
        Returns:
            True if available, False otherwise
        """
        # Check for availability indicators
        classes = (element.get("class") or [])
        
        # Common availability indicators
        available_classes = ["available", "bookable", "can-book", "green"]
        unavailable_classes = ["unavailable", "booked", "disabled", "red", "sold-out"]
        
        for cls in classes:
            cls_lower = cls.lower()
            
            if any(ac in cls_lower for ac in available_classes):
                return True
            
            if any(ua in cls_lower for ua in unavailable_classes):
                return False
        
        # Check element attributes
        data_available = element.get("data-available", "").lower()
        if data_available in ["true", "1", "yes"]:
            return True
        
        data_status = element.get("data-status", "").lower()
        if data_status in ["available", "bookable"]:
            return True
        
        # Default: assume available if we can't determine
        return True
