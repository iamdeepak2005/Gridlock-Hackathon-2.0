"""
Tests for Resource Recommendation.
"""

import pytest


class TestResourceRecommendation:
    """Tests for the resource recommendation feature."""

    def test_recommend_resources_endpoint(self, client):
        """Test resource recommendation endpoint."""
        payload = {
            "event_type": "unplanned",
            "event_cause": "accident",
            "priority": "High",
            "requires_road_closure": True,
        }
        response = client.post("/recommend-resources", json=payload)
        # Resource recommendation always works (rule-based fallback)
        assert response.status_code == 200
        data = response.json()
        assert "officers_required" in data
        assert "barricades_required" in data
        assert "tow_vehicles_required" in data
        assert data["officers_required"] >= 1
        assert data["confidence"] > 0

    def test_resource_rules_fallback(self):
        """Test that rule-based fallback produces sensible results."""
        from app.ml.resource_model import ResourceModel

        model = ResourceModel()
        from app.ml.feature_engineering import FeatureEngineer
        fe = FeatureEngineer()

        result = model.predict(
            {"event_cause": "accident", "requires_road_closure": True, "priority": "High"},
            fe,
        )

        assert result["officers_required"] >= 3
        assert result["barricades_required"] >= 4
        assert result["tow_vehicles_required"] >= 1

    def test_resource_vehicle_breakdown(self):
        """Test resource recommendation for vehicle breakdown."""
        from app.ml.resource_model import ResourceModel
        from app.ml.feature_engineering import FeatureEngineer

        model = ResourceModel()
        fe = FeatureEngineer()

        result = model.predict(
            {"event_cause": "vehicle_breakdown", "requires_road_closure": False, "priority": "Low"},
            fe,
        )

        assert result["tow_vehicles_required"] >= 1
        assert result["officers_required"] >= 1
