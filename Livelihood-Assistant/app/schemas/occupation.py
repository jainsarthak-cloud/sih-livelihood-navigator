"""Canonical occupation domain models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SourceEvidence


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    SEASONAL = "seasonal"
    SELF_EMPLOYED = "self_employed"
    APPRENTICESHIP = "apprenticeship"
    UNKNOWN = "unknown"


class Occupation(BaseModel):
    """Canonical occupation entity aligned with standard classifications (e.g. NCO/NOS)."""

    occupation_id: str = Field(..., description="Standardized occupation identifier")
    name: str = Field(..., description="Canonical title of the occupation")
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative titles, regional names, or industry synonyms",
    )
    sector: str = Field(..., description="Economic sector or Industry Skill Council")
    description: Optional[str] = Field(
        default=None, description="Overview of job responsibilities and working conditions"
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="List of required canonical skill IDs or names",
    )
    nsqf_qualification_ids: List[str] = Field(
        default_factory=list,
        description="Associated NSQF Qualification Pack (QP) references",
    )
    employment_type: EmploymentType = Field(
        default=EmploymentType.UNKNOWN,
        description="Standard engagement/employment arrangement",
    )
    source_metadata: Optional[SourceEvidence] = Field(
        default=None,
        description="Authoritative source or gazette reference documenting this occupation",
    )
