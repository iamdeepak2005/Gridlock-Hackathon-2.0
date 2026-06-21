"""
Pydantic v2 schemas for all API request/response models.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


# ─── Impact Scoring ───────────────────────────────────────────────

class ImpactPredictionRequest(BaseModel):
    """Request body for POST /predict-impact."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "event_type": "unplanned",
            "event_cause": "accident",
            "zone": "Central Zone 1",
            "junction": "SilkBoardJunc",
            "corridor": "Hosur Road",
            "priority": "High",
            "veh_type": "heavy_vehicle",
            "requires_road_closure": True,
            "start_datetime": "2024-03-07T17:01:48",
            "description": "Heavy vehicle accident blocking two lanes"
        }
    })

    event_type: str = Field(..., description="planned or unplanned")
    event_cause: str = Field(..., description="e.g. accident, vehicle_breakdown, tree_fall")
    zone: Optional[str] = Field(None, description="Traffic zone")
    junction: Optional[str] = Field(None, description="Junction name")
    corridor: Optional[str] = Field("Non-corridor", description="Corridor name")
    priority: Optional[str] = Field("Low", description="High or Low")
    veh_type: Optional[str] = Field(None, description="Vehicle type if applicable")
    requires_road_closure: bool = Field(False, description="Whether road closure is required")
    start_datetime: Optional[str] = Field(None, description="Event start time ISO format")
    description: Optional[str] = Field(None, description="Free-text event description")


class ContributingFactor(BaseModel):
    feature: str
    importance: float


class ImpactPredictionResponse(BaseModel):
    impact_score: float = Field(..., ge=0, le=100, description="Impact severity 0-100")
    impact_level: str = Field(..., description="Low / Medium / High / Critical")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence")
    top_contributing_factors: List[ContributingFactor]


# ─── Resource Recommendation ─────────────────────────────────────

class ResourceRecommendationRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "event_type": "unplanned",
            "event_cause": "accident",
            "priority": "High",
            "zone": "South Zone 1",
            "junction": "SilkBoardJunc",
            "requires_road_closure": True,
            "veh_type": "heavy_vehicle"
        }
    })

    event_type: str
    event_cause: str
    priority: Optional[str] = "Low"
    zone: Optional[str] = None
    junction: Optional[str] = None
    requires_road_closure: bool = False
    veh_type: Optional[str] = None
    corridor: Optional[str] = "Non-corridor"


class ResourceRecommendationResponse(BaseModel):
    officers_required: int = Field(..., ge=0)
    barricades_required: int = Field(..., ge=0)
    tow_vehicles_required: int = Field(..., ge=0)
    estimated_resolution_time: float = Field(..., description="Minutes")
    confidence: float = Field(..., ge=0, le=1)


# ─── Similar Events ──────────────────────────────────────────────

class SimilarEventRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "event_type": "unplanned",
            "event_cause": "vehicle_breakdown",
            "zone": "North Zone 1",
            "junction": "HebbalFlyoverJunc",
            "description": "BMTC bus breakdown on flyover",
            "requires_road_closure": False
        }
    })

    event_type: str
    event_cause: str
    zone: Optional[str] = None
    junction: Optional[str] = None
    description: Optional[str] = None
    requires_road_closure: bool = False
    corridor: Optional[str] = "Non-corridor"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SimilarEventItem(BaseModel):
    id: str
    event_cause: str
    zone: Optional[str]
    junction: Optional[str]
    resolution_minutes: Optional[float]
    similarity_score: float
    description: Optional[str] = None


class SimilarEventResponse(BaseModel):
    similar_events: List[SimilarEventItem]
    average_resolution_time: Optional[float]
    historical_success_patterns: List[str]
    recommended_action: str


# ─── Resolution Time Prediction ──────────────────────────────────

class ResolutionPredictionRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "event_type": "unplanned",
            "event_cause": "vehicle_breakdown",
            "zone": "Central Zone 2",
            "junction": "UrvashiJunction",
            "corridor": "Non-corridor",
            "priority": "Low",
            "veh_type": "bmtc_bus",
            "requires_road_closure": False,
            "start_datetime": "2024-01-30T04:07:24"
        }
    })

    event_type: str
    event_cause: str
    zone: Optional[str] = None
    junction: Optional[str] = None
    corridor: Optional[str] = "Non-corridor"
    priority: Optional[str] = "Low"
    veh_type: Optional[str] = None
    requires_road_closure: bool = False
    start_datetime: Optional[str] = None


class ResolutionPredictionResponse(BaseModel):
    estimated_resolution_minutes: float
    confidence: float = Field(..., ge=0, le=1)
    risk_level: str = Field(..., description="Low / Medium / High")


# ─── Feedback / Continual Learning ───────────────────────────────

class FeedbackRequest(BaseModel):
    prediction_id: str = Field(..., description="UUID of the prediction log entry")
    actual_outcome: Optional[dict] = None
    feedback_text: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str
    prediction_id: str
    updated_metrics: Optional[dict] = None


class ModelPerformanceItem(BaseModel):
    model_name: str
    feature_name: str
    model_type: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    accuracy: Optional[float] = None
    drift_score: Optional[float] = None
    last_trained: Optional[str] = None
    prediction_count: int = 0
    is_active: bool = False


class ModelPerformanceResponse(BaseModel):
    models: List[ModelPerformanceItem]
    total_predictions: int
    feedback_count: int


# ─── Traffic Diversion Simulation ────────────────────────────────

class DiversionRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "event_latitude": 12.9716,
            "event_longitude": 77.5946,
            "road_closure": True,
            "impact_radius_meters": 500
        }
    })

    event_latitude: float = Field(..., ge=-90, le=90)
    event_longitude: float = Field(..., ge=-180, le=180)
    road_closure: bool = True
    impact_radius_meters: float = Field(500, ge=100, le=5000)


class BlockedRoad(BaseModel):
    name: Optional[str] = "Unknown Road"
    from_node: int
    to_node: int
    length_m: Optional[float] = None
    coords: Optional[List[List[float]]] = None


class AlternativeRoute(BaseModel):
    route_coords: List[List[float]]
    distance_m: float
    estimated_time_min: float


class NormalRoad(BaseModel):
    name: str
    coords: List[List[float]]
    speed_kph: int
    flow_level: str


class DiversionResponse(BaseModel):
    blocked_roads: List[BlockedRoad]
    alternative_routes: List[AlternativeRoute]
    normal_roads: List[NormalRoad] = []
    estimated_extra_travel_time: float
    congestion_risk_score: float = Field(..., ge=0, le=100)
    affected_junctions: List[str]


# ─── Health ──────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: Dict[str, bool]
    database_connected: bool
    timestamp: str


# ─── Copilot ─────────────────────────────────────────────────────

class CopilotRequest(BaseModel):
    query: str


class CopilotResponse(BaseModel):
    response: str

