"""Tests for the bookings scraper."""

import unittest
import sys
from pathlib import Path

# Add project source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bookings_scraper.database import init_database, get_db_path


class TestDatabase(unittest.TestCase):
    """Tests for the database module."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = Path("data/test.db")
        self.test_db.parent.mkdir(parents=True, exist_ok=True)
        init_database(self.test_db)
    
    def tearDown(self):
        """Clean up test database."""
        if self.test_db.exists():
            self.test_db.unlink()
    
    def test_init_database(self):
        """Test database initialization."""
        conn = init_database(self.test_db)
        self.assertIsNotNone(conn)
        conn.close()
    
    def test_save_availability(self):
        """Test saving availability records."""
        record_id = save_availability(
            trail_name="otter",
            date="2026-04-01",
            available=True
        )
        self.assertIsNotNone(record_id)
        self.assertIsInstance(record_id, int)
    
    def test_get_availability(self):
        """Test retrieving availability records."""
        save_availability(
            trail_name="otter",
            date="2026-04-01",
            available=True
        )
        
        record = get_availability("otter", "2026-04-01")
        self.assertIsNotNone(record)
        self.assertTrue(record.available)
    
    def test_update_availability(self):
        """Test updating availability records."""
        save_availability(
            trail_name="otter",
            date="2026-04-01",
            available=True
        )
        
        # Update
        save_availability(
            trail_name="otter",
            date="2026-04-01",
            available=False
        )
        
        # Verify update
        record = get_availability("otter", "2026-04-01")
        self.assertFalse(record.available)


if __name__ == "__main__":
    unittest.main()
