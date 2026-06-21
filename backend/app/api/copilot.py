"""
Traffic Copilot API endpoint.
POST /copilot
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import CopilotRequest, CopilotResponse
from app.services.copilot_service import copilot_service

router = APIRouter(tags=["AI Traffic Copilot"])

@router.post(
    "/copilot",
    response_model=CopilotResponse,
    summary="Query Traffic Copilot",
    description="Processes operator queries using Gemini to provide tactical advice and structure incidents.",
)
def query_copilot(request: CopilotRequest):
    """Query AI copilot for natural language responses and event extraction."""
    try:
        response_text = copilot_service.query(request.query)
        return CopilotResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot query failed: {str(e)}")
