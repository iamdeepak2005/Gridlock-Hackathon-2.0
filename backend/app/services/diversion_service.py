"""
Traffic Diversion Service.
Wraps the simulation engine for API consumption.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.simulation.traffic_diversion import diversion_engine
from app.repositories.prediction_log_repository import PredictionLogRepository


class DiversionService:
    """Service for traffic diversion simulation."""

    def simulate(self, input_data: dict, db: Optional[Session] = None) -> dict:
        """Run diversion simulation and return results."""
        result = diversion_engine.simulate(
            event_lat=input_data["event_latitude"],
            event_lng=input_data["event_longitude"],
            road_closure=input_data.get("road_closure", True),
            impact_radius_m=input_data.get("impact_radius_meters", 500),
        )

        if db:
            try:
                repo = PredictionLogRepository(db)
                log_result = {
                    "num_blocked_roads": len(result.get("blocked_roads", [])),
                    "num_alt_routes": len(result.get("alternative_routes", [])),
                    "congestion_score": result.get("congestion_risk_score"),
                }
                repo.create("diversion", input_data, log_result)
            except Exception:
                pass

        return result

    @property
    def is_available(self) -> bool:
        return True


diversion_service = DiversionService()
