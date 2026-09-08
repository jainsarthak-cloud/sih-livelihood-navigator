"""Personalized career and skilling roadmap routes."""

from pathlib import Path
from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.roadmap import RoadmapRequest, RoadmapResponse
from app.services.roadmap.generator import BaseRoadmapService, RoadmapService

router = APIRouter(prefix="/roadmap", tags=["Career Roadmap"])


def get_roadmap_service() -> BaseRoadmapService:
    """Compose canonical repositories at the boundary; roadmap logic reads no files."""
    seed_dir = Path(settings.SEED_DATA_DIR)
    repository_loaders = (
        (SkillRepository(), SkillLoader(seed_dir / "skills.json")),
        (OccupationRepository(), OccupationLoader(seed_dir / "occupations.json")),
        (CourseRepository(), CourseLoader(seed_dir / "courses.json")),
        (OpportunityRepository(), OpportunityLoader(seed_dir / "opportunities.json")),
    )
    repositories = []
    for repository, loader in repository_loaders:
        loaded = loader.load()
        if loaded.errors:
            raise RuntimeError(f"Cannot initialize roadmap seed data: {loaded.errors[0].reason}")
        for record in loaded.records:
            repository.add(record)
        repositories.append(repository)
    skill_repository, occupation_repository, course_repository, opportunity_repository = repositories
    return RoadmapService(occupation_repository, course_repository, opportunity_repository, skill_repository)


@router.post(
    "",
    response_model=RoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalized skilling & livelihood progression roadmap",
)
async def generate_career_roadmap(
    request: RoadmapRequest,
    service: BaseRoadmapService = Depends(get_roadmap_service),
) -> RoadmapResponse:
    """Generate structured step-by-step roadmap towards target NSQF role."""
    return await service.generate_roadmap(request)
