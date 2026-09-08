"""Profile extraction and validation routes."""

from pathlib import Path
from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.data.loaders.domain_loaders import SkillLoader
from app.data.repositories.domain_repositories import SkillRepository
from app.schemas.profile import (
    ProfileExtractRequest,
    ProfileExtractResponse,
    ProfileValidateRequest,
    ProfileValidateResponse,
)
from app.services.ai.extractor import BaseProfileExtractionService, ProfileExtractionService
from app.services.ai.gemini import GeminiStructuredExtractionProvider
from app.services.normalization.skill_normalizer import SkillNormalizationService

router = APIRouter(prefix="/profile", tags=["Candidate Profile"])


def get_profile_service() -> BaseProfileExtractionService:
    """Compose Gemini and the canonical skill repository at the route boundary."""
    repository = SkillRepository()
    loaded = SkillLoader(Path(settings.SEED_DATA_DIR) / "skills.json").load()
    if loaded.errors:
        raise RuntimeError(f"Cannot initialize skill seed data: {loaded.errors[0].reason}")
    for skill in loaded.records:
        repository.add(skill)
    return ProfileExtractionService(
        GeminiStructuredExtractionProvider(settings),
        SkillNormalizationService(repository, settings),
        settings,
    )


@router.post(
    "/extract",
    response_model=ProfileExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract candidate profile from unstructured voice transcript/text",
)
async def extract_candidate_profile(
    request: ProfileExtractRequest,
    service: BaseProfileExtractionService = Depends(get_profile_service),
) -> ProfileExtractResponse:
    """Extract candidate profile using extraction service."""
    return await service.extract_profile(request)


@router.post(
    "/validate",
    response_model=ProfileValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate candidate eligibility against PM-AJAY and NSQF guidelines",
)
async def validate_candidate_profile(
    request: ProfileValidateRequest,
    service: BaseProfileExtractionService = Depends(get_profile_service),
) -> ProfileValidateResponse:
    """Validate candidate profile using validation rules service."""
    return await service.validate_profile(request)
