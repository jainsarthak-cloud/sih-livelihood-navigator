"""Phase 10 opportunity normalization, matching, and observation-count tests."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from app.data.loaders.domain_loaders import OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.common import EmploymentPreference, GeographicLocation, SourceEvidence, SourceType, VerificationStatus
from app.schemas.market import MarketDemandRequest
from app.schemas.occupation import Occupation
from app.schemas.skill import Skill
from app.schemas.opportunity import (
    OpportunityDraft, OpportunityLifecycle, OpportunityMatchRequest, OpportunityParseRequest, OpportunityType,
)
from app.schemas.profile import BeneficiaryProfile
from app.services.market.demand import MarketDemandService
from app.services.normalization.skill_normalizer import SkillNormalizationService
from app.services.opportunity.intelligence import OpportunityIntelligenceService
from app.services.opportunity.parser import OpportunityParsingService


def repositories():
    skill_repository, occupation_repository, opportunity_repository = SkillRepository(), OccupationRepository(), OpportunityRepository()
    for repository, loader in (
        (skill_repository, SkillLoader(Path("data/seed/skills.json"))),
        (occupation_repository, OccupationLoader(Path("data/seed/occupations.json"))),
        (opportunity_repository, OpportunityLoader(Path("data/seed/opportunities.json"))),
    ):
        result = loader.load()
        assert not result.errors
        for record in result.records:
            repository.add(record)
    normalizer = SkillNormalizationService(skill_repository)
    intelligence = OpportunityIntelligenceService(opportunity_repository, occupation_repository, normalizer)
    return skill_repository, occupation_repository, opportunity_repository, normalizer, intelligence


def draft(**overrides):
    values = dict(
        opportunity_id="OPP-INPUT-1", title="Tailor vacancy", opportunity_type=OpportunityType.WAGE_EMPLOYMENT,
        sector="Textile and Apparel", location=GeographicLocation(state="Demo State", district="Demo District"),
        collected_at=datetime.now(timezone.utc), occupation_raw="Tailor", required_skills_raw=["silai"],
        verification_status=VerificationStatus.VERIFIED, lifecycle_status=OpportunityLifecycle.ACTIVE,
        is_synthetic=True,
    )
    values.update(overrides)
    return OpportunityDraft(**values)


def test_valid_normalization_preserves_raw_values_provenance_and_synthetic_marker():
    _, occupations, _, normalizer, _ = repositories()
    service = OpportunityParsingService(occupations, normalizer)
    evidence = SourceEvidence(source_id="SRC-INPUT", source_type=SourceType.FIELD_SURVEY, source_name="Input evidence")
    response = asyncio.run(service.parse_opportunities(OpportunityParseRequest(record=draft(source=evidence))))
    result = response.normalization_results[0]

    assert result.canonical_occupation_id == "OCC-SYN-001"
    assert result.opportunity.required_skills == ["SKL-SYN-001"]
    assert result.raw_required_skills == ["silai"]
    assert result.opportunity.source.source_id == "SRC-INPUT"
    assert result.opportunity.is_synthetic is True


def test_unknown_or_ambiguous_mappings_are_left_unresolved_without_fabrication():
    skills, occupations, _, normalizer, _ = repositories()
    occupations.add(Occupation(occupation_id="OCC-DUP", name="Duplicate Tailor", aliases=["Tailor"], sector="Textile and Apparel"))
    skills.add(Skill(skill_id="SKL-DUP", name="Duplicate skill", aliases=["shared skill"]))
    skills.add(Skill(skill_id="SKL-DUP-2", name="Second duplicate skill", aliases=["shared skill"]))
    # Rebuild so the normalizer sees the deliberately ambiguous alias.
    normalizer = SkillNormalizationService(skills)
    service = OpportunityParsingService(occupations, normalizer)
    response = asyncio.run(service.parse_opportunities(OpportunityParseRequest(record=draft(
        occupation_raw="Tailor", required_skills_raw=["not a canonical skill", "shared skill"],
    ))))
    result = response.normalization_results[0]

    assert result.canonical_occupation_id is None
    assert result.opportunity.required_skills == []
    assert any("ambiguous" in item for item in result.limitations)
    assert any("could not be safely normalized" in item for item in result.limitations)


def test_unknown_occupation_is_left_unknown_with_no_substitute_mapping():
    _, occupations, _, normalizer, _ = repositories()
    result = asyncio.run(OpportunityParsingService(occupations, normalizer).parse_opportunities(
        OpportunityParseRequest(record=draft(occupation_raw="Unlisted role"))
    )).normalization_results[0]

    assert result.canonical_occupation_id is None
    assert "unknown in the canonical ontology" in result.limitations[0]


def test_raw_text_without_structured_record_is_not_parsed_or_fabricated():
    _, occupations, _, normalizer, _ = repositories()
    response = asyncio.run(OpportunityParsingService(occupations, normalizer).parse_opportunities(
        OpportunityParseRequest(raw_content="Need ten tailors immediately")
    ))

    assert response.parsed_opportunities == []
    assert response.status == "structured_record_required"


def test_location_mobility_preference_and_lifecycle_filters_are_evidence_bound():
    _, _, opportunities, _, intelligence = repositories()
    profile = BeneficiaryProfile(
        location=GeographicLocation(state="Demo State", district="Demo District"),
        employment_preference=EmploymentPreference.WAGE_EMPLOYMENT,
        willingness_to_travel=False,
    )
    response = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=profile)))

    assert [match.opportunity.opportunity_id for match in response.matches] == []  # seed active record is apprenticeship
    apprenticeship = profile.model_copy(update={"employment_preference": EmploymentPreference.APPRENTICESHIP})
    response = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=apprenticeship)))
    assert [match.opportunity.opportunity_id for match in response.matches] == ["OPP-SYN-001"]
    assert response.matches[0].location_match is True

    reported = opportunities.get_by_id("OPP-SYN-002")
    assert reported.lifecycle_status == OpportunityLifecycle.REPORTED
    assert "OPP-SYN-002" not in [match.opportunity.opportunity_id for match in response.matches]

    remote = response.matches[0].opportunity.model_copy(update={
        "opportunity_id": "OPP-REMOTE", "location": GeographicLocation(state="Other", district="Elsewhere"),
    })
    opportunities.add(remote)
    constrained = asyncio.run(intelligence.match_opportunities(OpportunityMatchRequest(profile=apprenticeship)))
    assert "OPP-REMOTE" not in [match.opportunity.opportunity_id for match in constrained.matches]

    expired = remote.model_copy(update={"opportunity_id": "OPP-EXPIRED", "lifecycle_status": OpportunityLifecycle.EXPIRED})
    opportunities.add(expired)
    filled = remote.model_copy(update={"opportunity_id": "OPP-FILLED", "lifecycle_status": OpportunityLifecycle.FILLED})
    opportunities.add(filled)
    assert "OPP-EXPIRED" not in [match.opportunity.opportunity_id for match in constrained.matches]
    assert "OPP-FILLED" not in [match.opportunity.opportunity_id for match in constrained.matches]


def test_market_counts_are_explicit_observations_and_missing_evidence_is_unknown():
    _, _, opportunities, _, intelligence = repositories()
    service = MarketDemandService(opportunities, intelligence)
    observed = asyncio.run(service.analyze_demand(MarketDemandRequest(state="Demo State", district="Demo District")))
    absent = asyncio.run(service.analyze_demand(MarketDemandRequest(state="No", district="Records")))

    sector = observed.top_sectors[0]
    assert sector.active_opportunity_count == 1
    assert sector.verified_active_opportunity_count == 0
    assert sector.demand_level == "unknown"
    assert "synthetic/demo" in sector.scope_note
    assert absent.top_sectors == []
    assert "market demand is unknown" in absent.limitations[0]
