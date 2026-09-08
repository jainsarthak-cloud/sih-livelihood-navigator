"""Structured Phase 11 deterministic livelihood assessment contracts."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import SourceEvidence
from app.schemas.eligibility import EligibilityResult
from app.schemas.market import MarketDemandResponse
from app.schemas.opportunity import OpportunityMatch
from app.schemas.profile import BeneficiaryProfile
from app.schemas.recommendation import PathwayType, Recommendation
from app.schemas.roadmap import Roadmap


class LivelihoodAssessRequest(BaseModel):
    """Structured entry point; ASR and LLM extraction are deliberately optional upstream steps."""

    profile: BeneficiaryProfile
    target_sector: Optional[str] = Field(default=None, max_length=200)
    preferred_pathway: Optional[PathwayType] = None
    eligibility_result: Optional[EligibilityResult] = None
    max_recommendations: int = Field(default=3, ge=1, le=3)


class LivelihoodPathwayAssessment(BaseModel):
    recommendation: Recommendation
    opportunity_matches: List[OpportunityMatch] = Field(default_factory=list)
    roadmap: Optional[Roadmap] = None
    limitations: List[str] = Field(default_factory=list)


class LivelihoodAssessmentMetadata(BaseModel):
    assessment_version: str
    recommendation_model_version: str
    deterministic: bool = True
    services: List[str] = Field(default_factory=list)


class LivelihoodAssessResponse(BaseModel):
    profile: BeneficiaryProfile
    pathways: List[LivelihoodPathwayAssessment] = Field(default_factory=list)
    local_opportunity_evidence: List[OpportunityMatch] = Field(default_factory=list)
    market_observation: Optional[MarketDemandResponse] = None
    evidence: List[SourceEvidence] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    metadata: LivelihoodAssessmentMetadata
    status: str = "completed"
