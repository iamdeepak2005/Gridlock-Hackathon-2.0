"""
Model Registry: Save, load, and manage trained ML models.
Handles model persistence via joblib and tracks metadata.
"""

import joblib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from app.config import settings


class ModelRegistry:
    """
    Centralized registry for trained ML models.
    Saves/loads models to/from disk and tracks active models per feature.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or settings.model_dir_path
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_models: dict[str, Any] = {}
        self._model_metadata: dict[str, dict] = {}

    def save_model(
        self,
        model: Any,
        feature_name: str,
        model_type: str,
        metrics: dict,
        is_best: bool = False,
    ) -> str:
        """
        Save a trained model to disk.

        Args:
            model: The trained ML model object.
            feature_name: e.g. 'impact', 'resolution', 'resource'
            model_type: e.g. 'xgboost', 'lightgbm', 'catboost', 'random_forest'
            metrics: Dict of evaluation metrics (mae, rmse, r2, etc.)
            is_best: Whether this is the best model for this feature.

        Returns:
            The file path where the model was saved.
        """
        filename = f"{feature_name}_{model_type}.joblib"
        filepath = self.model_dir / filename
        joblib.dump(model, filepath)

        # Track metadata
        meta = {
            "model_type": model_type,
            "feature_name": feature_name,
            "metrics": metrics,
            "file_path": str(filepath),
            "is_best": is_best,
            "trained_at": datetime.utcnow().isoformat(),
        }
        self._model_metadata[f"{feature_name}_{model_type}"] = meta

        if is_best:
            # Also save as the "active" model for this feature
            best_path = self.model_dir / f"{feature_name}_best.joblib"
            joblib.dump(model, best_path)
            self._model_metadata[f"{feature_name}_best"] = meta

        print(f"[REGISTRY] Saved {feature_name}/{model_type} -> {filepath}")
        return str(filepath)

    def load_model(self, feature_name: str, model_type: str = "best") -> Any:
        """
        Load a model from disk. Defaults to loading the best model.
        Caches loaded models in memory.
        """
        cache_key = f"{feature_name}_{model_type}"
        if cache_key in self._loaded_models:
            return self._loaded_models[cache_key]

        filepath = self.model_dir / f"{feature_name}_{model_type}.joblib"
        if not filepath.exists():
            raise FileNotFoundError(
                f"Model not found: {filepath}. Run training first."
            )

        model = joblib.load(filepath)
        self._loaded_models[cache_key] = model
        print(f"[REGISTRY] Loaded {feature_name}/{model_type} from {filepath}")
        return model

    def is_model_available(self, feature_name: str) -> bool:
        """Check if a best model exists for the given feature."""
        filepath = self.model_dir / f"{feature_name}_best.joblib"
        return filepath.exists()

    def get_all_metadata(self) -> dict[str, dict]:
        """Return metadata for all tracked models."""
        return self._model_metadata

    def list_available_models(self) -> list[str]:
        """List all .joblib model files in the model directory."""
        return [f.stem for f in self.model_dir.glob("*.joblib")]


# Global registry singleton
registry = ModelRegistry()
