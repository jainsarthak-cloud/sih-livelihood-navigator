"""Phase 11 end-to-end structured deterministic livelihood assessment tests."""

import asyncio
from pathlib import Path

import pytest

from app.core.config import Settings
from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.common import EducationLevel, EmploymentPreference, GeographicLocation, SourceEvidence, SourceType
from app.schemas.eligibility import EligibilityResult, EligibilityStatus
from app.schemas.livelihood import LivelihoodAssessRequest
from app.schemas.occupation import Occupation
from app.schemas.profile import BeneficiaryProfile
from app.schemas.skill import Skill
from app.services.livelihood.assessment import LivelihoodAssessmentService
from app.services.market.demand import MarketDemandService
from app.services.normalization.skill_normalizer import SkillNormalizationService
from app.services.opportunity.intelligence import OpportunityIntelligenceService
from app.services.recommendation.recommender import RecommendationService
from app.services.roadmap.generator import RoadmapService


def make_service():
    repositories = (SkillRepository(), OccupationRepository(), CourseRepository(), OpportunityRepository())
    loaders = (SkillLoader(Path("data/seed/skills.json")), OccupationLoader(Path("data/seed/occupations.json")),
               CourseLoader(Path("data/seed/courses.json")), OpportunityLoader(Path("data/seed/opportunities.json")))
    for repository, loader in zip(repositories, loaders):
        result = loader.load()
        assert not result.errors
        for record in result.records:
            repository.add(record)
    skills, occupations, courses, opportunities = repositories
    config = Settings()
    normalizer = SkillNormalizationService(skills, config)
    intelligence = OpportunityIntelligenceService(opportunities, occupations, normalizer)
    return LivelihoodAssessmentService(
        RecommendationService(occupations, courses, opportunities, skills, normalizer, config),
        intelligence, MarketDemandService(opportunities, intelligence),
        RoadmapService(occupations, courses, opportunities, skills, normalizer), config,
    ), repositories


def run(service, request):
    return asyncio.run(service.assess(request))


def apparel_profile(**overrides):
    values = dict(
        beneficiary_id="BEN-E2E", education_level=EducationLevel.PRIMARY,
        normalized_skills=[Skill(skill_id="SKL-SYN-001", name="Basic Garment Stitching"),
                           Skill(skill_id="SKL-SYN-003", name="Customer Service Communication")],
        interests=["Apparel"], aspirations=["Tailor"], employment_preference=EmploymentPreference.WAGE_EMPLOYMENT,
        location=GeographicLocation(state="Demo State", district="Demo District"),
    )
    values.update(overrides)
    return BeneficiaryProfile(**values)


def test_complete_profile_connects_recommendations_gaps_roadmap_market_and_synthetic_scope():
    response = run(make_service()[0], LivelihoodAssessRequest(profile=apparel_profile()))

    assert response.status == "completed"
    assert response.pathways[0].recommendation.occupation_reference == "OCC-SYN-001"
    assert response.pathways[0].roadmap is not None
    assert response.pathways[0].roadmap.matched_skills == ["SKL-SYN-001", "SKL-SYN-003"]
    assert response.market_observation.top_sectors[0].active_opportunity_count == 1
    assert "Synthetic/demo" in response.market_observation.limitations[1]
    assert response.metadata.deterministic is True


def test_minimal_and_unknown_skill_profiles_are_explicitly_incomplete_not_fabricated():
    response = run(make_service()[0], LivelihoodAssessRequest(profile=BeneficiaryProfile()))

    assert response.status == "incomplete_or_no_pathway" or response.pathways
    assert any("canonical skills are unknown" in item for item in response.limitations)
    assert any("location is unknown" in item for item in response.limitations)
    for pathway in response.pathways:
        assert all(gap.gap_status.value == "unknown" for gap in pathway.roadmap.skill_gaps)


def test_no_matching_opportunity_course_and_ineligible_pathway_are_safe_empty_results():
    service, repositories = make_service()
    _, occupations, _, _ = repositories
    occupations.add(Occupation(occupation_id="OCC-NO-COURSE", name="No course", sector="Other", required_skills=[]))
    no_course = run(service, LivelihoodAssessRequest(profile=apparel_profile(), target_sector="Other"))
    ineligible = EligibilityResult(scheme_name="Explicit", status=EligibilityStatus.INELIGIBLE, explanation="Failed")
    blocked = run(service, LivelihoodAssessRequest(profile=apparel_profile(), eligibility_result=ineligible))

    assert no_course.pathways[0].roadmap is not None
    assert any("No linked course" in item for item in no_course.pathways[0].roadmap.limitations)
    assert blocked.pathways == []
    assert "No eligible canonical livelihood pathways" in blocked.limitations[-1]


def test_mobility_and_work_preference_restrictions_remain_deterministic():
    service, _ = make_service()
    profile = apparel_profile(employment_preference=EmploymentPreference.APPRENTICESHIP,
                              willingness_to_travel=False,
                              location=GeographicLocation(state="Other", district="Elsewhere"))
    response = run(service, LivelihoodAssessRequest(profile=profile))

    assert [pathway.recommendation.occupation_reference for pathway in response.pathways] == ["OCC-SYN-002"]
    assert response.local_opportunity_evidence == []


def test_evidence_propagates_and_repeated_execution_is_equivalent():
    evidence = SourceEvidence(source_id="SRC-E2E", source_type=SourceType.FIELD_SURVEY, source_name="E2E profile evidence")
    service, _ = make_service()
    request = LivelihoodAssessRequest(profile=apparel_profile(evidence=[evidence]))
    first, second = run(service, request), run(service, request)

    assert [item.source_id for item in first.evidence] == ["SRC-E2E"]
    assert first.model_dump() == second.model_dump()


def test_assessment_request_rejects_invalid_bounds_and_enum_values():
    with pytest.raises(ValueError):
        LivelihoodAssessRequest(profile=BeneficiaryProfile(), max_recommendations=4)
    with pytest.raises(ValueError):
        LivelihoodAssessRequest.model_validate({"profile": {"employment_preference": "invalid"}})
