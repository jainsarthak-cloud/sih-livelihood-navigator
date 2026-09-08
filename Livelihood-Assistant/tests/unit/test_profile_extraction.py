"""Phase 6 profile extraction tests with mocked Gemini provider responses."""

import asyncio
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderConfigurationException, ProviderResponseException
from app.data.loaders.domain_loaders import SkillLoader
from app.data.repositories.domain_repositories import SkillRepository
from app.schemas.common import EducationLevel, EmploymentPreference, ProfileSource
from app.schemas.profile import ProfileExtractRequest
from app.services.ai.extractor import ProfileExtractionService
from app.services.ai.gemini import BaseStructuredExtractionProvider, GeminiStructuredExtractionProvider
from app.services.normalization.skill_normalizer import SkillNormalizationService


class FakeGemini(BaseStructuredExtractionProvider):
    provider_name = "gemini"
    model_name = "fake-gemini-json"

    def __init__(self, response):
        self.response = response
        self.prompts = []

    async def extract_json(self, prompt):
        self.prompts.append(prompt)
        return self.response


def make_service(response) -> tuple[ProfileExtractionService, FakeGemini]:
    repository = SkillRepository()
    loaded = SkillLoader(Path("data/seed/skills.json")).load()
    assert not loaded.errors
    for skill in loaded.records:
        repository.add(skill)
    provider = FakeGemini(response)
    return ProfileExtractionService(provider, SkillNormalizationService(repository), Settings()), provider


def extract(service, text="I do stitching"):
    return asyncio.run(service.extract_profile(ProfileExtractRequest(raw_text=text, language="hi", source=ProfileSource.TEXT_INPUT)))


def test_valid_extraction_preserves_text_and_normalizes_seed_backed_skills():
    service, provider = make_service({
        "age": 24, "gender": "female", "education_level": "primary",
        "location": {"state": "Demo State", "district": "Demo District"},
        "skills": ["silai"], "traditional_skills": ["grahak seva"],
        "interests": ["apparel"], "aspirations": ["tailor"],
        "employment_preference": "wage_employment", "willingness_to_travel": False,
        "preferred_language": "hi", "extraction_confidence": 0.82,
    })
    response = extract(service, "मैं सिलाई और ग्राहक सेवा का काम करती हूँ")

    assert response.original_text == "मैं सिलाई और ग्राहक सेवा का काम करती हूँ"
    assert response.extracted_profile.age == 24
    assert response.extracted_profile.education_level == EducationLevel.PRIMARY
    assert response.extracted_profile.employment_preference == EmploymentPreference.WAGE_EMPLOYMENT
    assert {skill.skill_id for skill in response.extracted_profile.normalized_skills} == {"SKL-SYN-001", "SKL-SYN-003"}
    assert [skill.raw_text for skill in response.raw_skills_detected] == ["silai", "grahak seva"]
    assert response.confidence_score == 0.82
    assert response.extraction_metadata.model == "fake-gemini-json"
    assert "untrusted input" in provider.prompts[0].casefold()


def test_missing_fields_remain_unknown_or_null_without_defaulting_claims():
    service, _ = make_service({"skills": [], "traditional_skills": [], "extraction_confidence": 0.1})
    response = extract(service)

    assert response.extracted_profile.age is None
    assert response.extracted_profile.education_level == EducationLevel.UNKNOWN
    assert response.extracted_profile.location is None
    assert response.extracted_profile.community is None
    assert response.missing_critical_fields == ["age", "education_level", "location", "skills"]


@pytest.mark.parametrize("payload", [
    "not a JSON object",
    {"gender": "not-a-gender"},
    {"skills": [123]},
    {"unexpected": "field"},
])
def test_malformed_or_invalid_model_output_is_rejected(payload):
    service, _ = make_service(payload)

    with pytest.raises(ProviderResponseException):
        extract(service)


def test_multilingual_input_is_preserved_without_language_specific_code_paths():
    service, _ = make_service({
        "current_occupation": "दर्जी", "skills": ["Silai"], "traditional_skills": [],
        "preferred_language": "hi", "extraction_confidence": 0.7,
    })
    response = extract(service, "मैं दर्जी हूँ और सिलाई करती हूँ")

    assert response.original_text.startswith("मैं")
    assert response.extracted_profile.current_occupation == "दर्जी"
    assert response.extracted_profile.preferred_language == "hi"
    assert response.extracted_profile.normalized_skills[0].skill_id == "SKL-SYN-001"


def test_missing_gemini_key_fails_without_exposing_a_secret():
    provider = GeminiStructuredExtractionProvider(Settings(GEMINI_API_KEY=""))

    with pytest.raises(ProviderConfigurationException) as error:
        asyncio.run(provider.extract_json("test"))
    assert "API_KEY" not in str(error.value)
