"""
Root API router that aggregates all feature routers.
"""

from fastapi import APIRouter

from app.api.events import router as events_router
from app.api.impact import router as impact_router
from app.api.resources import router as resources_router
from app.api.similar import router as similar_router
from app.api.resolution import router as resolution_router
from app.api.feedback import router as feedback_router
from app.api.diversion import router as diversion_router
from app.api.health import router as health_router
from app.api.copilot import router as copilot_router

api_router = APIRouter()

# Include all feature routers
api_router.include_router(events_router)
api_router.include_router(impact_router)
api_router.include_router(resources_router)
api_router.include_router(similar_router)
api_router.include_router(resolution_router)
api_router.include_router(feedback_router)
api_router.include_router(diversion_router)
api_router.include_router(health_router)
api_router.include_router(copilot_router)
