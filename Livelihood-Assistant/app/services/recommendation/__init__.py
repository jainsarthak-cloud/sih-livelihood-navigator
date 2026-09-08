"""Recommendation Services package."""

from app.services.recommendation.recommender import (
    BaseRecommendationService,
    RecommendationService,
)

__all__ = ["BaseRecommendationService", "RecommendationService"]
