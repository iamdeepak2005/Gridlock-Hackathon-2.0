"""
Tests for Traffic Diversion Simulation.
"""

import pytest


class TestDiversion:
    """Tests for the traffic diversion simulation feature."""

    def test_simulate_diversion_endpoint(self, client):
        """Test diversion simulation endpoint."""
        payload = {
            "event_latitude": 12.9716,
            "event_longitude": 77.5946,
            "road_closure": True,
            "impact_radius_meters": 500,
        }
        response = client.post("/simulate-diversion", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "blocked_roads" in data
        assert "alternative_routes" in data
        assert "congestion_risk_score" in data
        assert 0 <= data["congestion_risk_score"] <= 100

    def test_diversion_without_closure(self, client):
        """Test diversion simulation without road closure."""
        payload = {
            "event_latitude": 13.0350,
            "event_longitude": 77.5970,
            "road_closure": False,
            "impact_radius_meters": 300,
        }
        response = client.post("/simulate-diversion", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["congestion_risk_score"] < 100

    def test_haversine_distance(self):
        """Test haversine distance calculation."""
        from app.simulation.traffic_diversion import TrafficDiversionEngine

        dist = TrafficDiversionEngine._haversine(
            12.9716, 77.5946,  # Bengaluru center
            12.9750, 77.5946,  # ~380m north
        )
        assert 300 < dist < 500  # Should be roughly 378m

    def test_fallback_simulation(self):
        """Test fallback simulation when OSMnx unavailable."""
        from app.simulation.traffic_diversion import TrafficDiversionEngine

        engine = TrafficDiversionEngine()
        result = engine._fallback_simulation(12.97, 77.59, True, 500)

        assert "blocked_roads" in result
        assert "alternative_routes" in result
        assert "congestion_risk_score" in result
        assert len(result["alternative_routes"]) > 0
