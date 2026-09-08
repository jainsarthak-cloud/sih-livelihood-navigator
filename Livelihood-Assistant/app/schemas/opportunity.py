"""Canonical opportunity domain models supporting wage and self-employment."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.common import GeographicLocation, SourceEvidence, VerificationStatus
from app.schemas.eligibility import EligibilityResult
from app.schemas.ontology import DataClassification
from app.schemas.profile import BeneficiaryProfile
from app.schemas.skill import SkillNormalizationResult


class OpportunityType(str, Enum):
    WAGE_EMPLOYMENT = "wage_employment"
    SELF_EMPLOYMENT = "self_employment"
    APPRENTICESHIP = "apprenticeship"
    SCHEME_SUBSIDY = "scheme_subsidy"
    TRAINING_PROGRAM = "training_program"
    OTHER = "other"


class OpportunityLifecycle(str, Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    ACTIVE = "active"
    EXPIRED = "expired"
    FILLED = "filled"


class Opportunity(BaseModel):
    """Canonical opportunity record for wage jobs, apprenticeships, and PM-AJAY micro-enterprises."""

    opportunity_id: str = Field(..., description="Unique opportunity identifier")
    title: str = Field(..., description="Official title or description of role/grant")
    opportunity_type: OpportunityType = Field(
        ..., description="Wage employment vs. self-employment grant/pathway"
    )
    sector: str = Field(..., description="Industry domain or economic sector")
    description: Optional[str] = Field(
        default=None, description="Detailed job description or scheme terms"
    )
    required_skills: List[str] = Field(
        default_factory=list, description="Skills required for this opportunity"
    )
    location: GeographicLocation = Field(
        ..., description="Geographic location including district and optional coordinates"
    )
    employer_or_provider: Optional[str] = Field(
        default=None, description="Hiring organization, implementing agency, or DIC center"
    )
    source: Optional[SourceEvidence] = Field(
        default=None, description="Primary intake evidence reference"
    )
    collected_at: datetime = Field(
        ..., description="Timezone-aware intake/creation timestamp"
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="Verification state of the opportunity posting",
    )
    last_verified_at: Optional[datetime] = Field(
        default=None, description="Timezone-aware timestamp of most recent verification check"
    )
    lifecycle_status: OpportunityLifecycle = Field(
        default=OpportunityLifecycle.REPORTED,
        description="Current lifecycle state (REPORTED -> VERIFIED -> ACTIVE -> EXPIRED/FILLED)",
    )
    financial_assistance: Optional[str] = Field(
        default=None, description="Salary, stipend, or PM-AJAY capital subsidy if applicable"
    )
    evidence: List[SourceEvidence] = Field(
        default_factory=list, description="Supporting documents, gazette notifications, or job ads"
    )
    is_synthetic: bool = Field(default=False, description="Explicit synthetic/demo marker")
    data_classification: Optional[DataClassification] = Field(default=None)

    @field_validator("collected_at", "last_verified_at")
    @classmethod
    def validate_tz(cls, dt: Optional[datetime]) -> Optional[datetime]:
        if dt is not None and (dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None):
            raise ValueError("Opportunity timestamps must be timezone-aware (e.g. UTC).")
        return dt


class OpportunityDraft(BaseModel):
    """Structured external record awaiting deterministic ontology normalization."""

    opportunity_id: str
    title: str
    opportunity_type: OpportunityType
    sector: str
    location: GeographicLocation
    collected_at: datetime
    required_skills_raw: List[str] = Field(default_factory=list)
    occupation_raw: Optional[str] = None
    description: Optional[str] = None
    employer_or_provider: Optional[str] = None
    source: Optional[SourceEvidence] = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    last_verified_at: Optional[datetime] = None
    lifecycle_status: OpportunityLifecycle = OpportunityLifecycle.REPORTED
    financial_assistance: Optional[str] = None
    evidence: List[SourceEvidence] = Field(default_factory=list)
    is_synthetic: bool = False
    data_classification: Optional[DataClassification] = None

    @field_validator("collected_at", "last_verified_at")
    @classmethod
    def validate_tz(cls, dt: Optional[datetime]) -> Optional[datetime]:
        if dt is not None and (dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None):
            raise ValueError("Opportunity timestamps must be timezone-aware (e.g. UTC).")
        return dt


class OpportunityParseRequest(BaseModel):
    raw_content: Optional[str] = Field(default=None, description="Raw source text preserved for audit; not interpreted without a structured record")
    record: Optional[OpportunityDraft] = Field(default=None, description="Structured record supplied by a trusted ingestion adapter")
    scheme_context: Optional[str] = Field(default="PM-AJAY", description="Specific scheme context")

    @model_validator(mode="after")
    def require_input(self) -> "OpportunityParseRequest":
        if not self.raw_content and self.record is None:
            raise ValueError("raw_content or record is required")
        return self


class OpportunityNormalizationResult(BaseModel):
    opportunity: Opportunity
    raw_occupation: Optional[str] = None
    canonical_occupation_id: Optional[str] = None
    canonical_occupation_name: Optional[str] = None
    raw_required_skills: List[str] = Field(default_factory=list)
    skill_normalizations: List[SkillNormalizationResult] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class OpportunityParseResponse(BaseModel):
    parsed_opportunities: List[Opportunity] = Field(default_factory=list)
    normalization_results: List[OpportunityNormalizationResult] = Field(default_factory=list)
    total_parsed: int = 0
    limitations: List[str] = Field(default_factory=list)
    status: str = Field(default="completed")


class OpportunityMatchRequest(BaseModel):
    profile: BeneficiaryProfile
    occupation_id: Optional[str] = None
    pathway_type: Optional[str] = Field(default=None, description="Optional existing pathway type filter")
    eligibility_result: Optional[EligibilityResult] = None
    include_reported: bool = False


class OpportunityMatch(BaseModel):
    opportunity: Opportunity
    canonical_occupation_id: Optional[str] = None
    matched_skill_ids: List[str] = Field(default_factory=list)
    missing_skill_ids: List[str] = Field(default_factory=list)
    location_match: Optional[bool] = None
    limitations: List[str] = Field(default_factory=list)
    evidence: List[SourceEvidence] = Field(default_factory=list)


class OpportunityMatchResponse(BaseModel):
    matches: List[OpportunityMatch] = Field(default_factory=list)
    total_matches: int = 0
    limitations: List[str] = Field(default_factory=list)
    status: str = "completed"
