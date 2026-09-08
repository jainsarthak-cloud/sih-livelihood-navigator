"""Conservative RawSkill to canonical Skill normalization.

This module intentionally uses only the in-memory canonical ontology.  Its
matching stages are deterministic and ordered so a future embedding matcher can
be added as a later, separately governed fallback without changing callers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Iterable, Union

from app.core.config import Settings, settings
from app.data.repositories.domain_repositories import SkillRepository
from app.schemas.skill import (
    RawSkill,
    Skill,
    SkillNormalizationMethod,
    SkillNormalizationResult,
    SkillNormalizationStatus,
)


@dataclass(frozen=True)
class _Candidate:
    skill: Skill
    input_value: str
    method: SkillNormalizationMethod


class BaseSkillNormalizationService(ABC):
    """Contract for mapping raw skill observations to the canonical ontology."""

    @abstractmethod
    def normalize(self, raw_skill: Union[RawSkill, str]) -> SkillNormalizationResult:
        """Return a canonical match only when it satisfies configured confidence."""


class SkillNormalizationService(BaseSkillNormalizationService):
    """Ontology-backed normalizer with conservative exact, phrase, and fuzzy stages."""

    def __init__(self, skill_repository: SkillRepository, config: Settings = settings):
        self._repository = skill_repository
        self._min_confidence = config.SKILL_NORMALIZATION_MIN_CONFIDENCE
        self._phrase_confidence = config.SKILL_NORMALIZATION_PHRASE_CONFIDENCE

    @staticmethod
    def _key(value: str) -> str:
        value = unicodedata.normalize("NFKC", value).casefold()
        return " ".join(re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).split())

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        """Match complete token sequences only (never a substring of a word)."""
        return bool(re.search(rf"(?:^| ){re.escape(phrase)}(?:$| )", text))

    def _candidates(self) -> Iterable[_Candidate]:
        for skill in sorted(self._repository.list_all(), key=lambda item: item.skill_id):
            yield _Candidate(skill, skill.name, SkillNormalizationMethod.EXACT_NAME)
            for alias in sorted(skill.aliases, key=lambda item: (self._key(item), item)):
                yield _Candidate(skill, alias, SkillNormalizationMethod.EXACT_ALIAS)

    @staticmethod
    def _unknown(raw_skill: RawSkill) -> SkillNormalizationResult:
        return SkillNormalizationResult(
            raw_skill=raw_skill,
            status=SkillNormalizationStatus.UNKNOWN,
            normalization_method=SkillNormalizationMethod.UNKNOWN,
            confidence=0.0,
        )

    def _result(
        self, raw_skill: RawSkill, candidate: _Candidate, confidence: float
    ) -> SkillNormalizationResult:
        return SkillNormalizationResult(
            raw_skill=raw_skill,
            status=SkillNormalizationStatus.MATCHED,
            canonical_skill_id=candidate.skill.skill_id,
            canonical_skill_name=candidate.skill.name,
            matched_input=candidate.input_value,
            normalization_method=candidate.method,
            confidence=confidence,
        )

    def get_canonical_skill(self, skill_id: str) -> Skill | None:
        """Expose a read-only canonical lookup for downstream service composition."""
        return self._repository.get_by_id(skill_id)

    def _select_unique(
        self, candidates: list[_Candidate]
    ) -> _Candidate | None:
        """Reject ontology collisions instead of resolving them arbitrarily."""
        skill_ids = {candidate.skill.skill_id for candidate in candidates}
        return candidates[0] if len(skill_ids) == 1 and candidates else None

    def normalize(self, raw_skill: Union[RawSkill, str]) -> SkillNormalizationResult:
        """Normalize one raw observation without altering its original text or metadata."""
        if isinstance(raw_skill, str):
            raw_skill = RawSkill(raw_text=raw_skill)
        raw_key = self._key(raw_skill.raw_text)
        if not raw_key:
            return self._unknown(raw_skill)

        candidates = list(self._candidates())
        # Keep exact canonical/alias lookup in the repository layer so another
        # storage implementation can optimize it without changing this service.
        exact_skill_ids = {
            skill.skill_id
            for skill in self._repository.find_by_normalized_term(raw_skill.raw_text)
        }
        exact = [
            item
            for item in candidates
            if item.skill.skill_id in exact_skill_ids
            and self._key(item.input_value) == raw_key
        ]
        selected = self._select_unique(exact)
        if selected is not None:
            return self._result(raw_skill, selected, 1.0)

        phrase = [
            _Candidate(
                item.skill,
                item.input_value,
                SkillNormalizationMethod.PHRASE_NAME
                if item.method == SkillNormalizationMethod.EXACT_NAME
                else SkillNormalizationMethod.PHRASE_ALIAS,
            )
            for item in candidates
            if self._contains_phrase(raw_key, self._key(item.input_value))
        ]
        # Prefer the most specific supported phrase; ties across skills are unknown.
        if phrase and self._phrase_confidence >= self._min_confidence:
            longest = max(len(self._key(item.input_value)) for item in phrase)
            selected = self._select_unique(
                [item for item in phrase if len(self._key(item.input_value)) == longest]
            )
            if selected is not None:
                return self._result(raw_skill, selected, self._phrase_confidence)

        scored = [
            (SequenceMatcher(None, raw_key, self._key(item.input_value)).ratio(), item)
            for item in candidates
        ]
        best_score = max((score for score, _ in scored), default=0.0)
        if best_score < self._min_confidence:
            return self._unknown(raw_skill)
        best = [item for score, item in scored if score == best_score]
        selected = self._select_unique(best)
        if selected is None:
            return self._unknown(raw_skill)
        method = (
            SkillNormalizationMethod.FUZZY_NAME
            if selected.method == SkillNormalizationMethod.EXACT_NAME
            else SkillNormalizationMethod.FUZZY_ALIAS
        )
        return self._result(
            raw_skill,
            _Candidate(selected.skill, selected.input_value, method),
            best_score,
        )
