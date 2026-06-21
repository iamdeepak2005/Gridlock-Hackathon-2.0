"""
Similar Event Retrieval API endpoint.
POST /similar-events
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import SimilarEventRequest, SimilarEventResponse, SimilarEventItem
from app.services.similarity_service import similarity_service
from app.database.connection import get_db

router = APIRouter(tags=["Similar Events"])


@router.post(
    "/similar-events",
    response_model=SimilarEventResponse,
    summary="Find Similar Historical Events",
    description="Retrieves the most similar historical traffic events "
                "and provides resolution patterns and recommendations.",
)
def find_similar_events(
    request: SimilarEventRequest,
    db: Session = Depends(get_db),
):
    """Find similar historical events."""
    try:
        result = similarity_service.find_similar(request.model_dump(), db=db)

        # Convert similar events to schema
        similar_items = [
            SimilarEventItem(
                id=e["id"],
                event_cause=e["event_cause"],
                zone=e.get("zone"),
                junction=e.get("junction"),
                resolution_minutes=e.get("resolution_minutes"),
                similarity_score=e["similarity_score"],
                description=e.get("description"),
            )
            for e in result.get("similar_events", [])
        ]

        return SimilarEventResponse(
            similar_events=similar_items,
            average_resolution_time=result.get("average_resolution_time"),
            historical_success_patterns=result.get("historical_success_patterns", []),
            recommended_action=result.get("recommended_action", ""),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")
