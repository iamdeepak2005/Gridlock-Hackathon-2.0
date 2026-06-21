"""
Similar Event Retrieval Service.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.ml.similarity_model import SimilarityModel
from app.ml.model_registry import registry
from app.repositories.prediction_log_repository import PredictionLogRepository


class SimilarityService:
    """Service for finding similar historical events."""

    def __init__(self):
        self._model = SimilarityModel()
        self._is_loaded = False

    def _ensure_loaded(self):
        if self._is_loaded:
            return
        try:
            self._model.load(registry)
            self._is_loaded = True
        except FileNotFoundError:
            raise RuntimeError(
                "Similarity model not trained. Run: python -m app.training.train_all"
            )

    def find_similar(self, input_data: dict, k: int = 5, db: Optional[Session] = None) -> dict:
        self._ensure_loaded()

        result = self._model.find_similar(input_data, k=k)

        if db:
            try:
                repo = PredictionLogRepository(db)
                # Store a summarized version to avoid huge JSONB
                log_result = {
                    "num_similar": len(result.get("similar_events", [])),
                    "avg_resolution": result.get("average_resolution_time"),
                    "recommended_action": result.get("recommended_action"),
                }
                repo.create("similar", input_data, log_result)
            except Exception:
                pass

        return result

    @property
    def is_available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except Exception:
            return False


similarity_service = SimilarityService()
