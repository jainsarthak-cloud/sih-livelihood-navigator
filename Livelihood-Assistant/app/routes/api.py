"""API Router aggregator for version 1 endpoints."""

from fastapi import APIRouter
from app.routes import (
    health,
    profile,
    recommendations,
    speech,
    opportunities,
    market,
    roadmap,
    interview,
    livelihood,
    channel,
)

api_router = APIRouter()

# Register all V1 route modules
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(recommendations.router)
api_router.include_router(speech.router)
api_router.include_router(opportunities.router)
api_router.include_router(market.router)
api_router.include_router(roadmap.router)
api_router.include_router(interview.router)
api_router.include_router(livelihood.router)
api_router.include_router(channel.router)
