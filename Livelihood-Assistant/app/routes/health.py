"""Health check route."""

from fastapi import APIRouter, status
from pathlib import Path
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns service status, environment, version, and component availability.",
)
async def check_health() -> HealthResponse:
    """Check application health status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        services={
            "api": "online",
            "ai_extractor": "configured" if settings.GEMINI_API_KEY else "not_configured",
            "speech_transcriber": "configured" if settings.ASR_MODEL_PATH and Path(settings.ASR_MODEL_PATH).exists() else "not_configured",
            "skill_matcher": "registered",
            "recommendation_engine": "registered",
            "market_demand": "registered",
            "roadmap_generator": "registered",
        },
    )
