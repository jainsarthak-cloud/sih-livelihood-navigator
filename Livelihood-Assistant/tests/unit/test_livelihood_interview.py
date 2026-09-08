"""Focused Phase 8 state-light interview tests with mocked Phase 6 extraction."""

import asyncio

import pytest

from app.schemas.common import EducationLevel, EmploymentPreference, GeographicLocation, ProfileSource
from app.schemas.interview import InterviewSlot, InterviewTurnRequest
from app.schemas.profile import BeneficiaryProfile, ProfileExtractResponse
from app.schemas.skill import Skill
from app.services.ai.extractor import BaseProfileExtractionService
from app.services.interview.service import LivelihoodInterviewService


class FakeExtractionService(BaseProfileExtractionService):
    def __init__(self, profiles):
        self.profiles = iter(profiles)
        self.requests = []

    async def extract_profile(self, request):
        self.requests.append(request)
        return ProfileExtractResponse(extracted_profile=next(self.profiles), original_text=request.raw_text)

    async def validate_profile(self, request):  # pragma: no cover - not used by interviews
        raise NotImplementedError


def turn(service, **values):
    return asyncio.run(service.process_turn(InterviewTurnRequest(user_text="user reply", **values)))


def test_first_turn_asks_highest_priority_missing_slot_in_requested_language():
    extractor = FakeExtractionService([BeneficiaryProfile(profile_source=ProfileSource.VOICE_INTERVIEW)])
    response = turn(LivelihoodInterviewService(extractor), language="hi", session_id="session-1")

    assert response.session_id == "session-1"
    assert response.next_question.slot == InterviewSlot.AGE
    assert response.next_question.language == "hi"
    assert response.next_question.text == "आपकी उम्र कितनी है?"
    assert extractor.requests[0].raw_text == "user reply"


def test_progressive_profile_completion_merges_only_extracted_facts():
    extractor = FakeExtractionService([
        BeneficiaryProfile(age=28, profile_source=ProfileSource.VOICE_INTERVIEW),
        BeneficiaryProfile(education_level=EducationLevel.PRIMARY, profile_source=ProfileSource.VOICE_INTERVIEW),
    ])
    service = LivelihoodInterviewService(extractor)
    first = turn(service, language="en")
    second = turn(service, language="en", profile=first.profile)

    assert first.profile.age == 28
    assert first.next_question.slot == InterviewSlot.EDUCATION
    assert second.profile.age == 28
    assert second.profile.education_level == EducationLevel.PRIMARY
    assert second.next_question.slot == InterviewSlot.LOCATION
    assert second.profile.profile_completion_pct > first.profile.profile_completion_pct


def test_missing_detection_and_skill_normalization_output_are_preserved():
    normalized_skill = Skill(skill_id="SKL-SYN-001", name="Basic Garment Stitching")
    extracted = BeneficiaryProfile(
        normalized_skills=[normalized_skill], traditional_skills=["silai"],
        profile_source=ProfileSource.VOICE_INTERVIEW,
    )
    response = turn(LivelihoodInterviewService(FakeExtractionService([extracted])))

    assert response.profile.normalized_skills[0].skill_id == "SKL-SYN-001"
    assert response.profile.traditional_skills == ["silai"]
    assert InterviewSlot.SKILLS not in response.missing_slots


def test_unknown_extraction_does_not_erase_existing_profile_and_unknown_slots_stop_reasking():
    existing = BeneficiaryProfile(age=30, education_level=EducationLevel.PRIMARY)
    extracted_unknown = BeneficiaryProfile(profile_source=ProfileSource.VOICE_INTERVIEW)
    response = turn(
        LivelihoodInterviewService(FakeExtractionService([extracted_unknown])),
        profile=existing,
        unknown_slots=[InterviewSlot.LOCATION, InterviewSlot.CURRENT_OCCUPATION, InterviewSlot.SKILLS,
                       InterviewSlot.INTERESTS, InterviewSlot.ASPIRATIONS, InterviewSlot.EMPLOYMENT_PREFERENCE,
                       InterviewSlot.MOBILITY, InterviewSlot.CONSTRAINTS],
    )

    assert response.profile.age == 30
    assert response.profile.education_level == EducationLevel.PRIMARY
    assert response.is_complete is True
    assert response.next_question is None
    assert InterviewSlot.LOCATION in response.missing_slots


def test_complete_profile_has_no_next_question_and_completion_is_deterministic():
    complete = BeneficiaryProfile(
        age=29, education_level=EducationLevel.ITI,
        location=GeographicLocation(state="Demo State", district="Demo District"),
        current_occupation="tailor", normalized_skills=[Skill(skill_id="SKL-SYN-001", name="Basic Garment Stitching")],
        interests=["apparel"], aspirations=["tailor"], employment_preference=EmploymentPreference.WAGE_EMPLOYMENT,
        willingness_to_travel=False, physical_constraints="none reported",
    )
    extractor = FakeExtractionService([BeneficiaryProfile(), BeneficiaryProfile()])
    service = LivelihoodInterviewService(extractor)
    first = turn(service, profile=complete, language="en")
    second = turn(service, profile=complete, language="en")

    assert first.is_complete is True
    assert first.next_question is None
    assert first.status == "completed"
    assert first.model_dump() == second.model_dump()


def test_malformed_turn_input_is_rejected_by_schema():
    with pytest.raises(ValueError):
        InterviewTurnRequest(user_text="")
