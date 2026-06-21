"""
Feedback / Continual Learning API endpoints.
POST /feedback
GET /model-performance
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import (
    FeedbackRequest, FeedbackResponse,
    ModelPerformanceResponse, ModelPerformanceItem,
)
from app.services.feedback_service import feedback_service
from app.database.connection import get_db

router = APIRouter(tags=["Feedback & Learning"])


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit Prediction Feedback",
    description="Submit actual outcome or feedback for a previous prediction "
                "to improve future model performance.",
)
def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """Submit feedback for a prediction."""
    try:
        result = feedback_service.submit_feedback(
            prediction_id=request.prediction_id,
            actual_outcome=request.actual_outcome,
            feedback_text=request.feedback_text,
            db=db,
        )
        return FeedbackResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@router.get(
    "/model-performance",
    response_model=ModelPerformanceResponse,
    summary="Get Model Performance Metrics",
    description="Returns MAE, RMSE, R2, accuracy, drift metrics, and prediction counts "
                "for all trained models.",
)
def get_model_performance(
    db: Session = Depends(get_db),
):
    """Get performance metrics for all models."""
    try:
        result = feedback_service.get_model_performance(db)

        models = [
            ModelPerformanceItem(**m)
            for m in result["models"]
        ]

        return ModelPerformanceResponse(
            models=models,
            total_predictions=result["total_predictions"],
            feedback_count=result["feedback_count"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
