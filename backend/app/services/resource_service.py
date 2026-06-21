"""
Resource Recommendation Service.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.ml.feature_engineering import FeatureEngineer
from app.ml.resource_model import ResourceModel
from app.ml.model_registry import registry
from app.repositories.prediction_log_repository import PredictionLogRepository
from app.config import settings


class ResourceService:
    """Service for resource recommendation."""

    def __init__(self):
        self._model = ResourceModel()
        self._feature_engineer: Optional[FeatureEngineer] = None
        self._is_loaded = False

    def _ensure_loaded(self):
        if self._is_loaded:
            return
        try:
            self._model.load(registry)
            self._feature_engineer = FeatureEngineer()
            self._feature_engineer.load(settings.model_dir_path / "resource")
            self._is_loaded = True
        except FileNotFoundError:
            # Use rule-based fallback
            self._feature_engineer = FeatureEngineer()
            self._is_loaded = True

    def predict(self, input_data: dict, db: Optional[Session] = None) -> dict:
        self._ensure_loaded()

        result = self._model.predict(input_data, self._feature_engineer)

        response = {
            "officers_required": result["officers_required"],
            "barricades_required": result["barricades_required"],
            "tow_vehicles_required": result["tow_vehicles_required"],
            "estimated_resolution_time": result["estimated_resolution_time"],
            "confidence": result["confidence"],
        }

        if db:
            try:
                repo = PredictionLogRepository(db)
                repo.create("resource", input_data, response)
            except Exception:
                pass

        return response

    @property
    def is_available(self) -> bool:
        return True  # Always available (rule-based fallback)


resource_service = ResourceService()
