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
