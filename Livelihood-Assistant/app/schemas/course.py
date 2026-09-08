"""Canonical NSQF course and qualification domain models."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import EducationLevel, SourceEvidence


class NSQFCourse(BaseModel):
    """Canonical NSQF-aligned course or Qualification Pack (QP)."""

    course_id: str = Field(..., description="Unique course identifier")
    course_name: str = Field(..., description="Official title of the course/program")
    qualification_name: str = Field(
        ..., description="Official qualification title under National Qualifications Register"
    )
    qp_code: Optional[str] = Field(
        default=None, description="Qualification Pack code (e.g., ELE/Q0101)"
    )
    nsqf_level: int = Field(
        ..., ge=1, le=10, description="NSQF Level strictly validated from 1 to 10"
    )
    sector: str = Field(..., description="Sector Skill Council / Industry domain")
    job_roles: List[str] = Field(
        default_factory=list,
        description="Associated job roles or target occupations",
    )
    required_education: Optional[EducationLevel] = Field(
        default=None,
        description="Minimum education requirement per official qualification pack",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Prerequisite skills or baseline proficiencies",
    )
    acquired_skills: List[str] = Field(
        default_factory=list,
        description="Core competencies and NOS skills imparted upon completion",
    )
    duration_hours: Optional[int] = Field(
        default=None, ge=1, description="Nominal training duration in hours"
    )
    training_provider: Optional[str] = Field(
        default=None, description="Associated training partner/institute name when known"
    )
    training_center_id: Optional[str] = Field(
        default=None, description="Accredited training center reference when known"
    )
    source_metadata: Optional[SourceEvidence] = Field(
        default=None,
        description="Official NQR or NSDC gazette source reference",
    )
