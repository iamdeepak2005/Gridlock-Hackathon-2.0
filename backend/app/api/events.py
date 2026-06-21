"""
Events retrieval API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.connection import get_db
from app.repositories.event_repository import EventRepository
from pydantic import BaseModel, Field

router = APIRouter(tags=["Events"])


class EventResponseSchema(BaseModel):
    id: str
    event_type: str
    latitude: float
    longitude: float
    event_cause: str
    requires_road_closure: bool
    status: str
    priority: Optional[str] = "Low"
    description: Optional[str] = None
    zone: Optional[str] = None
    junction: Optional[str] = None
    corridor: Optional[str] = None
    veh_type: Optional[str] = None
    resolution_minutes: Optional[float] = None
    impact_score: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("/events", response_model=List[EventResponseSchema])
def get_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve list of traffic events from database."""
    repo = EventRepository(db)
    return repo.get_all(limit=limit, offset=offset)
