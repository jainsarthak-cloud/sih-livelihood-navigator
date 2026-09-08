"""Phase 7 ASR tests using a mocked provider and tiny in-memory audio."""

import asyncio
import base64

import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderResponseException, ValidationException
from app.schemas.speech import SpeechTranscribeRequest
from app.services.speech.providers import ASRResult, BaseASRProvider
from app.services.speech.transcriber import SpeechTranscriptionService


WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32
WAV_BASE64 = base64.b64encode(WAV_BYTES).decode("ascii")


class FakeASR(BaseASRProvider):
    provider_name = "fake-asr"
    model_name = "indic-test-model"

    def __init__(self, result=None, error=None):
        self.result = result or ASRResult(transcript="")
        self.error = error
        self.calls = []

    async def transcribe(self, audio_bytes, audio_format, language_hint):
        self.calls.append((audio_bytes, audio_format, language_hint))
        if self.error:
            raise self.error
        return self.result


def request(**overrides):
    values = {"audio_content_base64": WAV_BASE64, "audio_format": "wav", "language_code": "hi"}
    values.update(overrides)
    return SpeechTranscribeRequest(**values)


def test_valid_transcription_returns_profile_extraction_ready_metadata():
    provider = FakeASR(ASRResult(transcript="मैं सिलाई करती हूँ", detected_language="hi", confidence=0.88, duration_seconds=1.2))
    response = asyncio.run(SpeechTranscriptionService(provider).transcribe(request()))

    assert response.transcript == "मैं सिलाई करती हूँ"
    assert response.detected_language == "hi"
    assert response.confidence == 0.88
    assert response.processing_metadata.provider == "fake-asr"
    assert response.processing_metadata.selected_language == "hi"
    assert response.status == "completed"


def test_invalid_audio_content_and_declared_type_are_rejected_before_provider():
    provider = FakeASR()
    service = SpeechTranscriptionService(provider)

    with pytest.raises(ValidationException):
        asyncio.run(service.transcribe(request(audio_content_base64=base64.b64encode(b"not wav").decode())))
    with pytest.raises(ValidationException):
        asyncio.run(service.transcribe(request(audio_content_base64="%%%")))
    assert provider.calls == []


def test_oversized_audio_is_rejected_before_provider():
    provider = FakeASR()
    service = SpeechTranscriptionService(provider, Settings(ASR_MAX_AUDIO_BYTES=len(WAV_BYTES) - 1))

    with pytest.raises(ValidationException):
        asyncio.run(service.transcribe(request()))
    assert provider.calls == []


def test_provider_failure_and_empty_transcript_are_handled_cleanly():
    failing = SpeechTranscriptionService(FakeASR(error=ProviderResponseException("Fake ASR")))
    with pytest.raises(ProviderResponseException):
        asyncio.run(failing.transcribe(request()))

    empty = asyncio.run(SpeechTranscriptionService(FakeASR()).transcribe(request()))
    assert empty.transcript == ""
    assert empty.status == "no_speech_detected"


def test_selected_language_is_preserved_when_provider_does_not_detect_one():
    response = asyncio.run(SpeechTranscriptionService(FakeASR(ASRResult(transcript="hello"))).transcribe(request(language_code="en")))

    assert response.detected_language == "en"
    assert response.processing_metadata.selected_language == "en"


def test_request_rejects_unsupported_formats_and_remote_urls():
    with pytest.raises(ValueError):
        request(audio_format="txt")
    with pytest.raises(ValueError):
        request(audio_url="https://untrusted.example/audio.wav")
