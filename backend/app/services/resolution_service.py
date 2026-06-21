"""
Resolution Time Prediction Service.
"""

import numpy as np
from typing import Optional
from sqlalchemy.orm import Session

from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_registry import registry
from app.repositories.prediction_log_repository import PredictionLogRepository
from app.utils.helpers import compute_risk_level
from app.config import settings


class ResolutionService:
    """Service for resolution time prediction."""

    def __init__(self):
        self._model = None
        self._feature_engineer: Optional[FeatureEngineer] = None
        self._is_loaded = False

    def _ensure_loaded(self):
        if self._is_loaded:
            return
        try:
            self._model = registry.load_model("resolution", "best")
            self._feature_engineer = FeatureEngineer()
            self._feature_engineer.load(settings.model_dir_path / "resolution")
            self._is_loaded = True
        except FileNotFoundError:
            raise RuntimeError(
                "Resolution model not trained. Run: python -m app.training.train_all"
            )

    def predict(self, input_data: dict, db: Optional[Session] = None) -> dict:
        self._ensure_loaded()

        X = self._feature_engineer.transform_single(input_data)

        # Model predicts log1p(minutes), so inverse transform
        raw_pred = float(self._model.predict(X)[0])
        minutes = float(np.expm1(raw_pred))
        minutes = max(5.0, min(10080.0, minutes))  # Clip to 5min - 7days

        risk_level = compute_risk_level(minutes)

        # Confidence
        confidence = self._compute_confidence(X)

        result = {
            "estimated_resolution_minutes": round(minutes, 1),
            "confidence": confidence,
            "risk_level": risk_level,
        }

        if db:
            try:
                repo = PredictionLogRepository(db)
                repo.create("resolution", input_data, result)
            except Exception:
                pass

        return result

    def _compute_confidence(self, X) -> float:
        if hasattr(self._model, "estimators_"):
            predictions = [np.expm1(tree.predict(X)[0]) for tree in self._model.estimators_[:20]]
            std = float(np.std(predictions))
            mean = float(np.mean(predictions))
            cv = std / mean if mean > 0 else 1.0
            confidence = max(0.3, min(0.95, 1.0 - cv))
        else:
            confidence = 0.75
        return round(confidence, 2)

    @property
    def is_available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except Exception:
            return False


resolution_service = ResolutionService()
