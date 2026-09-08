"""Opportunity normalization and local matching routes."""

from pathlib import Path
from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.data.loaders.domain_loaders import OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.opportunity import OpportunityMatchRequest, OpportunityMatchResponse, OpportunityParseRequest, OpportunityParseResponse
from app.services.opportunity.parser import (
    BaseOpportunityParsingService,
    OpportunityParsingService,
)
from app.services.opportunity.intelligence import OpportunityIntelligenceService
from app.services.normalization.skill_normalizer import SkillNormalizationService

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


def get_opportunity_service() -> BaseOpportunityParsingService:
    skill_repository, occupation_repository, _ = _repositories()
    return OpportunityParsingService(occupation_repository, SkillNormalizationService(skill_repository, settings))


def _repositories():
    """Build canonical repositories at the route boundary; services never read seed files."""
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
            raise RuntimeError(f"Cannot initialize opportunity seed data: {loaded.errors[0].reason}")
        for record in loaded.records:
            repository.add(record)
        repositories.append(repository)
    return repositories


def get_opportunity_intelligence_service() -> OpportunityIntelligenceService:
    skill_repository, occupation_repository, opportunity_repository = _repositories()
    return OpportunityIntelligenceService(
        opportunity_repository, occupation_repository, SkillNormalizationService(skill_repository, settings)
    )


@router.post(
    "/parse",
    response_model=OpportunityParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse opportunities from circulars, announcements, or scheme documents",
)
async def parse_opportunities(
    request: OpportunityParseRequest,
    service: BaseOpportunityParsingService = Depends(get_opportunity_service),
) -> OpportunityParseResponse:
    """Parse unstructured circular text into structured opportunities."""
    return await service.parse_opportunities(request)


@router.post(
    "/match",
    response_model=OpportunityMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Match active canonical opportunities against a beneficiary profile",
)
async def match_opportunities(
    request: OpportunityMatchRequest,
    service: OpportunityIntelligenceService = Depends(get_opportunity_intelligence_service),
) -> OpportunityMatchResponse:
    return await service.match_opportunities(request)
