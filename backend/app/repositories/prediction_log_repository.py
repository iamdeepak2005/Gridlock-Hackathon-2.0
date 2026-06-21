"""
Repository for prediction log CRUD operations.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import PredictionLog


class PredictionLogRepository:
    """Data access layer for prediction logs."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        prediction_type: str,
        input_data: dict,
        prediction: dict,
    ) -> PredictionLog:
        """Log a new prediction."""
        log = PredictionLog(
            id=str(uuid.uuid4()),
            prediction_type=prediction_type,
            input_data=input_data,
            prediction=prediction,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_id(self, prediction_id: str) -> Optional[PredictionLog]:
        return self.db.query(PredictionLog).filter(PredictionLog.id == prediction_id).first()

    def update_feedback(
        self,
        prediction_id: str,
        actual_outcome: Optional[dict] = None,
        feedback_text: Optional[str] = None,
        error_metric: Optional[float] = None,
    ) -> Optional[PredictionLog]:
        """Update a prediction log with actual outcome and feedback."""
        log = self.get_by_id(prediction_id)
        if not log:
            return None

        if actual_outcome is not None:
            log.actual_outcome = actual_outcome
        if feedback_text is not None:
            log.feedback = feedback_text
        if error_metric is not None:
            log.error_metric = error_metric
        log.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(log)
        return log

    def get_count_by_type(self, prediction_type: Optional[str] = None) -> int:
        """Get total prediction count, optionally filtered by type."""
        query = self.db.query(func.count(PredictionLog.id))
        if prediction_type:
            query = query.filter(PredictionLog.prediction_type == prediction_type)
        return query.scalar() or 0

    def get_feedback_count(self) -> int:
        """Count predictions that have received feedback."""
        return self.db.query(func.count(PredictionLog.id)).filter(
            PredictionLog.feedback.isnot(None)
        ).scalar() or 0

    def get_recent_errors(self, prediction_type: str, limit: int = 100) -> list[float]:
        """Get recent error metrics for drift analysis."""
        logs = (
            self.db.query(PredictionLog.error_metric)
            .filter(
                PredictionLog.prediction_type == prediction_type,
                PredictionLog.error_metric.isnot(None),
            )
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [log.error_metric for log in logs if log.error_metric is not None]
