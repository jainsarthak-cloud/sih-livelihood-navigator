"""Speech transcription and voice processing schemas."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.language import normalize_language_code


_SUPPORTED_FORMATS = {"wav", "mp3", "ogg", "webm"}


class SpeechTranscribeRequest(BaseModel):
    audio_content_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded audio byte payload",
    )
    audio_url: Optional[str] = Field(
        default=None,
        description="Public/presigned URL to audio recording",
    )
    language_code: str = Field(
        default="hi",
        description="Source audio language (e.g. hi, ta, te, mr, bn, en)",
    )
    audio_format: str = Field(
        default="wav",
        description="Audio format encoding: wav, mp3, ogg, webm",
    )

    @field_validator("audio_format")
    @classmethod
    def validate_audio_format(cls, value: str) -> str:
        value = value.casefold().strip()
        if value not in _SUPPORTED_FORMATS:
            raise ValueError(f"audio_format must be one of: {', '.join(sorted(_SUPPORTED_FORMATS))}")
        return value

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, value: str) -> str:
        return normalize_language_code(value)

    @model_validator(mode="after")
    def validate_audio_source(self) -> "SpeechTranscribeRequest":
        # Remote URLs are intentionally not fetched: accepting them would add
        # an unbounded SSRF and content-validation surface.
        if not self.audio_content_base64:
            raise ValueError("audio_content_base64 is required")
        if self.audio_url:
            raise ValueError("audio_url is not supported; provide audio_content_base64")
        return self


class SpeechProcessingMetadata(BaseModel):
    provider: str
    model: str
    audio_format: str
    input_bytes: int = Field(ge=0)
    selected_language: Optional[str] = None


class SpeechTranscribeResponse(BaseModel):
    transcript: str = ""
    detected_language: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    duration_seconds: Optional[float] = None
    processing_metadata: Optional[SpeechProcessingMetadata] = None
    status: str = Field(default="completed")
