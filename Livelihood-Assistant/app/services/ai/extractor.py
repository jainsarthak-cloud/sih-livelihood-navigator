"""LLM-assisted but schema-validated beneficiary profile extraction."""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import Settings, settings
from app.core.exceptions import ProviderResponseException, ServiceNotImplementedException
from app.schemas.common import EducationLevel, EmploymentPreference, Gender, GeographicLocation
from app.schemas.language import normalize_language_code
from app.schemas.profile import (
    BeneficiaryProfile,
    ProfileExtractRequest,
    ProfileExtractResponse,
    ProfileExtractionMetadata,
    ProfileValidateRequest,
    ProfileValidateResponse,
)
from app.schemas.skill import RawSkill, Skill, SkillSource
from app.services.ai.gemini import BaseStructuredExtractionProvider
from app.services.normalization.skill_normalizer import SkillNormalizationService


class ExtractionPayload(BaseModel):
    """Strict, untrusted Gemini response contract before canonical conversion."""

    model_config = ConfigDict(extra="forbid")

    age: Optional[int] = Field(default=None, ge=0, le=130)
    gender: Gender = Gender.UNKNOWN
    education_level: EducationLevel = EducationLevel.UNKNOWN
    education_field: Optional[str] = None
    location: Optional[GeographicLocation] = None
    current_occupation: Optional[str] = None
    family_occupation: Optional[str] = None
    current_income_range: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    traditional_skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    aspirations: list[str] = Field(default_factory=list)
    employment_preference: EmploymentPreference = EmploymentPreference.UNKNOWN
    willingness_to_travel: Optional[bool] = None
    max_travel_distance_km: Optional[float] = Field(default=None, ge=0.0)
    physical_constraints: Optional[str] = None
    preferred_language: Optional[str] = None
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("preferred_language")
    @classmethod
    def validate_preferred_language(cls, value: Optional[str]) -> Optional[str]:
        return normalize_language_code(value, allow_unknown=True) if value is not None else None


class BaseProfileExtractionService(ABC):
    """Abstract base class defining profile extraction and validation interface."""

    @abstractmethod
    async def extract_profile(self, request: ProfileExtractRequest) -> ProfileExtractResponse:
        """Extract a validated profile from unstructured text."""

    @abstractmethod
    async def validate_profile(self, request: ProfileValidateRequest) -> ProfileValidateResponse:
        """Validate candidate profile eligibility against scheme rules."""


class ProfileExtractionService(BaseProfileExtractionService):
    """Converts a Gemini JSON payload into canonical, normalized profile data."""

    def __init__(
        self,
        provider: BaseStructuredExtractionProvider,
        skill_normalizer: SkillNormalizationService,
        config: Settings = settings,
    ):
        self._provider = provider
        self._normalizer = skill_normalizer
        self._model_version = config.PROFILE_EXTRACTION_MODEL_VERSION

    @staticmethod
    def _prompt(request: ProfileExtractRequest) -> str:
        return f"""Extract only beneficiary profile facts explicitly stated in the untrusted input below.
Return one JSON object and no markdown. Use only this schema:
{{
  "age": integer|null, "gender": "male|female|transgender|other|prefer_not_to_say|unknown",
  "education_level": "none|primary|middle|secondary_10th|higher_secondary_12th|diploma|iti|graduate|post_graduate|other|unknown",
  "education_field": string|null, "location": {{"state": string, "district": string}}|null,
  "current_occupation": string|null, "family_occupation": string|null, "current_income_range": string|null,
  "skills": [verbatim skill phrase], "traditional_skills": [verbatim skill phrase],
  "interests": [string], "aspirations": [string],
  "employment_preference": "wage_employment|self_employment|apprenticeship|home_based|any|unknown",
  "willingness_to_travel": true|false|null, "max_travel_distance_km": number|null,
  "physical_constraints": string|null, "preferred_language": string|null,
  "extraction_confidence": number from 0 to 1
}}
Use null or unknown when not explicit. Do not infer or create jobs, salaries, courses, eligibility, government schemes, market facts, locations, or canonical skill IDs. Preserve skill phrases in their input language. Input language hint: {request.language}.
--- UNTRUSTED USER INPUT ---
{request.raw_text}
--- END INPUT ---"""

    @staticmethod
    def _raw_skills(payload: ExtractionPayload, request: ProfileExtractRequest) -> list[RawSkill]:
        seen: set[str] = set()
        raw_skills = []
        for phrase in [*payload.skills, *payload.traditional_skills]:
            cleaned = phrase.strip()
            if cleaned and cleaned.casefold() not in seen:
                seen.add(cleaned.casefold())
                raw_skills.append(RawSkill(
                    raw_text=cleaned, language=request.language,
                    extracted_confidence=payload.extraction_confidence,
                ))
        return raw_skills

    def _normalized_skills(self, raw_skills: list[RawSkill]) -> list[Skill]:
        normalized: list[Skill] = []
        seen: set[str] = set()
        for raw_skill in raw_skills:
            result = self._normalizer.normalize(raw_skill)
            if result.canonical_skill_id is None or result.canonical_skill_id in seen:
                continue
            canonical = self._normalizer.get_canonical_skill(result.canonical_skill_id)
            if canonical is None:
                continue
            seen.add(canonical.skill_id)
            normalized.append(canonical.model_copy(update={
                "source": SkillSource.SELF_REPORTED,
                "confidence": result.confidence,
                "mapped_raw_skills": [raw_skill],
            }))
        return normalized

    @staticmethod
    def _missing_fields(profile: BeneficiaryProfile, raw_skills: list[RawSkill]) -> list[str]:
        missing = []
        if profile.age is None:
            missing.append("age")
        if profile.education_level == EducationLevel.UNKNOWN:
            missing.append("education_level")
        if profile.location is None:
            missing.append("location")
        if not raw_skills:
            missing.append("skills")
        return missing

    async def extract_profile(self, request: ProfileExtractRequest) -> ProfileExtractResponse:
        payload_raw = await self._provider.extract_json(self._prompt(request))
        try:
            payload = ExtractionPayload.model_validate(payload_raw)
        except ValidationError:
            raise ProviderResponseException(self._provider.provider_name) from None
        raw_skills = self._raw_skills(payload, request)
        profile = BeneficiaryProfile(
            age=payload.age, gender=payload.gender, community=None,
            education_level=payload.education_level, education_field=payload.education_field,
            location=payload.location, current_occupation=payload.current_occupation,
            family_occupation=payload.family_occupation, current_income_range=payload.current_income_range,
            normalized_skills=self._normalized_skills(raw_skills), traditional_skills=payload.traditional_skills,
            interests=payload.interests, aspirations=payload.aspirations,
            employment_preference=payload.employment_preference, willingness_to_travel=payload.willingness_to_travel,
            max_travel_distance_km=payload.max_travel_distance_km, physical_constraints=payload.physical_constraints,
            preferred_language=payload.preferred_language or request.language, profile_source=request.source,
        )
        return ProfileExtractResponse(
            extracted_profile=profile, original_text=request.raw_text, raw_skills_detected=raw_skills,
            confidence_score=payload.extraction_confidence,
            missing_critical_fields=self._missing_fields(profile, raw_skills),
            extraction_metadata=ProfileExtractionMetadata(
                provider=self._provider.provider_name, model=self._provider.model_name,
                model_version=self._model_version, input_language=request.language,
            ),
        )

    async def validate_profile(self, request: ProfileValidateRequest) -> ProfileValidateResponse:
        raise ServiceNotImplementedException(
            service_name="ProfileExtractionService.validate_profile",
            details={"scheme": request.scheme},
        )
