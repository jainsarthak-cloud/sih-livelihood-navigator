"""Deterministic structured opportunity normalization; no untrusted text inference."""

from abc import ABC, abstractmethod

from app.data.repositories.domain_repositories import OccupationRepository
from app.schemas.opportunity import (
    Opportunity,
    OpportunityNormalizationResult,
    OpportunityParseRequest,
    OpportunityParseResponse,
)
from app.services.normalization.skill_normalizer import SkillNormalizationService


class BaseOpportunityParsingService(ABC):
    @abstractmethod
    async def parse_opportunities(self, request: OpportunityParseRequest) -> OpportunityParseResponse:
        """Normalize a structured record; raw text alone is intentionally not inferred."""


class OpportunityParsingService(BaseOpportunityParsingService):
    """Converts trusted structured records to canonical IDs while retaining raw fields."""

    def __init__(self, occupation_repository: OccupationRepository, skill_normalizer: SkillNormalizationService):
        self._occupations = occupation_repository
        self._normalizer = skill_normalizer

    async def parse_opportunities(self, request: OpportunityParseRequest) -> OpportunityParseResponse:
        if request.record is None:
            return OpportunityParseResponse(
                limitations=["Unstructured text is preserved but is not converted into an opportunity without a trusted structured record."],
                status="structured_record_required",
            )
        draft = request.record
        skill_results = [self._normalizer.normalize(raw) for raw in draft.required_skills_raw]
        canonical_skill_ids = [
            result.canonical_skill_id for result in skill_results if result.canonical_skill_id is not None
        ]
        limitations = []
        for raw, result in zip(draft.required_skills_raw, skill_results):
            if result.canonical_skill_id is None:
                limitations.append(f"Required skill {raw!r} could not be safely normalized.")
        occupation = None
        if draft.occupation_raw:
            matches = self._occupations.find_by_normalized_term(draft.occupation_raw)
            if len(matches) == 1:
                occupation = matches[0]
            elif len(matches) > 1:
                limitations.append("Occupation mapping is ambiguous and was left unknown.")
            else:
                limitations.append("Occupation mapping is unknown in the canonical ontology.")
        else:
            limitations.append("No raw occupation was supplied for canonical occupation mapping.")
        opportunity = Opportunity(
            opportunity_id=draft.opportunity_id, title=draft.title, opportunity_type=draft.opportunity_type,
            sector=draft.sector, description=draft.description, required_skills=list(dict.fromkeys(canonical_skill_ids)),
            location=draft.location, employer_or_provider=draft.employer_or_provider, source=draft.source,
            collected_at=draft.collected_at, verification_status=draft.verification_status,
            last_verified_at=draft.last_verified_at, lifecycle_status=draft.lifecycle_status,
            financial_assistance=draft.financial_assistance, evidence=draft.evidence,
            is_synthetic=draft.is_synthetic, data_classification=draft.data_classification,
        )
        result = OpportunityNormalizationResult(
            opportunity=opportunity, raw_occupation=draft.occupation_raw,
            canonical_occupation_id=occupation.occupation_id if occupation else None,
            canonical_occupation_name=occupation.name if occupation else None,
            raw_required_skills=draft.required_skills_raw, skill_normalizations=skill_results,
            limitations=limitations,
        )
        return OpportunityParseResponse(
            parsed_opportunities=[opportunity], normalization_results=[result], total_parsed=1,
            limitations=limitations, status="completed",
        )
