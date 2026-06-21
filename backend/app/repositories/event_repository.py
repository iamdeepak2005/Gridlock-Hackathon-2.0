"""
Repository for traffic event CRUD operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import TrafficEvent


class EventRepository:
    """Data access layer for traffic events."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: str) -> Optional[TrafficEvent]:
        return self.db.query(TrafficEvent).filter(TrafficEvent.id == event_id).first()

    def get_all(self, limit: int = 1000, offset: int = 0) -> list[TrafficEvent]:
        return self.db.query(TrafficEvent).offset(offset).limit(limit).all()

    def get_count(self) -> int:
        return self.db.query(func.count(TrafficEvent.id)).scalar() or 0

    def get_by_zone(self, zone: str) -> list[TrafficEvent]:
        return self.db.query(TrafficEvent).filter(TrafficEvent.zone == zone).all()

    def get_by_cause(self, cause: str) -> list[TrafficEvent]:
        return self.db.query(TrafficEvent).filter(TrafficEvent.event_cause == cause).all()
