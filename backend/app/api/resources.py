"""
Resource Recommendation API endpoint.
POST /recommend-resources
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import ResourceRecommendationRequest, ResourceRecommendationResponse
from app.services.resource_service import resource_service
from app.database.connection import get_db

router = APIRouter(tags=["Resource Recommendation"])


@router.post(
    "/recommend-resources",
    response_model=ResourceRecommendationResponse,
    summary="Recommend Resources for Event",
    description="Recommends officers, barricades, and tow vehicles needed "
                "based on historical incident patterns.",
)
def recommend_resources(
    request: ResourceRecommendationRequest,
    db: Session = Depends(get_db),
):
    """Recommend resource allocation for a traffic event."""
    try:
        result = resource_service.predict(request.model_dump(), db=db)
        return ResourceRecommendationResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")
