"""Tests for Phase 4 deterministic skill normalization."""

from pathlib import Path

from app.core.config import Settings
from app.data.loaders.domain_loaders import SkillLoader
from app.data.repositories.domain_repositories import SkillRepository
from app.schemas.skill import (
    RawSkill,
    Skill,
    SkillNormalizationMethod,
    SkillNormalizationStatus,
)
from app.services.normalization.skill_normalizer import SkillNormalizationService


def make_service(**settings_overrides: float) -> SkillNormalizationService:
    repository = SkillRepository()
    loaded = SkillLoader(Path("data/seed/skills.json")).load()
    assert not loaded.errors
    for skill in loaded.records:
        repository.add(skill)
    return SkillNormalizationService(repository, Settings(**settings_overrides))


def test_exact_alias_uses_existing_canonical_skill_and_preserves_raw_input():
    raw = RawSkill(raw_text="  SiLAI  ", language="hi", context="self-reported")
    result = make_service().normalize(raw)

    assert result.status == SkillNormalizationStatus.MATCHED
    assert result.canonical_skill_id == "SKL-SYN-001"
    assert result.canonical_skill_name == "Basic Garment Stitching"
    assert result.matched_input == "Silai"
    assert result.normalization_method == SkillNormalizationMethod.EXACT_ALIAS
    assert result.confidence == 1.0
    assert result.raw_skill == raw


def test_phrase_and_multilingual_aliases_are_grounded_in_seed_data():
    service = make_service()
    phrase = service.normalize("Main silai ka kaam karti hoon")
    multilingual = service.normalize("grahak-seva")

    assert phrase.canonical_skill_id == "SKL-SYN-001"
    assert phrase.matched_input == "silai ka kaam"
    assert phrase.normalization_method == SkillNormalizationMethod.PHRASE_ALIAS
    assert multilingual.canonical_skill_id == "SKL-SYN-003"
    assert multilingual.matched_input == "Grahak seva"


def test_high_confidence_spelling_variation_is_matched_deterministically():
    result = make_service().normalize("wirng")

    assert result.canonical_skill_id == "SKL-SYN-002"
    assert result.matched_input == "Wiring"
    assert result.normalization_method == SkillNormalizationMethod.FUZZY_ALIAS
    assert result.confidence >= 0.90


def test_low_confidence_or_unrecognized_skill_is_unknown_without_guessing():
    service = make_service()
    typo = service.normalize("wirng")
    unknown = service.normalize("plumbing")
    strict_typo = make_service(SKILL_NORMALIZATION_MIN_CONFIDENCE=0.95).normalize("wirng")

    assert unknown.status == SkillNormalizationStatus.UNKNOWN
    assert unknown.canonical_skill_id is None
    assert unknown.matched_input is None
    assert unknown.normalization_method == SkillNormalizationMethod.UNKNOWN
    assert typo.status == SkillNormalizationStatus.MATCHED
    assert strict_typo.status == SkillNormalizationStatus.UNKNOWN


def test_ambiguous_alias_is_unknown_instead_of_selecting_by_order():
    repository = SkillRepository()
    repository.add(Skill(skill_id="SKL-A", name="One", aliases=["shared"]))
    repository.add(Skill(skill_id="SKL-B", name="Two", aliases=["shared"]))

    result = SkillNormalizationService(repository, Settings()).normalize("shared")

    assert result.status == SkillNormalizationStatus.UNKNOWN


def test_repository_normalized_term_query_handles_spacing_and_punctuation():
    repository = SkillRepository()
    repository.add(Skill(skill_id="SKL-A", name="Customer Service", aliases=["Grahak seva"]))

    assert [item.skill_id for item in repository.find_by_normalized_term("grahak-seva")] == ["SKL-A"]
