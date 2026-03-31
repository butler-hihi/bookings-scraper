"""Database models and operations for booking availability tracking."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

# Configure SQLAlchemy
Base = declarative_base()


class AvailabilityRecord(Base):
    """Model for tracking trail availability."""

    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trail_name = Column(String(100), nullable=False)
    date = Column(String(10), nullable=False, unique=True)
    available = Column(Boolean, nullable=False, default=False)
    last_checked = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"AvailabilityRecord(trail={self.trail_name}, date={self.date}, available={self.available})"


class Subscriber(Base):
    """Model for tracking notification subscribers."""

    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=True)
    subscribed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    active = Column(Boolean, nullable=False, default=True)
    notify_on_available = Column(Boolean, nullable=False, default=True)
    notify_on_unavailable = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"Subscriber(phone={self.phone_number}, active={self.active})"


def get_db_path() -> Path:
    """Get the database file path.

    Returns:
        Path to the SQLite database file
    """
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "bookings.db"


def init_database(db_path: Path = None) -> sqlite3.Connection:
    """Initialize the SQLite database with required tables.

    Args:
        db_path: Path to database file (uses default if None)

    Returns:
        Database connection object
    """
    if db_path is None:
        db_path = get_db_path()

    # Create data directory
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Use SQLite directly for simplicity
    engine = create_engine(f"sqlite:///{db_path}")

    # Create all tables
    Base.metadata.create_all(engine)

    return engine.connect()


def save_availability(
    trail_name: str,
    date: str,
    available: bool,
    metadata: Optional[dict[str, Any]] = None,
    db_path: Path = None,
) -> int:
    """Save or update availability record.

    Args:
        trail_name: Name of the trail (e.g., 'otter')
        date: Date string in YYYY-MM-DD format
        available: Whether bookings are available
        metadata: Additional metadata
        db_path: Path to database

    Returns:
        ID of the saved record
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if record exists
        existing = (
            session.query(AvailabilityRecord)
            .filter(AvailabilityRecord.trail_name == trail_name, AvailabilityRecord.date == date)
            .first()
        )

        if existing:
            # Update existing record
            existing.available = available
            existing.extra_data = metadata
            existing.last_checked = datetime.utcnow()
            session.commit()
            return existing.id
        else:
            # Create new record
            new_record = AvailabilityRecord(
                trail_name=trail_name,
                date=date,
                available=available,
                extra_data=metadata,
                last_checked=datetime.utcnow(),
            )
            session.add(new_record)
            session.commit()
            return new_record.id

    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_availability(
    trail_name: str, date: str, db_path: Path = None
) -> Optional[AvailabilityRecord]:
    """Get availability record for a specific trail and date.

    Args:
        trail_name: Name of the trail
        date: Date string in YYYY-MM-DD format
        db_path: Path to database

    Returns:
        AvailabilityRecord if exists, None otherwise
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        record = (
            session.query(AvailabilityRecord)
            .filter(AvailabilityRecord.trail_name == trail_name, AvailabilityRecord.date == date)
            .first()
        )

        return record
    finally:
        session.close()


def get_all_availability(
    trail_name: Optional[str] = None, db_path: Path = None
) -> list[AvailabilityRecord]:
    """Get all availability records, optionally filtered by trail.

    Args:
        trail_name: Filter by trail name if provided
        db_path: Path to database

    Returns:
        List of AvailabilityRecord objects
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        query = session.query(AvailabilityRecord)
        if trail_name:
            query = query.filter(AvailabilityRecord.trail_name == trail_name)

        return query.order_by(AvailabilityRecord.trail_name, AvailabilityRecord.date).all()
    finally:
        session.close()


def get_changes(
    trail_name: str, current_availability: dict[str, bool], db_path: Path = None
) -> dict[str, Any]:
    """Detect changes between current data and stored records.

    Args:
        trail_name: Name of the trail
        current_availability: Dict of date -> availability mapping
        db_path: Path to database

    Returns:
        Dict with 'newly_available', 'newly_unavailable', 'status'
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get stored records for this trail
        records = (
            session.query(AvailabilityRecord)
            .filter(AvailabilityRecord.trail_name == trail_name)
            .all()
        )

        # Convert to dict for comparison
        stored_availability = {record.date: record.available for record in records}

        # Detect changes
        newly_available = []
        newly_unavailable = []

        # Check for newly available
        for date, available in current_availability.items():
            if date not in stored_availability and available:
                newly_available.append(date)

        # Check for newly unavailable
        for date, available in current_availability.items():
            if date not in stored_availability and not available:
                newly_unavailable.append(date)

        # Check for status changes
        for date, available in stored_availability.items():
            if date in current_availability:
                if current_availability[date] != available:
                    if not available:
                        newly_unavailable.append(f"{date} (was available)")
                    else:
                        newly_available.append(f"{date} (was unavailable)")

        return {
            "trail_name": trail_name,
            "newly_available": newly_available,
            "newly_unavailable": newly_unavailable,
            "total_records": len(records),
        }

    finally:
        session.close()


def add_subscriber(
    phone_number: str,
    name: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> Subscriber:
    """Add a new subscriber.

    Args:
        phone_number: Subscriber's phone number (with country code)
        name: Optional subscriber name
        db_path: Path to database

    Returns:
        The created Subscriber object
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if already exists
        existing = session.query(Subscriber).filter(Subscriber.phone_number == phone_number).first()

        if existing:
            existing.active = True
            if name:
                existing.name = name
            session.commit()
            return existing

        # Create new subscriber
        subscriber = Subscriber(
            phone_number=phone_number,
            name=name,
            subscribed_at=datetime.utcnow(),
            active=True,
        )
        session.add(subscriber)
        session.commit()

        # Expose the subscriber object before closing session
        result = {
            "id": subscriber.id,
            "phone_number": subscriber.phone_number,
            "name": subscriber.name,
            "active": subscriber.active,
        }

        session.close()

        # Return a simple dict instead of ORM object to avoid detached instance issues
        class SubscriberResult:
            def __init__(self, data):
                self.id = data["id"]
                self.phone_number = data["phone_number"]
                self.name = data["name"]
                self.active = data["active"]

        return SubscriberResult(result)

    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()


def remove_subscriber(phone_number: str, db_path: Optional[Path] = None) -> bool:
    """Remove (deactivate) a subscriber.

    Args:
        phone_number: Subscriber's phone number
        db_path: Path to database

    Returns:
        True if subscriber was found and removed, False otherwise
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        subscriber = (
            session.query(Subscriber).filter(Subscriber.phone_number == phone_number).first()
        )

        if subscriber:
            subscriber.active = False
            session.commit()
            return True
        return False

    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_active_subscribers(db_path: Optional[Path] = None) -> list[Subscriber]:
    """Get all active subscribers.

    Args:
        db_path: Path to database

    Returns:
        List of active Subscriber objects
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        return (
            session.query(Subscriber)
            .filter(Subscriber.active.is_(True))
            .order_by(Subscriber.subscribed_at)
            .all()
        )
    finally:
        session.close()


def get_subscriber_count(db_path: Optional[Path] = None) -> int:
    """Get count of active subscribers.

    Args:
        db_path: Path to database

    Returns:
        Number of active subscribers
    """
    if db_path is None:
        db_path = get_db_path()

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        return session.query(Subscriber).filter(Subscriber.active.is_(True)).count()
    finally:
        session.close()
