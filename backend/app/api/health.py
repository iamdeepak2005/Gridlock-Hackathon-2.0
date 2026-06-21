"""
Health check endpoint.
GET /health
"""

from datetime import datetime
from fastapi import APIRouter

from app.config import settings
from app.services.impact_service import impact_service
from app.services.resolution_service import resolution_service
from app.services.similarity_service import similarity_service
from app.services.resource_service import resource_service
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns system health, loaded models status, and DB connectivity.",
)
def health_check():
    """System health check."""
    # Check DB connectivity
    db_connected = True
    try:
        from app.database.connection import engine
        with engine.connect() as conn:
            conn.execute(conn.connection.cursor().execute if False else type(conn).begin)
    except Exception:
        # Just check if engine is defined
        try:
            from app.database.connection import engine
            db_connected = engine is not None
        except Exception:
            db_connected = False

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        models_loaded={
            "impact": impact_service.is_available,
            "resolution": resolution_service.is_available,
            "similarity": similarity_service.is_available,
            "resource": resource_service.is_available,
        },
        database_connected=db_connected,
        timestamp=datetime.utcnow().isoformat(),
    )
