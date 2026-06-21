"""
Tests for Similar Event Retrieval.
"""

import pytest


class TestSimilarEvents:
    """Tests for the similar events feature."""

    def test_similar_events_without_model(self, client):
        """Test similar events gracefully fails when model not trained."""
        payload = {
            "event_type": "unplanned",
            "event_cause": "vehicle_breakdown",
            "zone": "North Zone 1",
        }
        response = client.post("/similar-events", json=payload)
        assert response.status_code in [200, 503]

    def test_similarity_model_patterns(self):
        """Test pattern extraction logic."""
        from app.ml.similarity_model import SimilarityModel

        model = SimilarityModel()
        patterns = model._extract_patterns(
            [
                {"event_cause": "accident", "zone": "North Zone 1", "resolution_minutes": 120},
                {"event_cause": "accident", "zone": "North Zone 1", "resolution_minutes": 90},
                {"event_cause": "accident", "zone": "South Zone 1", "resolution_minutes": 60},
            ],
            {"event_cause": "accident"},
        )

        assert len(patterns) >= 1
        assert any("accident" in p for p in patterns)
