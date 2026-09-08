"""Canonical career roadmap and milestone progression domain models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.common import SourceEvidence
from app.schemas.profile import BeneficiaryProfile
from app.schemas.recommendation import PathwayType, Recommendation
from app.schemas.skill import SkillGap


class StepType(str, Enum):
    TRAINING = "training"
    CERTIFICATION = "certification"
    JOB_APPLICATION = "job_application"
    SCHEME_APPLICATION = "scheme_application"
    DOCUMENTATION = "documentation"
    MENTORSHIP = "mentorship"
    VERIFICATION = "verification"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class RoadmapStep(BaseModel):
    """An individual actionable step in a beneficiary's livelihood roadmap."""

    step_id: str = Field(..., description="Unique step identifier")
    step_number: int = Field(..., ge=1, description="Sequential order in progression plan")
    title: str = Field(..., description="Actionable title of milestone")
    description: str = Field(..., description="Step details, instructions, and outcomes")
    step_type: StepType = Field(..., description="Category of action required")
    status: StepStatus = Field(
        default=StepStatus.PENDING, description="Current progress status of step"
    )
    estimated_duration_weeks: Optional[int] = Field(
        default=None, ge=1, description="Estimated time in weeks when known"
    )
    course_references: List[str] = Field(
        default_factory=list, description="Associated NSQF courses/training modules"
    )
    opportunity_references: List[str] = Field(
        default_factory=list, description="Target job, apprenticeship, or scheme opportunities"
    )
    prerequisites: List[str] = Field(
        default_factory=list, description="Step IDs or requirements that must precede this step"
    )
    evidence: List[SourceEvidence] = Field(
        default_factory=list, description="Regulatory guidelines or syllabus references"
    )


class Roadmap(BaseModel):
    """Canonical milestone-driven career progression roadmap towards target NSQF role/livelihood."""

    roadmap_id: str = Field(..., description="Unique roadmap identifier")
    beneficiary_id: Optional[str] = Field(
        default=None, description="Associated beneficiary or candidate ID"
    )
    target_occupation_id: Optional[str] = Field(
        default=None, description="Target occupation or qualification pack"
    )
    target_pathway: PathwayType = Field(
        ..., description="Recommended pathway: wage employment, micro-enterprise, etc."
    )
    current_state_summary: Optional[str] = Field(
        default=None, description="Summary baseline of beneficiary's current capabilities"
    )
    skill_gaps: List[SkillGap] = Field(
        default_factory=list, description="Competency gaps targeted by this roadmap"
    )
    matched_skills: List[str] = Field(
        default_factory=list, description="Canonical skill IDs already matching the target pathway"
    )
    limitations: List[str] = Field(
        default_factory=list, description="Explicitly recorded unavailable or unknown inputs"
    )
    steps: List[RoadmapStep] = Field(
        default_factory=list, description="Ordered milestone action steps"
    )
    total_estimated_duration_weeks: Optional[int] = Field(
        default=None, ge=1, description="Cumulative projected timeframe in weeks when known"
    )
    evidence: List[SourceEvidence] = Field(
        default_factory=list, description="Authoritative program references supporting roadmap"
    )


class RoadmapRequest(BaseModel):
    profile: BeneficiaryProfile
    target_occupation_id: Optional[str] = Field(
        default=None, description="Identifier of target occupation when no selected recommendation is supplied"
    )
    recommendation: Optional[Recommendation] = Field(
        default=None, description="Selected canonical recommendation from Phase 5"
    )
    target_pathway: Optional[PathwayType] = Field(
        default=PathwayType.SKILL_TRAINING, description="Preferred pathway"
    )
    timeframe_months: Optional[int] = Field(
        default=6, ge=1, le=36, description="Desired completion timeframe in months"
    )

    @model_validator(mode="after")
    def require_pathway_target(self) -> "RoadmapRequest":
        if self.target_occupation_id is None and self.recommendation is None:
            raise ValueError("target_occupation_id or recommendation is required")
        return self


class RoadmapResponse(BaseModel):
    roadmap: Optional[Roadmap] = None
    status: str = Field(default="completed")
