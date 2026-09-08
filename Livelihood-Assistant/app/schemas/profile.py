"""Canonical beneficiary profile domain models and profile API contracts."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.common import (
    EducationLevel,
    EmploymentPreference,
    Gender,
    GeographicLocation,
    ProfileSource,
    SourceEvidence,
)
from app.schemas.eligibility import EligibilityResult
from app.schemas.skill import RawSkill, Skill
from app.schemas.language import normalize_language_code


class EducationEntry(BaseModel):
    """Structured educational milestone or qualification."""

    level: EducationLevel = Field(
        default=EducationLevel.UNKNOWN, description="Standardized education level"
    )
    field_of_study: Optional[str] = Field(
        default=None, description="Specialization or major (e.g. Science, Arts, ITI Fitter)"
    )
    institution: Optional[str] = Field(default=None, description="School, college, or institute name")
    year_completed: Optional[int] = Field(
        default=None, ge=1950, le=2035, description="Year of passing"
    )


class WorkHistoryEntry(BaseModel):
    """Candidate prior formal or informal livelihood experience."""

    role_title: str = Field(..., description="Job role or informal livelihood task")
    sector: Optional[str] = Field(default=None, description="Economic sector or craft domain")
    years_experience: Optional[float] = Field(
        default=None, ge=0.0, le=60.0, description="Duration in years"
    )
    skills_practiced: List[str] = Field(
        default_factory=list, description="Skills actively exercised during this tenure"
    )


class BeneficiaryProfile(BaseModel):
    """Canonical domain model for PM-AJAY beneficiaries and skilling candidates."""

    beneficiary_id: Optional[str] = Field(
        default=None, description="Unique beneficiary or session identifier"
    )
    age: Optional[int] = Field(default=None, ge=0, le=130, description="Beneficiary age in years")
    gender: Gender = Field(
        default=Gender.UNKNOWN,
        description="Beneficiary gender, explicit UNKNOWN when uncollected",
    )
    community: Optional[str] = Field(
        default="SC", description="Target socio-economic group (e.g. Scheduled Caste)"
    )
    education_level: EducationLevel = Field(
        default=EducationLevel.UNKNOWN, description="Highest verified education attainment"
    )
    education_field: Optional[str] = Field(
        default=None, description="Academic or vocational specialization"
    )
    education_history: List[EducationEntry] = Field(
        default_factory=list, description="Chronological education details"
    )
    location: Optional[GeographicLocation] = Field(
        default=None, description="Geographic location details"
    )
    current_occupation: Optional[str] = Field(
        default=None, description="Current primary livelihood or job activity"
    )
    family_occupation: Optional[str] = Field(
        default=None, description="Traditional or primary household livelihood"
    )
    current_income_range: Optional[str] = Field(
        default=None, description="Monthly or annual income bracket (e.g. '< 1.0 Lakh')"
    )
    normalized_skills: List[Skill] = Field(
        default_factory=list, description="Canonical skills mapped to standardized registries"
    )
    traditional_skills: List[str] = Field(
        default_factory=list, description="Indigenous, generational, or craft competencies"
    )
    interests: List[str] = Field(
        default_factory=list, description="Expressed interest areas or hobbies"
    )
    aspirations: List[str] = Field(
        default_factory=list, description="Desired future occupations or economic goals"
    )
    employment_preference: EmploymentPreference = Field(
        default=EmploymentPreference.UNKNOWN,
        description="Wage employment vs. micro-enterprise/self-employment preference",
    )
    willingness_to_travel: Optional[bool] = Field(
        default=None, description="Willingness to commute or relocate for employment/training"
    )
    max_travel_distance_km: Optional[float] = Field(
        default=None, ge=0.0, description="Max acceptable commute distance in kilometers"
    )
    physical_constraints: Optional[str] = Field(
        default=None, description="Accessibility or physical limitations if disclosed"
    )
    preferred_language: str = Field(
        default="hi", description="Primary spoken language (ISO code, e.g. hi, ta, te, bn)"
    )
    profile_completion_pct: Optional[float] = Field(
        default=None, ge=0.0, le=100.0, description="Profile data completeness percentage"
    )
    profile_source: ProfileSource = Field(
        default=ProfileSource.UNKNOWN, description="Intake channel for this profile"
    )
    work_history: List[WorkHistoryEntry] = Field(
        default_factory=list, description="Historical employment/work background"
    )
    evidence: List[SourceEvidence] = Field(
        default_factory=list, description="Verification documents or conversational records"
    )

    @field_validator("preferred_language")
    @classmethod
    def validate_preferred_language(cls, value: str) -> str:
        return normalize_language_code(value, allow_unknown=True)


# API Request/Response Schemas
class ProfileExtractRequest(BaseModel):
    raw_text: str = Field(..., description="Unstructured conversational transcript or audio transcript")
    language: str = Field(default="hi", description="ISO 639-1 language code")
    source: ProfileSource = Field(
        default=ProfileSource.VOICE_INTERVIEW, description="Origin of the input"
    )

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("raw_text must not be empty")
        return value

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language_code(value)


class ProfileExtractionMetadata(BaseModel):
    """Traceability metadata for a validated extraction response."""

    provider: str
    model: str
    model_version: str
    input_language: str


class ProfileExtractResponse(BaseModel):
    extracted_profile: BeneficiaryProfile
    original_text: str = Field(..., description="Original user input preserved verbatim")
    raw_skills_detected: List[RawSkill] = Field(
        default_factory=list, description="Raw dialect and conversational skill phrases detected"
    )
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    missing_critical_fields: List[str] = Field(default_factory=list)
    extraction_metadata: Optional[ProfileExtractionMetadata] = None
    status: str = Field(default="completed")


class ProfileValidateRequest(BaseModel):
    profile: BeneficiaryProfile
    scheme: str = Field(default="PM-AJAY", description="Target government scheme to evaluate against")


class ProfileValidateResponse(BaseModel):
    eligibility_result: EligibilityResult
    recommended_nsqf_levels: List[int] = Field(default_factory=list)
    status: str = Field(default="pending_ai_implementation")
