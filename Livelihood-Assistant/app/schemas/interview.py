"""State-light conversational livelihood interview contracts."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.language import normalize_language_code
from app.schemas.profile import BeneficiaryProfile


class InterviewSlot(str, Enum):
    AGE = "age"
    EDUCATION = "education"
    LOCATION = "location"
    CURRENT_OCCUPATION = "current_occupation"
    SKILLS = "skills"
    INTERESTS = "interests"
    ASPIRATIONS = "aspirations"
    EMPLOYMENT_PREFERENCE = "employment_preference"
    MOBILITY = "mobility"
    CONSTRAINTS = "constraints"


class InterviewQuestion(BaseModel):
    """Frontend-friendly question payload; text is localized when available."""

    slot: InterviewSlot
    text: str
    language: str


class InterviewTurnRequest(BaseModel):
    """One user turn plus client-held, state-light interview state."""

    user_text: str = Field(..., min_length=1, max_length=10000)
    language: str = Field(default="hi", min_length=1, max_length=16)
    session_id: Optional[str] = Field(default=None, max_length=128)
    profile: BeneficiaryProfile = Field(default_factory=BeneficiaryProfile)
    unknown_slots: List[InterviewSlot] = Field(
        default_factory=list,
        description="Slots the beneficiary explicitly declined or reported as unknown.",
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language_code(value)


class InterviewTurnResponse(BaseModel):
    session_id: Optional[str] = None
    profile: BeneficiaryProfile
    missing_slots: List[InterviewSlot] = Field(default_factory=list)
    unknown_slots: List[InterviewSlot] = Field(default_factory=list)
    next_question: Optional[InterviewQuestion] = None
    is_complete: bool = False
    status: str = "in_progress"
