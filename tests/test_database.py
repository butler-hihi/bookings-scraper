"""Tests for the bookings scraper."""

import sys
import unittest
from pathlib import Path

# Add project source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bookings_scraper.database import (
    add_subscriber,
    get_active_subscribers,
    get_availability,
    get_db_path,
    get_subscriber_count,
    init_database,
    remove_subscriber,
    save_availability,
)


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
            trail_name="otter", date="2026-04-01", available=True, db_path=self.test_db
        )
        self.assertIsNotNone(record_id)
        self.assertIsInstance(record_id, int)

    def test_get_availability(self):
        """Test retrieving availability records."""
        save_availability(
            trail_name="otter", date="2026-04-01", available=True, db_path=self.test_db
        )

        record = get_availability("otter", "2026-04-01", db_path=self.test_db)
        self.assertIsNotNone(record)
        self.assertTrue(record.available)

    def test_update_availability(self):
        """Test updating availability records."""
        save_availability(
            trail_name="otter", date="2026-04-01", available=True, db_path=self.test_db
        )

        # Update
        save_availability(
            trail_name="otter", date="2026-04-01", available=False, db_path=self.test_db
        )

        # Verify update
        record = get_availability("otter", "2026-04-01", db_path=self.test_db)
        self.assertFalse(record.available)


class TestSubscribers(unittest.TestCase):
    """Tests for the subscriber management."""

    def setUp(self):
        """Set up test database."""
        self.test_db = Path("data/test_subscribers.db")
        self.test_db.parent.mkdir(parents=True, exist_ok=True)
        init_database(self.test_db)

    def tearDown(self):
        """Clean up test database."""
        if self.test_db.exists():
            self.test_db.unlink()

    def test_add_subscriber(self):
        """Test adding a new subscriber."""
        subscriber = add_subscriber(
            phone_number="+27689145805", name="Test User", db_path=self.test_db
        )
        self.assertIsNotNone(subscriber)
        # Access attributes before session closes
        phone = subscriber.phone_number
        self.assertEqual(phone, "+27689145805")
        self.assertTrue(subscriber.active)

    def test_add_duplicate_subscriber(self):
        """Test adding a duplicate subscriber reactivates them."""
        add_subscriber(phone_number="+27689145805", db_path=self.test_db)
        add_subscriber(phone_number="+27689145805", db_path=self.test_db)

        count = get_subscriber_count(db_path=self.test_db)
        self.assertEqual(count, 1)

    def test_remove_subscriber(self):
        """Test removing a subscriber."""
        add_subscriber(phone_number="+27689145805", db_path=self.test_db)
        removed = remove_subscriber("+27689145805", db_path=self.test_db)
        self.assertTrue(removed)

        count = get_subscriber_count(db_path=self.test_db)
        self.assertEqual(count, 0)

    def test_get_active_subscribers(self):
        """Test getting active subscribers."""
        add_subscriber(phone_number="+27689145805", db_path=self.test_db)
        add_subscriber(phone_number="+27689145806", db_path=self.test_db)

        subscribers = get_active_subscribers(db_path=self.test_db)
        self.assertEqual(len(subscribers), 2)

    def test_subscriber_count(self):
        """Test subscriber count."""
        add_subscriber(phone_number="+27689145805", db_path=self.test_db)
        add_subscriber(phone_number="+27689145806", db_path=self.test_db)
        add_subscriber(phone_number="+27689145807", db_path=self.test_db)

        # Remove one
        remove_subscriber("+27689145806", db_path=self.test_db)

        count = get_subscriber_count(db_path=self.test_db)
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
