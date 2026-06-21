"""
Impact Scoring API endpoint.
POST /predict-impact
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import ImpactPredictionRequest, ImpactPredictionResponse
from app.services.impact_service import impact_service
from app.database.connection import get_db

router = APIRouter(tags=["Impact Scoring"])


@router.post(
    "/predict-impact",
    response_model=ImpactPredictionResponse,
    summary="Predict Event Impact Score",
    description="Analyzes a traffic event and returns an impact score (0-100) "
                "with contributing factors and confidence level.",
)
def predict_impact(
    request: ImpactPredictionRequest,
    db: Session = Depends(get_db),
):
    """Predict impact score for a traffic event."""
    try:
        result = impact_service.predict(request.model_dump(), db=db)
        return ImpactPredictionResponse(
            impact_score=result["impact_score"],
            impact_level=result["impact_level"],
            confidence=result["confidence"],
            top_contributing_factors=result["top_contributing_factors"],
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
