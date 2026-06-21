"""
Feature Engineering Pipeline for TRINETRA AI.
Transforms raw traffic event data into ML-ready feature vectors.
Shared by all models (impact, resolution, resource, similarity).
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Optional
import joblib
from pathlib import Path

from app.utils.helpers import (
    EVENT_CAUSE_SEVERITY, CORRIDOR_IMPORTANCE,
    is_peak_hour, get_hour_of_day,
)


class FeatureEngineer:
    """
    Transforms raw event data into feature vectors for ML models.
    Maintains fitted encoders for consistent inference.
    """

    # Categorical columns to encode
    CATEGORICAL_COLS = [
        "event_type", "event_cause", "priority",
        "corridor", "zone", "junction", "veh_type",
    ]

    def __init__(self):
        self.label_encoders: dict[str, LabelEncoder] = {}
        self.scaler: Optional[StandardScaler] = None
        self.is_fitted = False
        self._feature_columns: list[str] = []

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit encoders on the dataset and transform to feature DataFrame.
        Call this during training.
        """
        features = self._build_features(df, fit=True)
        self.is_fitted = True
        return features

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform using previously fitted encoders.
        Call this during inference.
        """
        if not self.is_fitted:
            raise RuntimeError("FeatureEngineer not fitted. Call fit_transform first.")
        return self._build_features(df, fit=False)

    def transform_single(self, data: dict) -> pd.DataFrame:
        """Transform a single event dict into a feature row."""
        df = pd.DataFrame([data])
        return self.transform(df)

    def _build_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Core feature building logic."""
        feat = pd.DataFrame(index=df.index)

        # ── Temporal features ──────────────────────────────────
        if "start_datetime" in df.columns:
            dt = pd.to_datetime(df["start_datetime"], format="mixed", utc=True, errors="coerce")
            feat["hour_of_day"] = dt.dt.hour.fillna(12).astype(int)
            feat["day_of_week"] = dt.dt.dayofweek.fillna(3).astype(int)
            feat["is_weekend"] = (feat["day_of_week"] >= 5).astype(int)
            feat["month"] = dt.dt.month.fillna(6).astype(int)
            feat["is_peak_hour"] = feat["hour_of_day"].apply(lambda h: int(is_peak_hour(h)))
        else:
            feat["hour_of_day"] = 12
            feat["day_of_week"] = 3
            feat["is_weekend"] = 0
            feat["month"] = 6
            feat["is_peak_hour"] = 0

        # ── Derived severity features ─────────────────────────
        feat["event_cause_severity"] = df.get("event_cause", pd.Series("others")).map(
            EVENT_CAUSE_SEVERITY
        ).fillna(1).astype(int)

        feat["corridor_importance"] = df.get("corridor", pd.Series("Non-corridor")).map(
            CORRIDOR_IMPORTANCE
        ).fillna(2).astype(int)

        # ── Binary features ───────────────────────────────────
        if "requires_road_closure" in df.columns:
            feat["has_road_closure"] = df["requires_road_closure"].astype(int)
        else:
            feat["has_road_closure"] = 0

        if "endlatitude" in df.columns:
            feat["has_end_location"] = (
                df["endlatitude"].notna() & (df["endlatitude"] != 0)
            ).astype(int)
        else:
            feat["has_end_location"] = 0

        if "veh_type" in df.columns:
            feat["has_vehicle_info"] = df["veh_type"].notna().astype(int)
        else:
            feat["has_vehicle_info"] = 0

        # ── Priority numeric ──────────────────────────────────
        feat["priority_numeric"] = df.get("priority", pd.Series("Low")).map(
            {"High": 1, "Low": 0}
        ).fillna(0).astype(int)

        # ── Categorical label encoding ────────────────────────
        for col in self.CATEGORICAL_COLS:
            if col not in df.columns:
                df[col] = "unknown"

            series = df[col].fillna("unknown").astype(str)

            if fit:
                le = LabelEncoder()
                le.fit(series)
                self.label_encoders[col] = le
                feat[f"{col}_encoded"] = le.transform(series)
            else:
                le = self.label_encoders.get(col)
                if le is None:
                    feat[f"{col}_encoded"] = 0
                else:
                    # Handle unseen labels
                    feat[f"{col}_encoded"] = series.map(
                        lambda x, _le=le: (
                            _le.transform([x])[0] if x in _le.classes_
                            else len(_le.classes_)
                        )
                    )

        # ── Geospatial features ───────────────────────────────
        if "latitude" in df.columns:
            feat["latitude"] = df["latitude"].fillna(12.97).astype(float)
            feat["longitude"] = df["longitude"].fillna(77.59).astype(float)
        else:
            feat["latitude"] = 12.97
            feat["longitude"] = 77.59

        # ── Store feature column list ─────────────────────────
        self._feature_columns = list(feat.columns)

        # Fill any remaining NaN
        feat = feat.fillna(0)

        return feat

    @property
    def feature_columns(self) -> list[str]:
        return self._feature_columns

    def save(self, path: Path):
        """Persist the fitted encoders."""
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "label_encoders": self.label_encoders,
            "feature_columns": self._feature_columns,
            "is_fitted": self.is_fitted,
        }, path / "feature_engineer.joblib")

    def load(self, path: Path):
        """Load previously fitted encoders."""
        data = joblib.load(path / "feature_engineer.joblib")
        self.label_encoders = data["label_encoders"]
        self._feature_columns = data["feature_columns"]
        self.is_fitted = data["is_fitted"]
