"""NSQF recommendation routes."""

from pathlib import Path
from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation.recommender import (
    BaseRecommendationService,
    RecommendationService,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def get_recommendation_service() -> BaseRecommendationService:
    """Compose repositories at the application boundary; the service never reads files."""
    seed_dir = Path(settings.SEED_DATA_DIR)
    repositories_and_loaders = (
        (SkillRepository(), SkillLoader(seed_dir / "skills.json")),
        (OccupationRepository(), OccupationLoader(seed_dir / "occupations.json")),
        (CourseRepository(), CourseLoader(seed_dir / "courses.json")),
        (OpportunityRepository(), OpportunityLoader(seed_dir / "opportunities.json")),
    )
    repositories = []
    for repository, loader in repositories_and_loaders:
        loaded = loader.load()
        if loaded.errors:
            raise RuntimeError(f"Cannot initialize recommendation seed data: {loaded.errors[0].reason}")
        for record in loaded.records:
            repository.add(record)
        repositories.append(repository)
    skill_repository, occupation_repository, course_repository, opportunity_repository = repositories
    return RecommendationService(occupation_repository, course_repository, opportunity_repository, skill_repository)


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate NSQF-aligned skilling and livelihood recommendations",
)
async def generate_recommendations(
    request: RecommendationRequest,
    service: BaseRecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    """Generate recommendations based on candidate profile."""
    return await service.get_recommendations(request)
