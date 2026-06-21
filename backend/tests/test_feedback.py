"""
Tests for Feedback / Continual Learning.
"""

import pytest


class TestFeedback:
    """Tests for the feedback and model performance features."""

    def test_model_performance_endpoint(self, client):
        """Test model performance endpoint returns valid response."""
        response = client.get("/model-performance")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "total_predictions" in data
        assert "feedback_count" in data

    def test_feedback_submission_missing_prediction(self, client):
        """Test feedback for non-existent prediction."""
        payload = {
            "prediction_id": "non-existent-id",
            "feedback_text": "Test feedback",
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Should handle gracefully
        assert "prediction_id" in data
