"""
Tests for AI Traffic Copilot endpoint.
"""

import pytest

class TestCopilot:
    """Tests for the Copilot endpoint."""

    def test_copilot_endpoint_success(self, client):
        """Test that the /copilot endpoint returns a valid response format."""
        payload = {
            "query": "Is there a traffic incident on Richmond Road?"
        }
        # Since it calls Gemini, it might return a PROTOCOL_FAILURE if api key is mock/invalid,
        # but the HTTP status code should be 200 (gracefully handles and returns text).
        response = client.post("/copilot", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0
