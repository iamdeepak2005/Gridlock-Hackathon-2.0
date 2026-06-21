"""
Traffic Copilot Service.
Handles natural language operator queries by interfacing with Gemini API.
"""

import httpx
from typing import Optional
from app.config import settings

class CopilotService:
    """Service for AI Traffic Copilot query processing."""

    def __init__(self):
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def query(self, query_text: str) -> str:
        """
        Send the operator query to Gemini API and return the response text.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return "PROTOCOL_FAILURE: Gemini API Key is not configured on the backend. Please check your .env file."

        system_prompt = (
            "You are Trinetra AI, an advanced Traffic Copilot designed for city traffic police operations in Bengaluru. "
            "Your goal is to provide quick, accurate, and actionable insights to operators.\n\n"
            "If the operator is describing or reporting a new traffic incident (e.g. 'Report a vehicle breakdown on Hebbal Flyover', "
            "'There is a major accident near Silk Board', 'Protest blocking Richmond Road'), you must perform two actions:\n"
            "1. Provide a professional, tactical response confirming receipt and initial assessment.\n"
            "2. Underneath your response, on a single line, output [EVENT_JSON] followed by a JSON object containing the extracted details:\n"
            "{\n"
            "  \"event_type\": \"unplanned\" or \"planned\",\n"
            "  \"event_cause\": \"accident\", \"vehicle_breakdown\", \"tree_fall\", \"water_logging\", \"protest\", or \"other\",\n"
            "  \"description\": \"<short description>\",\n"
            "  \"zone\": \"<Bengaluru zone, e.g., North Zone 1, South Zone 1, Central Zone 1, East Zone 1, West Zone 1>\",\n"
            "  \"junction\": \"<junction name, e.g., HebbalFlyoverJunc, SilkBoardJunc, RichmondRoadJunc>\",\n"
            "  \"corridor\": \"<corridor name or Non-corridor>\",\n"
            "  \"priority\": \"High\" or \"Low\",\n"
            "  \"requires_road_closure\": true or false,\n"
            "  \"latitude\": <realistic float latitude in Bengaluru, e.g. Hebbal is ~13.03, Silk Board is ~12.91, Central is ~12.97>,\n"
            "  \"longitude\": <realistic float longitude in Bengaluru, e.g. ~77.59>\n"
            "}\n\n"
            "Example output when reporting:\n"
            "\"Tactical report received. Logged a vehicle breakdown at Hebbal Flyover. Initializing prediction engines and routing simulations.\"\n"
            "[EVENT_JSON] {\"event_type\": \"unplanned\", \"event_cause\": \"vehicle_breakdown\", \"description\": \"BMTC breakdown on Hebbal flyover\", \"zone\": \"North Zone 1\", \"junction\": \"HebbalFlyoverJunc\", \"corridor\": \"Bellary Road\", \"priority\": \"High\", \"requires_road_closure\": false, \"latitude\": 13.0350, \"longitude\": 77.5980}\n\n"
            "If they are just asking general questions, do not output the [EVENT_JSON] line.\n\n"
            f"Operator's Query: {query_text}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt}
                    ]
                }
            ]
        }

        try:
            # Use httpx to POST to Gemini API
            url = f"{self.api_url}?key={api_key}"
            response = httpx.post(url, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                return f"PROTOCOL_FAILURE: Gemini API returned status {response.status_code}. Response: {response.text}"

            response_data = response.json()
            
            # Navigate safety checks and content structure
            candidates = response_data.get("candidates", [])
            if not candidates:
                return "PROTOCOL_FAILURE: No text response candidates returned by Gemini."
                
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return "PROTOCOL_FAILURE: Empty content parts returned by Gemini."

            text_response = parts[0].get("text", "")
            if not text_response:
                return "PROTOCOL_FAILURE: Received an empty message from Gemini."

            return text_response.strip()

        except Exception as e:
            return f"PROTOCOL_FAILURE: Secure uplink timed out or encountered an issue. Detail: {str(e)}"

# Global service instance
copilot_service = CopilotService()
