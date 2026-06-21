"""
Traffic Diversion Simulation API endpoint.
POST /simulate-diversion
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import (
    DiversionRequest, DiversionResponse,
    BlockedRoad, AlternativeRoute, NormalRoad,
)
from app.services.diversion_service import diversion_service
from app.database.connection import get_db

router = APIRouter(tags=["Traffic Diversion"])


@router.post(
    "/simulate-diversion",
    response_model=DiversionResponse,
    summary="Simulate Traffic Diversion",
    description="Simulates traffic diversion around a blocked area using "
                "OpenStreetMap road network data. Computes alternative routes "
                "and congestion risk scores.",
)
def simulate_diversion(
    request: DiversionRequest,
    db: Session = Depends(get_db),
):
    """Simulate traffic diversion for a road closure event."""
    try:
        result = diversion_service.simulate(request.model_dump(), db=db)

        blocked = [BlockedRoad(**r) for r in result.get("blocked_roads", [])]
        alternatives = [AlternativeRoute(**r) for r in result.get("alternative_routes", [])]
        normal = [NormalRoad(**r) for r in result.get("normal_roads", [])]

        return DiversionResponse(
            blocked_roads=blocked,
            alternative_routes=alternatives,
            normal_roads=normal,
            estimated_extra_travel_time=result.get("estimated_extra_travel_time", 0),
            congestion_risk_score=result.get("congestion_risk_score", 0),
            affected_junctions=result.get("affected_junctions", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
