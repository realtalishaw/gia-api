from fastapi import APIRouter
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        service="GIA API"
    )


@router.get("/heartbeat", response_model=HealthResponse)
async def heartbeat():
    """
    Heartbeat endpoint for monitoring.
    """
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow().isoformat(),
        service="GIA API"
    )

