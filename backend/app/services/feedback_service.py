"""
Post-Event Learning / Feedback Service.
Handles prediction logging, feedback collection, and model performance monitoring.
"""

import numpy as np
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.prediction_log_repository import PredictionLogRepository
from app.ml.model_registry import registry


class FeedbackService:
    """Service for continual learning feedback loop."""

    def submit_feedback(
        self,
        prediction_id: str,
        actual_outcome: Optional[dict],
        feedback_text: Optional[str],
        db: Session,
    ) -> dict:
        """Submit feedback for a previous prediction."""
        repo = PredictionLogRepository(db)

        log = repo.get_by_id(prediction_id)
        if not log:
            return {"status": "error", "prediction_id": prediction_id,
                    "updated_metrics": {"error": "Prediction not found"}}

        # Compute error metric if possible
        error_metric = None
        if actual_outcome and log.prediction:
            error_metric = self._compute_error(log.prediction, actual_outcome, log.prediction_type)

        updated = repo.update_feedback(
            prediction_id=prediction_id,
            actual_outcome=actual_outcome,
            feedback_text=feedback_text,
            error_metric=error_metric,
        )

        return {
            "status": "success",
            "prediction_id": prediction_id,
            "updated_metrics": {
                "error_metric": error_metric,
                "feedback_recorded": True,
            },
        }

    def get_model_performance(self, db: Session) -> dict:
        """Get performance metrics for all models."""
        repo = PredictionLogRepository(db)

        models_info = []
        all_metadata = registry.get_all_metadata()

        # Iterate through known feature types
        for feature_name in ["impact", "resolution", "resource", "similarity"]:
            meta = all_metadata.get(f"{feature_name}_best", {})

            # Get prediction stats
            pred_count = repo.get_count_by_type(feature_name)
            recent_errors = repo.get_recent_errors(feature_name)

            # Compute drift score (simple: compare recent MAE vs training MAE)
            drift_score = None
            if recent_errors and meta.get("metrics", {}).get("mae"):
                recent_mae = float(np.mean(recent_errors))
                train_mae = float(meta["metrics"]["mae"])
                drift_score = round(abs(recent_mae - train_mae) / max(train_mae, 1e-6), 4)

            metrics = meta.get("metrics", {})

            models_info.append({
                "model_name": f"{feature_name}_best",
                "feature_name": feature_name,
                "model_type": meta.get("model_type", "unknown"),
                "mae": metrics.get("mae"),
                "rmse": metrics.get("rmse"),
                "r2": metrics.get("r2"),
                "accuracy": metrics.get("accuracy"),
                "drift_score": drift_score,
                "last_trained": meta.get("trained_at"),
                "prediction_count": pred_count,
                "is_active": registry.is_model_available(feature_name),
            })

        total_preds = repo.get_count_by_type()
        feedback_count = repo.get_feedback_count()

        return {
            "models": models_info,
            "total_predictions": total_preds,
            "feedback_count": feedback_count,
        }

    def _compute_error(self, prediction: dict, actual: dict, pred_type: str) -> Optional[float]:
        """Compute error metric between prediction and actual outcome."""
        try:
            if pred_type == "impact" and "impact_score" in prediction and "impact_score" in actual:
                return abs(float(prediction["impact_score"]) - float(actual["impact_score"]))
            elif pred_type == "resolution" and "estimated_resolution_minutes" in prediction:
                if "actual_resolution_minutes" in actual:
                    return abs(float(prediction["estimated_resolution_minutes"]) -
                             float(actual["actual_resolution_minutes"]))
            return None
        except (ValueError, TypeError):
            return None


feedback_service = FeedbackService()
