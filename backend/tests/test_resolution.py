"""
Tests for Resolution Time Prediction.
"""

import pytest
import pandas as pd


class TestResolutionPrediction:
    """Tests for the resolution time prediction feature."""

    def test_predict_resolution_without_model(self, client):
        """Test resolution prediction gracefully fails when model not trained."""
        payload = {
            "event_type": "unplanned",
            "event_cause": "vehicle_breakdown",
            "priority": "High",
        }
        response = client.post("/predict-resolution", json=payload)
        assert response.status_code in [200, 503]

    def test_resolution_data_preparation(self):
        """Test resolution data filtering logic."""
        from app.ml.resolution_model import prepare_resolution_data

        df = pd.DataFrame({
            "start_datetime": [
                "2024-01-30 04:07:24.173+00",
                "2024-01-30 05:00:00.000+00",
                "2024-01-30 06:00:00.000+00",
            ],
            "closed_datetime": [
                "2024-01-30 06:07:24.173+00",
                None,
                "2024-01-30 08:00:00.000+00",
            ],
            "resolved_datetime": [None, None, None],
        })

        valid = prepare_resolution_data(df)
        assert len(valid) == 2  # Only rows with closed_datetime
        assert all(valid["resolution_minutes"] > 0)
