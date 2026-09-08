"""Canonical eligibility evaluation domain models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SourceEvidence


class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"


class CriterionResult(BaseModel):
    """Evaluation result for an individual scheme or course criterion."""

    criterion_id: str = Field(..., description="Unique criterion code or identifier")
    name: str = Field(..., description="Human-readable criterion title")
    status: EligibilityStatus = Field(
        default=EligibilityStatus.UNKNOWN,
        description="Evaluation status: must support UNKNOWN when information is missing",
    )
    reason: str = Field(
        ...,
        description="Detailed explanation of evaluation outcome, highlighting missing data if unknown",
    )
    evidence: Optional[SourceEvidence] = Field(
        default=None, description="Supporting document or verification reference"
    )


class EligibilityResult(BaseModel):
    """Structured eligibility assessment for a scheme or opportunity."""

    scheme_name: str = Field(
        ..., description="Name of the government scheme or training initiative (e.g. PM-AJAY)"
    )
    status: EligibilityStatus = Field(
        default=EligibilityStatus.UNKNOWN,
        description="Overall eligibility determination; strictly UNKNOWN if any critical criterion is unknown",
    )
    overall_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Eligibility fitness index between 0.0 and 1.0 when computable",
    )
    matched_criteria: List[CriterionResult] = Field(
        default_factory=list, description="Criteria verified as satisfied"
    )
    unmet_criteria: List[CriterionResult] = Field(
        default_factory=list, description="Criteria explicitly violated or failed"
    )
    unknown_criteria: List[CriterionResult] = Field(
        default_factory=list,
        description="Criteria where beneficiary data is insufficient or missing",
    )
    explanation: str = Field(
        ...,
        description="Summary narrative explaining outcome without assuming eligibility for unknowns",
    )
    evidence: List[SourceEvidence] = Field(
        default_factory=list, description="Authoritative program guidelines referenced"
    )
