"""
SQLAlchemy ORM models for the TRINETRA AI database.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, Text, Integer,
    DateTime, JSON, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.database.connection import Base


def generate_uuid():
    return str(uuid.uuid4())


class TrafficEvent(Base):
    """Stores the full traffic event dataset."""
    __tablename__ = "traffic_events"

    id = Column(String(50), primary_key=True)
    event_type = Column(String(20), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    endlatitude = Column(Float, nullable=True)
    endlongitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    end_address = Column(Text, nullable=True)
    event_cause = Column(String(50), nullable=False, index=True)
    requires_road_closure = Column(Boolean, default=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    end_datetime = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, index=True)
    authenticated = Column(String(10), nullable=True)
    modified_datetime = Column(DateTime(timezone=True), nullable=True)
    direction = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    veh_type = Column(String(30), nullable=True)
    veh_no = Column(String(30), nullable=True)
    corridor = Column(String(100), nullable=True, index=True)
    priority = Column(String(10), nullable=True, index=True)
    cargo_material = Column(String(100), nullable=True)
    reason_breakdown = Column(String(200), nullable=True)
    age_of_truck = Column(Float, nullable=True)
    created_date = Column(DateTime(timezone=True), nullable=True)
    client_id = Column(Integer, nullable=True)
    created_by_id = Column(String(50), nullable=True)
    last_modified_by_id = Column(String(50), nullable=True)
    assigned_to_police_id = Column(String(50), nullable=True)
    citizen_accident_id = Column(String(50), nullable=True)
    police_station = Column(String(100), nullable=True)
    kgid = Column(String(50), nullable=True)
    resolved_at_address = Column(Text, nullable=True)
    resolved_at_latitude = Column(Float, nullable=True)
    resolved_at_longitude = Column(Float, nullable=True)
    closed_by_id = Column(String(50), nullable=True)
    closed_datetime = Column(DateTime(timezone=True), nullable=True)
    resolved_by_id = Column(String(50), nullable=True)
    resolved_datetime = Column(DateTime(timezone=True), nullable=True)
    gba_identifier = Column(String(100), nullable=True)
    zone = Column(String(50), nullable=True, index=True)
    junction = Column(String(100), nullable=True, index=True)
    # Derived fields
    resolution_minutes = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)


class PredictionLog(Base):
    """Logs every prediction for continual learning and feedback."""
    __tablename__ = "prediction_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prediction_type = Column(String(30), nullable=False, index=True)
    input_data = Column(JSON, nullable=False)
    prediction = Column(JSON, nullable=False)
    actual_outcome = Column(JSON, nullable=True)
    error_metric = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ModelMetadata(Base):
    """Model registry: tracks trained models, their metrics, and active status."""
    __tablename__ = "model_metadata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(30), nullable=False)
    feature_name = Column(String(30), nullable=False, index=True)
    metrics = Column(JSON, nullable=True)
    file_path = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime, default=func.now())
