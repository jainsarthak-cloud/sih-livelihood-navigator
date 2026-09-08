"""Replaceable ASR provider adapters.

The Whisper implementation only opens a locally provisioned model path; it
never downloads a model or speech dataset as a side effect of a request.
"""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import Optional

from app.core.config import Settings, settings
from app.core.exceptions import ProviderConfigurationException, ProviderResponseException


@dataclass(frozen=True)
class ASRResult:
    transcript: str
    detected_language: Optional[str] = None
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None


class BaseASRProvider(ABC):
    """Vendor-neutral speech recognition boundary."""

    provider_name: str = "unknown"
    model_name: str = "unknown"

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, audio_format: str, language_hint: Optional[str]) -> ASRResult:
        """Return only recognition output observed from the supplied audio."""


class WhisperASRProvider(BaseASRProvider):
    """Local multilingual Faster-Whisper adapter for Hindi, English, and Indic languages."""

    provider_name = "whisper"

    def __init__(self, config: Settings = settings):
        self._model_path = config.ASR_MODEL_PATH
        self.model_name = config.ASR_MODEL_VERSION

    async def transcribe(self, audio_bytes: bytes, audio_format: str, language_hint: Optional[str]) -> ASRResult:
        if not self._model_path or not Path(self._model_path).exists():
            raise ProviderConfigurationException("Whisper ASR")
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes, audio_format, language_hint)

    def _transcribe_sync(self, audio_bytes: bytes, audio_format: str, language_hint: Optional[str]) -> ASRResult:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ProviderConfigurationException("Whisper ASR") from None
        suffix = f".{audio_format}"
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
                audio_file.write(audio_bytes)
                temp_path = audio_file.name
            # A path is required so Faster-Whisper/FFmpeg can decode all allowed formats.
            model = WhisperModel(self._model_path)
            segments, info = model.transcribe(temp_path, language=language_hint or None)
            transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
            return ASRResult(
                transcript=transcript,
                detected_language=getattr(info, "language", None),
                duration_seconds=getattr(info, "duration", None),
            )
        except ProviderConfigurationException:
            raise
        except Exception:
            raise ProviderResponseException("Whisper ASR") from None
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
