"""
Tests for Impact Scoring API and model.
"""

import pytest
import pandas as pd
import numpy as np


class TestImpactScoring:
    """Tests for the impact scoring feature."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TRINETRA AI"
        assert "endpoints" in data

    def test_health_endpoint(self, client):
        """Test health check returns valid response."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "models_loaded" in data

    def test_predict_impact_without_model(self, client):
        """Test impact prediction gracefully fails when model not trained."""
        payload = {
            "event_type": "unplanned",
            "event_cause": "accident",
            "requires_road_closure": True,
            "priority": "High",
        }
        response = client.post("/predict-impact", json=payload)
        # Should return 503 when model not loaded
        assert response.status_code in [200, 503]

    def test_impact_score_derivation(self):
        """Test that impact score derivation produces valid scores."""
        from app.ml.impact_model import derive_impact_score

        df = pd.DataFrame({
            "event_cause": ["accident", "vehicle_breakdown", "pot_holes"],
            "requires_road_closure": [True, False, False],
            "priority": ["High", "Low", "Low"],
            "resolution_minutes": [120.0, 60.0, 30.0],
            "corridor": ["Hosur Road", "Non-corridor", "Non-corridor"],
            "start_datetime": [
                "2024-03-07 17:01:48.111+00",
                "2024-01-30 12:07:24.173+00",
                "2024-01-30 02:00:00.000+00",
            ],
            "veh_type": ["heavy_vehicle", None, None],
        })

        scores = derive_impact_score(df)

        assert len(scores) == 3
        assert all(0 <= s <= 100 for s in scores)
        # Accident with closure should score higher than pothole
        assert scores.iloc[0] > scores.iloc[2]


class TestFeatureEngineering:
    """Tests for the feature engineering pipeline."""

    def test_feature_engineer_fit_transform(self):
        """Test feature engineering produces expected features."""
        from app.ml.feature_engineering import FeatureEngineer

        df = pd.DataFrame({
            "event_type": ["unplanned", "planned"],
            "event_cause": ["accident", "construction"],
            "priority": ["High", "Low"],
            "corridor": ["Hosur Road", "Non-corridor"],
            "zone": ["South Zone 1", None],
            "junction": ["SilkBoardJunc", None],
            "veh_type": ["heavy_vehicle", None],
            "requires_road_closure": [True, False],
            "start_datetime": [
                "2024-03-07 17:01:48.111+00",
                "2024-01-30 04:07:24.173+00",
            ],
            "latitude": [12.97, 12.95],
            "longitude": [77.59, 77.58],
            "endlatitude": [12.98, 0],
            "endlongitude": [77.60, 0],
        })

        fe = FeatureEngineer()
        features = fe.fit_transform(df)

        assert len(features) == 2
        assert "hour_of_day" in features.columns
        assert "event_cause_severity" in features.columns
        assert "has_road_closure" in features.columns
        assert "priority_numeric" in features.columns
        assert features["has_road_closure"].iloc[0] == 1
        assert features["has_road_closure"].iloc[1] == 0

    def test_feature_engineer_transform_single(self):
        """Test single event transformation."""
        from app.ml.feature_engineering import FeatureEngineer

        df = pd.DataFrame({
            "event_type": ["unplanned"],
            "event_cause": ["accident"],
            "priority": ["High"],
            "corridor": ["Hosur Road"],
            "zone": ["South Zone 1"],
            "junction": ["SilkBoardJunc"],
            "veh_type": ["heavy_vehicle"],
            "requires_road_closure": [True],
            "start_datetime": ["2024-03-07 17:01:48"],
            "latitude": [12.97],
            "longitude": [77.59],
        })

        fe = FeatureEngineer()
        fe.fit_transform(df)

        single = fe.transform_single({
            "event_type": "unplanned",
            "event_cause": "accident",
            "priority": "High",
        })

        assert len(single) == 1
        assert not single.isnull().any().any()
