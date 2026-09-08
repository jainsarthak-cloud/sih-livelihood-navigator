"""Regional and district-level skill market demand schemas."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SourceEvidence


class DemandEvidenceStatus(str, Enum):
    OBSERVED = "observed"
    UNKNOWN = "unknown"


class SectorDemand(BaseModel):
    sector_name: str
    demand_level: str = Field(default="unknown", description="Always unknown: counts are observations, not a demand rating")
    top_in_demand_roles: List[str] = Field(default_factory=list)
    average_monthly_wage: Optional[str] = None
    evidence_status: DemandEvidenceStatus = DemandEvidenceStatus.UNKNOWN
    active_opportunity_count: int = Field(default=0, ge=0)
    verified_active_opportunity_count: int = Field(default=0, ge=0)
    observed_skill_ids: List[str] = Field(default_factory=list)
    evidence: List[SourceEvidence] = Field(default_factory=list)
    scope_note: str = "No opportunity observations available for the requested location."


class MarketDemandRequest(BaseModel):
    state: str = Field(..., description="State name (e.g., Uttar Pradesh, Bihar, Maharashtra)")
    district: str = Field(..., description="District name")
    sector_filter: Optional[str] = None


class MarketDemandResponse(BaseModel):
    state: str
    district: str
    top_sectors: List[SectorDemand] = Field(default_factory=list)
    growth_trends: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    evidence: List[SourceEvidence] = Field(default_factory=list)
    status: str = Field(default="completed")
