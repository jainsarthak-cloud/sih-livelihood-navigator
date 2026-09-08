"""Safe audio validation and provider-neutral speech transcription."""

import base64
import binascii
from abc import ABC, abstractmethod

from app.core.config import Settings, settings
from app.core.exceptions import ProviderConfigurationException, ProviderResponseException, ValidationException
from app.schemas.language import normalize_detected_language
from app.schemas.speech import SpeechProcessingMetadata, SpeechTranscribeRequest, SpeechTranscribeResponse
from app.services.speech.providers import BaseASRProvider


class BaseSpeechTranscriptionService(ABC):
    """Contract for turning an accepted audio payload into observed text."""

    @abstractmethod
    async def transcribe(self, request: SpeechTranscribeRequest) -> SpeechTranscribeResponse:
        """Transcribe audio into text."""


class SpeechTranscriptionService(BaseSpeechTranscriptionService):
    """Validates base64 audio before delegating recognition to an ASR provider."""

    def __init__(self, provider: BaseASRProvider, config: Settings = settings):
        self._provider = provider
        self._max_bytes = config.ASR_MAX_AUDIO_BYTES

    @staticmethod
    def _matches_format(audio_bytes: bytes, audio_format: str) -> bool:
        if audio_format == "wav":
            return len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"
        if audio_format == "mp3":
            return audio_bytes.startswith(b"ID3") or (len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF and audio_bytes[1] & 0xE0 == 0xE0)
        if audio_format == "ogg":
            return audio_bytes.startswith(b"OggS")
        if audio_format == "webm":
            return audio_bytes.startswith(b"\x1a\x45\xdf\xa3")
        return False

    def _decode_audio(self, request: SpeechTranscribeRequest) -> bytes:
        try:
            audio_bytes = base64.b64decode(request.audio_content_base64 or "", validate=True)
        except (binascii.Error, ValueError):
            raise ValidationException("audio_content_base64 is not valid base64 audio") from None
        if not audio_bytes:
            raise ValidationException("Audio payload is empty")
        if len(audio_bytes) > self._max_bytes:
            raise ValidationException("Audio payload exceeds the configured size limit")
        if not self._matches_format(audio_bytes, request.audio_format):
            raise ValidationException("Audio bytes do not match the declared audio_format")
        return audio_bytes

    async def transcribe(self, request: SpeechTranscribeRequest) -> SpeechTranscribeResponse:
        audio_bytes = self._decode_audio(request)
        try:
            result = await self._provider.transcribe(audio_bytes, request.audio_format, request.language_code)
        except (ProviderConfigurationException, ProviderResponseException):
            raise
        except Exception:
            raise ProviderResponseException(self._provider.provider_name) from None
        if not isinstance(result.transcript, str):
            raise ProviderResponseException(self._provider.provider_name)
        transcript = result.transcript.strip()
        # A selected language is useful fallback metadata only when speech was
        # actually returned. Empty recognition output must not claim detection.
        detected_language = (
            normalize_detected_language(result.detected_language)
            if result.detected_language is not None and transcript
            else (request.language_code if transcript else None)
        )
        return SpeechTranscribeResponse(
            transcript=transcript,
            detected_language=detected_language,
            confidence=result.confidence,
            duration_seconds=result.duration_seconds,
            processing_metadata=SpeechProcessingMetadata(
                provider=self._provider.provider_name,
                model=self._provider.model_name,
                audio_format=request.audio_format,
                input_bytes=len(audio_bytes),
                selected_language=request.language_code,
            ),
            status="completed" if transcript else "no_speech_detected",
        )
