"""Canonical skill and skill-gap domain models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.common import SourceEvidence
from app.schemas.language import normalize_language_code


class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT_SKILL = "soft_skill"
    TRADITIONAL_CRAFT = "traditional_craft"
    AGRICULTURAL = "agricultural"
    SERVICE = "service"
    DIGITAL = "digital"
    OTHER = "other"


class SkillProficiency(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNKNOWN = "unknown"


class SkillSource(str, Enum):
    SELF_REPORTED = "self_reported"
    INFERRED_FROM_WORK = "inferred_from_work"
    ASSESSED = "assessed"
    CERTIFIED = "certified"
    RESUME = "resume"
    UNKNOWN = "unknown"


class GapStatus(str, Enum):
    ACQUIRED = "acquired"
    PARTIALLY_ACQUIRED = "partially_acquired"
    MISSING = "missing"
    UNKNOWN = "unknown"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RawSkill(BaseModel):
    """Extracted raw dialect, vernacular phrasing, or conversational skill term."""

    raw_text: str = Field(..., description="Verbatim raw phrase from conversation or document")
    language: Optional[str] = Field(default="hi", description="ISO language code of input phrase")
    extracted_confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Extraction confidence score"
    )
    context: Optional[str] = Field(
        default=None, description="Surrounding contextual sentence or prompt snippet"
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: Optional[str]) -> Optional[str]:
        return normalize_language_code(value, allow_unknown=True) if value is not None else None


class SkillNormalizationStatus(str, Enum):
    """Whether a raw skill was safely resolved to the canonical ontology."""

    MATCHED = "matched"
    UNKNOWN = "unknown"


class SkillNormalizationMethod(str, Enum):
    """Evidence-bearing method used to resolve a raw skill."""

    EXACT_NAME = "exact_name"
    EXACT_ALIAS = "exact_alias"
    PHRASE_NAME = "phrase_name"
    PHRASE_ALIAS = "phrase_alias"
    FUZZY_NAME = "fuzzy_name"
    FUZZY_ALIAS = "fuzzy_alias"
    UNKNOWN = "unknown"


class SkillNormalizationResult(BaseModel):
    """Auditable outcome of mapping a RawSkill to a canonical Skill.

    Canonical fields are deliberately absent for UNKNOWN results.  Consumers
    must not treat an unresolved phrase as a canonical capability.
    """

    raw_skill: RawSkill = Field(..., description="Original input preserved verbatim")
    status: SkillNormalizationStatus = SkillNormalizationStatus.UNKNOWN
    canonical_skill_id: Optional[str] = Field(default=None)
    canonical_skill_name: Optional[str] = Field(default=None)
    matched_input: Optional[str] = Field(
        default=None,
        description="Canonical name or alias that supported the match",
    )
    normalization_method: SkillNormalizationMethod = SkillNormalizationMethod.UNKNOWN
    confidence: float = Field(..., ge=0.0, le=1.0)


class Skill(BaseModel):
    """Canonical normalized skill entity mapped from raw/extracted observations."""

    skill_id: str = Field(..., description="Unique canonical skill identifier")
    name: str = Field(..., description="Standardized canonical skill title")
    aliases: List[str] = Field(
        default_factory=list,
        description="Synonyms, dialect equivalents, or localized translations",
    )
    category: SkillCategory = Field(
        default=SkillCategory.OTHER, description="Skill domain classification"
    )
    proficiency: SkillProficiency = Field(
        default=SkillProficiency.UNKNOWN,
        description="Assessed or self-reported proficiency level",
    )
    source: SkillSource = Field(
        default=SkillSource.UNKNOWN, description="Origin or evidence source of this skill"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence of skill attribution"
    )
    mapped_raw_skills: List[RawSkill] = Field(
        default_factory=list,
        description="Raw phrases that mapped to this canonical skill",
    )
    evidence: List[SourceEvidence] = Field(
        default_factory=list, description="Traceability evidence references"
    )


class SkillGap(BaseModel):
    """Identified delta between candidate's current capability and target requirements."""

    skill_id: str = Field(..., description="Identifier of required skill")
    skill_name: str = Field(..., description="Name of required skill")
    current_proficiency: SkillProficiency = Field(
        default=SkillProficiency.UNKNOWN,
        description="Candidate's current proficiency, or UNKNOWN if unassessed",
    )
    target_proficiency: Optional[SkillProficiency] = Field(
        default=None,
        description="Proficiency required by target occupation/course",
    )
    gap_status: GapStatus = Field(
        default=GapStatus.UNKNOWN,
        description="Current acquisition gap status",
    )
    priority: PriorityLevel = Field(
        default=PriorityLevel.MEDIUM,
        description="Relative importance of bridging this gap",
    )
    evidence: Optional[SourceEvidence] = Field(
        default=None,
        description="Evidence or justification for this gap assessment",
    )
