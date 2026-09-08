"""Phase 13 language and voice safety regression tests."""

import asyncio
import base64

import pytest

from app.core.exceptions import ProviderResponseException
from app.evaluation.runner import build_services
from app.schemas.common import EducationLevel, EmploymentPreference, GeographicLocation, ProfileSource
from app.schemas.interview import InterviewTurnRequest
from app.schemas.opportunity import OpportunityMatchRequest
from app.schemas.profile import BeneficiaryProfile, ProfileExtractRequest, ProfileExtractResponse
from app.schemas.recommendation import RecommendationRequest
from app.schemas.roadmap import RoadmapRequest
from app.schemas.skill import RawSkill
from app.schemas.speech import SpeechTranscribeRequest
from app.services.ai.extractor import BaseProfileExtractionService
from app.services.interview.service import LivelihoodInterviewService
from app.services.speech.providers import ASRResult, BaseASRProvider
from app.services.speech.transcriber import SpeechTranscriptionService


WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32
WAV_BASE64 = base64.b64encode(WAV_BYTES).decode("ascii")


class FakeASR(BaseASRProvider):
    provider_name = "fake-asr"
    model_name = "fake-model"

    def __init__(self, result: ASRResult | None = None, error: Exception | None = None):
        self._result = result or ASRResult(transcript="")
        self._error = error

    async def transcribe(self, audio_bytes, audio_format, language_hint):
        if self._error:
            raise self._error
        return self._result


class FakeExtractionService(BaseProfileExtractionService):
    def __init__(self, profile: BeneficiaryProfile):
        self._profile = profile

    async def extract_profile(self, request):
        return ProfileExtractResponse(extracted_profile=self._profile, original_text=request.raw_text)

    async def validate_profile(self, request):  # pragma: no cover - not used here
        raise NotImplementedError


def test_supported_codes_are_normalized_consistently_and_unsupported_codes_fail_explicitly():
    assert ProfileExtractRequest(raw_text="नमस्ते", language=" HI ").language == "hi"
    assert InterviewTurnRequest(user_text="hello", language="EN").language == "en"
    assert SpeechTranscribeRequest(audio_content_base64=WAV_BASE64, language_code="ta").language_code == "ta"

    with pytest.raises(ValueError, match="unsupported language"):
        ProfileExtractRequest(raw_text="bonjour", language="fr")
    with pytest.raises(ValueError, match="unsupported language"):
        InterviewTurnRequest(user_text="bonjour", language="fr")
    with pytest.raises(ValueError, match="unsupported language"):
        SpeechTranscribeRequest(audio_content_base64=WAV_BASE64, language_code="fr")


def test_empty_audio_no_speech_and_unusable_provider_metadata_are_explicit():
    with pytest.raises(ValueError, match="audio_content_base64 is required"):
        SpeechTranscribeRequest(audio_content_base64="", language_code="hi")

    no_speech = asyncio.run(SpeechTranscriptionService(FakeASR()).transcribe(
        SpeechTranscribeRequest(audio_content_base64=WAV_BASE64, language_code="hi")
    ))
    assert no_speech.transcript == ""
    assert no_speech.detected_language is None
    assert no_speech.status == "no_speech_detected"

    unsupported_detection = asyncio.run(SpeechTranscriptionService(
        FakeASR(ASRResult(transcript="hello", detected_language="fr"))
    ).transcribe(SpeechTranscribeRequest(audio_content_base64=WAV_BASE64, language_code="en")))
    assert unsupported_detection.detected_language == "unknown"


def test_unexpected_asr_provider_failure_is_safe_and_explicit():
    service = SpeechTranscriptionService(FakeASR(error=RuntimeError("provider internals")))
    request = SpeechTranscribeRequest(audio_content_base64=WAV_BASE64, language_code="hi")
    with pytest.raises(ProviderResponseException) as error:
        asyncio.run(service.transcribe(request))
    assert "provider internals" not in str(error.value)


def test_interview_unknown_language_never_erases_known_preferred_language():
    existing = BeneficiaryProfile(preferred_language="en", age=24)
    extracted = BeneficiaryProfile(preferred_language="unknown", profile_source=ProfileSource.VOICE_INTERVIEW)
    response = asyncio.run(LivelihoodInterviewService(FakeExtractionService(extracted)).process_turn(
        InterviewTurnRequest(user_text="मुझे नहीं पता", language="hi", profile=existing)
    ))
    assert response.profile.preferred_language == "en"
    assert response.profile.age == 24


def test_multilingual_structured_profile_flows_through_normalization_and_downstream_services():
    normalizer, recommendation, intelligence, roadmap, _skills = build_services()
    normalized = normalizer.normalize(RawSkill(raw_text="सिलाई", language="hi"))
    # The synthetic ontology supports its Romanized seed alias; unsupported
    # Devanagari input remains UNKNOWN rather than being translated or guessed.
    assert normalized.canonical_skill_id is None

    supported = normalizer.normalize(RawSkill(raw_text="silai", language="hi"))
    canonical = normalizer.get_canonical_skill(supported.canonical_skill_id)
    assert canonical is not None
    profile = BeneficiaryProfile(
        preferred_language="hi", education_level=EducationLevel.PRIMARY,
        employment_preference=EmploymentPreference.WAGE_EMPLOYMENT,
        location=GeographicLocation(state="Demo State", district="Demo District"),
        normalized_skills=[canonical],
    )
    recommendations = asyncio.run(recommendation.get_recommendations(RecommendationRequest(profile=profile)))
    opportunities = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=profile)))
    roadmap_response = asyncio.run(roadmap.generate_roadmap(RoadmapRequest(
        profile=profile, target_occupation_id=recommendations.recommendations[0].occupation_reference,
    )))

    assert recommendations.recommendations[0].occupation_reference == "OCC-SYN-001"
    assert opportunities.status == "completed"
    assert roadmap_response.roadmap is not None
