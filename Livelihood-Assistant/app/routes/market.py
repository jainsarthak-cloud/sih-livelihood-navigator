"""Regional opportunity-observation routes."""

from pathlib import Path
from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.data.loaders.domain_loaders import OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.market import MarketDemandRequest, MarketDemandResponse
from app.services.market.demand import BaseMarketDemandService, MarketDemandService
from app.services.normalization.skill_normalizer import SkillNormalizationService
from app.services.opportunity.intelligence import OpportunityIntelligenceService

router = APIRouter(prefix="/market", tags=["Market Intelligence"])


def get_market_service() -> BaseMarketDemandService:
    seed_dir = Path(settings.SEED_DATA_DIR)
    source = (
        (SkillRepository(), SkillLoader(seed_dir / "skills.json")),
        (OccupationRepository(), OccupationLoader(seed_dir / "occupations.json")),
        (OpportunityRepository(), OpportunityLoader(seed_dir / "opportunities.json")),
    )
    repositories = []
    for repository, loader in source:
        loaded = loader.load()
        if loaded.errors:
            raise RuntimeError(f"Cannot initialize market seed data: {loaded.errors[0].reason}")
        for record in loaded.records:
            repository.add(record)
        repositories.append(repository)
    skill_repository, occupation_repository, opportunity_repository = repositories
    intelligence = OpportunityIntelligenceService(
        opportunity_repository, occupation_repository, SkillNormalizationService(skill_repository, settings)
    )
    return MarketDemandService(opportunity_repository, intelligence)


@router.post(
    "/demand",
    response_model=MarketDemandResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch regional and district skill market demand trends",
)
async def get_market_demand(
    request: MarketDemandRequest,
    service: BaseMarketDemandService = Depends(get_market_service),
) -> MarketDemandResponse:
    """Analyze and return district-level labor market demand."""
    return await service.analyze_demand(request)
