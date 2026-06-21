"""
Impact Scoring Service.
Orchestrates model loading, feature engineering, and prediction.
"""

import numpy as np
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_registry import registry
from app.repositories.prediction_log_repository import PredictionLogRepository
from app.utils.helpers import compute_impact_level
from app.config import settings


class ImpactService:
    """Service for impact score prediction."""

    def __init__(self):
        self._model = None
        self._feature_engineer: Optional[FeatureEngineer] = None
        self._is_loaded = False

    def _ensure_loaded(self):
        """Lazy-load the model and feature engineer."""
        if self._is_loaded:
            return

        try:
            self._model = registry.load_model("impact", "best")
            self._feature_engineer = FeatureEngineer()
            self._feature_engineer.load(settings.model_dir_path / "impact")
            self._is_loaded = True
        except FileNotFoundError:
            raise RuntimeError(
                "Impact model not trained. Run: python -m app.training.train_all"
            )

    def predict(self, input_data: dict, db: Optional[Session] = None) -> dict:
        """
        Predict impact score for an event.

        Returns dict with impact_score, impact_level, confidence, top_contributing_factors.
        """
        self._ensure_loaded()

        # Transform input to features
        X = self._feature_engineer.transform_single(input_data)

        # Predict
        raw_score = float(self._model.predict(X)[0])
        impact_score = round(max(0, min(100, raw_score)), 2)

        # Impact level
        impact_level = compute_impact_level(impact_score)

        # Confidence (use prediction variance from tree models)
        confidence = self._compute_confidence(X)

        # Feature importance (from the model)
        top_factors = self._get_contributing_factors(X)

        result = {
            "impact_score": impact_score,
            "impact_level": impact_level,
            "confidence": confidence,
            "top_contributing_factors": top_factors,
        }

        # Log prediction
        if db:
            try:
                repo = PredictionLogRepository(db)
                repo.create("impact", input_data, result)
            except Exception:
                pass  # Don't fail prediction if logging fails

        return result

    def _compute_confidence(self, X) -> float:
        """Estimate prediction confidence."""
        # For tree ensembles, use individual tree predictions to estimate variance
        if hasattr(self._model, "estimators_"):
            # RandomForest
            predictions = [tree.predict(X)[0] for tree in self._model.estimators_[:20]]
            std = float(np.std(predictions))
            confidence = max(0.3, min(0.95, 1.0 - std / 50))
        elif hasattr(self._model, "get_booster"):
            # XGBoost
            confidence = 0.80
        else:
            confidence = 0.75

        return round(confidence, 2)

    def _get_contributing_factors(self, X) -> list[dict]:
        """Extract top contributing factors from the model."""
        if not hasattr(self._model, "feature_importances_"):
            return [{"feature": "model_prediction", "importance": 1.0}]

        importances = self._model.feature_importances_
        features = X.columns.tolist()

        pairs = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)
        return [
            {"feature": f, "importance": round(float(i), 4)}
            for f, i in pairs[:5]
        ]

    @property
    def is_available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except Exception:
            return False


# Global service instance
impact_service = ImpactService()
