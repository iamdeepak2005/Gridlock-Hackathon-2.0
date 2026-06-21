"""
Resolution Time Prediction API endpoint.
POST /predict-resolution
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import ResolutionPredictionRequest, ResolutionPredictionResponse
from app.services.resolution_service import resolution_service
from app.database.connection import get_db

router = APIRouter(tags=["Resolution Prediction"])


@router.post(
    "/predict-resolution",
    response_model=ResolutionPredictionResponse,
    summary="Predict Event Resolution Time",
    description="Predicts how long a traffic event will take to resolve, "
                "with confidence and risk level.",
)
def predict_resolution(
    request: ResolutionPredictionRequest,
    db: Session = Depends(get_db),
):
    """Predict resolution time for a traffic event."""
    try:
        result = resolution_service.predict(request.model_dump(), db=db)
        return ResolutionPredictionResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
