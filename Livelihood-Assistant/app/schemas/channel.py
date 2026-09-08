"""Channel-agnostic external interaction contracts.

These contracts intentionally contain no WhatsApp, phone-number, webhook, or
credential semantics. External identifiers are opaque caller references.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.interview import InterviewSlot, InterviewTurnResponse
from app.schemas.language import normalize_language_code
from app.schemas.livelihood import LivelihoodAssessResponse
from app.schemas.profile import BeneficiaryProfile
from app.schemas.speech import SpeechProcessingMetadata


class ChannelAudioInput(BaseModel):
    """Audio supplied by a channel; remote references are deliberately refused."""

    audio_content_base64: Optional[str] = Field(default=None, min_length=1)
    audio_format: str = Field(default="wav")
    audio_reference: Optional[str] = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_safe_audio_source(self) -> "ChannelAudioInput":
        if self.audio_reference:
            raise ValueError("audio_reference is not supported; provide audio_content_base64")
        if not self.audio_content_base64:
            raise ValueError("audio_content_base64 is required")
        return self


class ChannelInteractRequest(BaseModel):
    """One externally-originated text or audio interaction, normalized at the edge."""

    channel: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    external_user_reference: str = Field(..., min_length=1, max_length=256)
    session_id: Optional[str] = Field(default=None, max_length=128)
    language: str = Field(default="hi")
    text: Optional[str] = Field(default=None, max_length=10000)
    audio: Optional[ChannelAudioInput] = None
    profile: BeneficiaryProfile = Field(default_factory=BeneficiaryProfile)
    unknown_slots: list[InterviewSlot] = Field(default_factory=list)
    session_metadata: dict[str, Any] = Field(default_factory=dict, max_length=32)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language_code(value)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("text must not be empty")
        return value

    @model_validator(mode="after")
    def validate_single_input(self) -> "ChannelInteractRequest":
        if (self.text is None) == (self.audio is None):
            raise ValueError("provide exactly one of text or audio")
        return self


class ChannelInteractResponse(BaseModel):
    """Existing service output wrapped with minimal external-channel metadata."""

    channel: str
    external_user_reference: str
    session_id: Optional[str] = None
    language: str
    transcript: Optional[str] = None
    speech_metadata: Optional[SpeechProcessingMetadata] = None
    interview: Optional[InterviewTurnResponse] = None
    assessment: Optional[LivelihoodAssessResponse] = None
    status: str
