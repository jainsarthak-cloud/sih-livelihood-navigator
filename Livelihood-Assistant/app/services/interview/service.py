"""Progressive, deterministic interview orchestration over Phase 6 extraction."""

from abc import ABC, abstractmethod

from app.schemas.common import EducationLevel, EmploymentPreference, Gender, ProfileSource
from app.schemas.interview import InterviewQuestion, InterviewSlot, InterviewTurnRequest, InterviewTurnResponse
from app.schemas.profile import BeneficiaryProfile, ProfileExtractRequest
from app.schemas.skill import Skill
from app.services.ai.extractor import BaseProfileExtractionService


_SLOT_ORDER = (
    InterviewSlot.AGE,
    InterviewSlot.EDUCATION,
    InterviewSlot.LOCATION,
    InterviewSlot.CURRENT_OCCUPATION,
    InterviewSlot.SKILLS,
    InterviewSlot.INTERESTS,
    InterviewSlot.ASPIRATIONS,
    InterviewSlot.EMPLOYMENT_PREFERENCE,
    InterviewSlot.MOBILITY,
    InterviewSlot.CONSTRAINTS,
)

_QUESTION_TEXT = {
    "en": {
        InterviewSlot.AGE: "What is your age?",
        InterviewSlot.EDUCATION: "What is the highest level of education or training you completed?",
        InterviewSlot.LOCATION: "Which state and district do you currently live in?",
        InterviewSlot.CURRENT_OCCUPATION: "What work or occupation do you currently do, if any?",
        InterviewSlot.SKILLS: "What skills or traditional work skills do you have?",
        InterviewSlot.INTERESTS: "What kind of work are you interested in?",
        InterviewSlot.ASPIRATIONS: "What work would you like to do in the future?",
        InterviewSlot.EMPLOYMENT_PREFERENCE: "Do you prefer wage work, self-employment, apprenticeship, or home-based work?",
        InterviewSlot.MOBILITY: "Can you travel for work or training? If yes, how far?",
        InterviewSlot.CONSTRAINTS: "Are there any accessibility, health, or work constraints you want us to consider?",
    },
    "hi": {
        InterviewSlot.AGE: "आपकी उम्र कितनी है?",
        InterviewSlot.EDUCATION: "आपने सबसे अधिक कौन-सी पढ़ाई या प्रशिक्षण पूरा किया है?",
        InterviewSlot.LOCATION: "आप अभी किस राज्य और जिले में रहते हैं?",
        InterviewSlot.CURRENT_OCCUPATION: "आप अभी कौन-सा काम करते हैं, यदि कोई है?",
        InterviewSlot.SKILLS: "आपके पास कौन-से कौशल या पारंपरिक काम के कौशल हैं?",
        InterviewSlot.INTERESTS: "आप किस तरह के काम में रुचि रखते हैं?",
        InterviewSlot.ASPIRATIONS: "भविष्य में आप कौन-सा काम करना चाहते हैं?",
        InterviewSlot.EMPLOYMENT_PREFERENCE: "आप वेतन वाला काम, स्वरोज़गार, अप्रेंटिसशिप या घर से काम में क्या पसंद करेंगे?",
        InterviewSlot.MOBILITY: "क्या आप काम या प्रशिक्षण के लिए यात्रा कर सकते हैं? हाँ तो कितनी दूर?",
        InterviewSlot.CONSTRAINTS: "क्या कोई स्वास्थ्य, पहुँच या काम से जुड़ी बाधा है जिसे हमें ध्यान में रखना चाहिए?",
    },
}


class BaseLivelihoodInterviewService(ABC):
    @abstractmethod
    async def process_turn(self, request: InterviewTurnRequest) -> InterviewTurnResponse:
        """Merge one extracted turn and select the next materially useful question."""


class LivelihoodInterviewService(BaseLivelihoodInterviewService):
    """State-light interview service; callers retain profile/session state between turns."""

    def __init__(self, extraction_service: BaseProfileExtractionService):
        self._extraction_service = extraction_service

    @staticmethod
    def _merge_unique_strings(existing: list[str], incoming: list[str]) -> list[str]:
        result = list(existing)
        seen = {value.casefold() for value in result}
        for value in incoming:
            if value.casefold() not in seen:
                seen.add(value.casefold())
                result.append(value)
        return result

    @staticmethod
    def _merge_skills(existing: list[Skill], incoming: list[Skill]) -> list[Skill]:
        result = list(existing)
        seen = {skill.skill_id for skill in result}
        for skill in incoming:
            if skill.skill_id not in seen:
                seen.add(skill.skill_id)
                result.append(skill)
        return result

    def merge_profile(self, current: BeneficiaryProfile, extracted: BeneficiaryProfile) -> BeneficiaryProfile:
        """Apply only explicit/non-UNKNOWN extracted values; never erase profile facts."""
        updates = {
            "normalized_skills": self._merge_skills(current.normalized_skills, extracted.normalized_skills),
            "traditional_skills": self._merge_unique_strings(current.traditional_skills, extracted.traditional_skills),
            "interests": self._merge_unique_strings(current.interests, extracted.interests),
            "aspirations": self._merge_unique_strings(current.aspirations, extracted.aspirations),
        }
        for field in ("age", "location", "current_occupation", "family_occupation", "current_income_range",
                      "education_field", "willingness_to_travel", "max_travel_distance_km", "physical_constraints"):
            value = getattr(extracted, field)
            if value is not None:
                updates[field] = value
        if extracted.gender != Gender.UNKNOWN:
            updates["gender"] = extracted.gender
        if extracted.education_level != EducationLevel.UNKNOWN:
            updates["education_level"] = extracted.education_level
        if extracted.employment_preference != EmploymentPreference.UNKNOWN:
            updates["employment_preference"] = extracted.employment_preference
        if extracted.preferred_language and extracted.preferred_language != "unknown":
            updates["preferred_language"] = extracted.preferred_language
        if current.profile_source == ProfileSource.UNKNOWN and extracted.profile_source != ProfileSource.UNKNOWN:
            updates["profile_source"] = extracted.profile_source
        return current.model_copy(update=updates)

    @staticmethod
    def missing_slots(profile: BeneficiaryProfile) -> list[InterviewSlot]:
        """Return known gaps in stable priority order; constraints stay optional."""
        missing = []
        if profile.age is None:
            missing.append(InterviewSlot.AGE)
        if profile.education_level == EducationLevel.UNKNOWN:
            missing.append(InterviewSlot.EDUCATION)
        if profile.location is None:
            missing.append(InterviewSlot.LOCATION)
        if profile.current_occupation is None:
            missing.append(InterviewSlot.CURRENT_OCCUPATION)
        if not profile.normalized_skills and not profile.traditional_skills:
            missing.append(InterviewSlot.SKILLS)
        if not profile.interests:
            missing.append(InterviewSlot.INTERESTS)
        if not profile.aspirations:
            missing.append(InterviewSlot.ASPIRATIONS)
        if profile.employment_preference == EmploymentPreference.UNKNOWN:
            missing.append(InterviewSlot.EMPLOYMENT_PREFERENCE)
        if profile.willingness_to_travel is None:
            missing.append(InterviewSlot.MOBILITY)
        if profile.physical_constraints is None:
            missing.append(InterviewSlot.CONSTRAINTS)
        return missing

    @staticmethod
    def _question(slot: InterviewSlot, language: str) -> InterviewQuestion:
        language_key = language.casefold().split("-")[0]
        localized = _QUESTION_TEXT.get(language_key, _QUESTION_TEXT["en"])
        return InterviewQuestion(slot=slot, text=localized[slot], language=language_key if language_key in _QUESTION_TEXT else "en")

    async def process_turn(self, request: InterviewTurnRequest) -> InterviewTurnResponse:
        extraction = await self._extraction_service.extract_profile(ProfileExtractRequest(
            raw_text=request.user_text, language=request.language, source=ProfileSource.VOICE_INTERVIEW,
        ))
        profile = self.merge_profile(request.profile, extraction.extracted_profile)
        missing = self.missing_slots(profile)
        unknown = list(dict.fromkeys(request.unknown_slots))
        actionable = [slot for slot in _SLOT_ORDER if slot in missing and slot not in unknown]
        next_question = self._question(actionable[0], request.language) if actionable else None
        complete = not actionable
        completion = round((len(_SLOT_ORDER) - len(missing)) / len(_SLOT_ORDER) * 100, 2)
        profile = profile.model_copy(update={"profile_completion_pct": completion})
        return InterviewTurnResponse(
            session_id=request.session_id, profile=profile, missing_slots=missing,
            unknown_slots=unknown, next_question=next_question, is_complete=complete,
            status="completed" if complete else "in_progress",
        )
