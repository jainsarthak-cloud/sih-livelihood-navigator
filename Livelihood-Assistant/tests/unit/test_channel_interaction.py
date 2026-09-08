"""Phase 14 tests for the channel-neutral adapter boundary."""

import asyncio
import base64

import pytest

from app.core.exceptions import ProviderResponseException
from app.schemas.channel import ChannelInteractRequest
from app.schemas.common import ProfileSource
from app.schemas.interview import InterviewTurnResponse
from app.schemas.livelihood import LivelihoodAssessResponse, LivelihoodAssessmentMetadata
from app.schemas.profile import BeneficiaryProfile
from app.schemas.speech import SpeechProcessingMetadata, SpeechTranscribeResponse
from app.services.channel.interaction import ChannelInteractionService
from app.services.interview.service import BaseLivelihoodInterviewService
from app.services.livelihood.assessment import LivelihoodAssessmentService
from app.services.speech.transcriber import BaseSpeechTranscriptionService


WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32
WAV_BASE64 = base64.b64encode(WAV_BYTES).decode("ascii")


class FakeSpeech(BaseSpeechTranscriptionService):
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.requests = []

    async def transcribe(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response


class FakeInterview(BaseLivelihoodInterviewService):
    def __init__(self):
        self.requests = []

    async def process_turn(self, request):
        self.requests.append(request)
        profile = request.profile.model_copy(update={"profile_source": ProfileSource.TEXT_INPUT})
        return InterviewTurnResponse(session_id=request.session_id, profile=profile, status="in_progress")


class FakeAssessment:
    def __init__(self):
        self.requests = []

    async def assess(self, request):
        self.requests.append(request)
        return LivelihoodAssessResponse(
            profile=request.profile, metadata=LivelihoodAssessmentMetadata(
                assessment_version="test", recommendation_model_version="test",
            ), status="incomplete_or_no_pathway",
        )


def request(**overrides):
    values = {
        "channel": "whatsapp_future", "external_user_reference": "opaque-caller-ref",
        "session_id": "session-1", "language": "hi", "text": "मैं सिलाई करती हूँ",
    }
    values.update(overrides)
    return ChannelInteractRequest(**values)


def service(speech_response=None, speech_error=None):
    speech = FakeSpeech(speech_response, speech_error)
    interview = FakeInterview()
    assessment = FakeAssessment()
    return ChannelInteractionService(speech, interview, assessment), speech, interview, assessment


def test_text_request_delegates_to_existing_interview_and_assessment_without_transcript_fabrication():
    adapter, speech, interview, assessment = service()
    response = asyncio.run(adapter.interact(request()))

    assert response.status == "completed"
    assert response.transcript is None
    assert speech.requests == []
    assert interview.requests[0].user_text == "मैं सिलाई करती हूँ"
    assert interview.requests[0].language == "hi"
    assert assessment.requests[0].profile == response.interview.profile
    assert response.external_user_reference == "opaque-caller-ref"


def test_audio_request_uses_existing_asr_result_then_returns_structured_response():
    speech_response = SpeechTranscribeResponse(
        transcript="मैं सिलाई करती हूँ", detected_language="hi", status="completed",
        processing_metadata=SpeechProcessingMetadata(provider="fake", model="fake", audio_format="wav", input_bytes=52),
    )
    adapter, speech, interview, assessment = service(speech_response)
    response = asyncio.run(adapter.interact(request(text=None, audio={
        "audio_content_base64": WAV_BASE64, "audio_format": "wav",
    })))

    assert response.status == "completed"
    assert response.transcript == "मैं सिलाई करती हूँ"
    assert speech.requests[0].language_code == "hi"
    assert interview.requests[0].user_text == "मैं सिलाई करती हूँ"
    assert len(assessment.requests) == 1


def test_no_speech_does_not_invent_a_transcript_or_continue_the_pipeline():
    no_speech = SpeechTranscribeResponse(transcript="", status="no_speech_detected")
    adapter, _speech, interview, assessment = service(no_speech)
    response = asyncio.run(adapter.interact(request(text=None, audio={
        "audio_content_base64": WAV_BASE64, "audio_format": "wav",
    })))

    assert response.status == "no_speech_detected"
    assert response.transcript == ""
    assert response.interview is None and response.assessment is None
    assert interview.requests == [] and assessment.requests == []


def test_asr_provider_failure_is_propagated_without_creating_channel_output():
    adapter, _speech, interview, assessment = service(speech_error=ProviderResponseException("fake-asr"))
    with pytest.raises(ProviderResponseException):
        asyncio.run(adapter.interact(request(text=None, audio={
            "audio_content_base64": WAV_BASE64, "audio_format": "wav",
        })))
    assert interview.requests == [] and assessment.requests == []


def test_invalid_and_unsupported_channel_inputs_are_rejected_at_the_contract_boundary():
    with pytest.raises(ValueError, match="unsupported language"):
        request(language="fr")
    with pytest.raises(ValueError, match="exactly one"):
        request(text=None)
    with pytest.raises(ValueError, match="exactly one"):
        request(audio={"audio_content_base64": WAV_BASE64})
    with pytest.raises(ValueError, match="audio_reference is not supported"):
        request(text=None, audio={"audio_reference": "https://untrusted.example/audio"})
