"""High-level structured deterministic livelihood assessment endpoint."""

from pathlib import Path

from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.livelihood import LivelihoodAssessRequest, LivelihoodAssessResponse
from app.services.livelihood.assessment import LivelihoodAssessmentService
from app.services.market.demand import MarketDemandService
from app.services.normalization.skill_normalizer import SkillNormalizationService
from app.services.opportunity.intelligence import OpportunityIntelligenceService
from app.services.recommendation.recommender import RecommendationService
from app.services.roadmap.generator import RoadmapService

router = APIRouter(prefix="/livelihood", tags=["Livelihood Assessment"])


def get_livelihood_assessment_service() -> LivelihoodAssessmentService:
    """Compose all existing deterministic services over one seed repository snapshot."""
    seed_dir = Path(settings.SEED_DATA_DIR)
    source = (
        (SkillRepository(), SkillLoader(seed_dir / "skills.json")),
        (OccupationRepository(), OccupationLoader(seed_dir / "occupations.json")),
        (CourseRepository(), CourseLoader(seed_dir / "courses.json")),
        (OpportunityRepository(), OpportunityLoader(seed_dir / "opportunities.json")),
    )
    repositories = []
    for repository, loader in source:
        loaded = loader.load()
        if loaded.errors:
            raise RuntimeError(f"Cannot initialize livelihood assessment seed data: {loaded.errors[0].reason}")
        for record in loaded.records:
            repository.add(record)
        repositories.append(repository)
    skills, occupations, courses, opportunities = repositories
    normalizer = SkillNormalizationService(skills, settings)
    intelligence = OpportunityIntelligenceService(opportunities, occupations, normalizer)
    return LivelihoodAssessmentService(
        RecommendationService(occupations, courses, opportunities, skills, normalizer, settings),
        intelligence,
        MarketDemandService(opportunities, intelligence),
        RoadmapService(occupations, courses, opportunities, skills, normalizer),
        settings,
    )


@router.post(
    "/assess",
    response_model=LivelihoodAssessResponse,
    status_code=status.HTTP_200_OK,
    summary="Run structured, deterministic livelihood assessment over canonical repository data",
)
async def assess_livelihood(
    request: LivelihoodAssessRequest,
    service: LivelihoodAssessmentService = Depends(get_livelihood_assessment_service),
) -> LivelihoodAssessResponse:
    """Assess a structured profile; ASR and LLM extraction are intentionally not required."""
    return await service.assess(request)
