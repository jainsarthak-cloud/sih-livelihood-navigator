"""Focused Phase 5 deterministic recommendation-engine tests."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.common import EducationLevel, EmploymentPreference, GeographicLocation, SourceEvidence, SourceType
from app.schemas.course import NSQFCourse
from app.schemas.eligibility import EligibilityResult, EligibilityStatus
from app.schemas.occupation import EmploymentType, Occupation
from app.schemas.opportunity import Opportunity, OpportunityLifecycle, OpportunityType
from app.schemas.profile import BeneficiaryProfile
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation.recommender import RecommendationService


def make_service() -> RecommendationService:
    repositories = (SkillRepository(), OccupationRepository(), CourseRepository(), OpportunityRepository())
    loaders = (
        SkillLoader(Path("data/seed/skills.json")), OccupationLoader(Path("data/seed/occupations.json")),
        CourseLoader(Path("data/seed/courses.json")), OpportunityLoader(Path("data/seed/opportunities.json")),
    )
    for repository, loader in zip(repositories, loaders):
        result = loader.load()
        assert not result.errors
        for record in result.records:
            repository.add(record)
    skill_repository, occupation_repository, course_repository, opportunity_repository = repositories
    return RecommendationService(occupation_repository, course_repository, opportunity_repository, skill_repository, config=Settings())


def run(service: RecommendationService, request: RecommendationRequest):
    return asyncio.run(service.get_recommendations(request))


def strong_apparel_profile(**overrides) -> BeneficiaryProfile:
    data = dict(
        beneficiary_id="BEN-1", education_level=EducationLevel.PRIMARY,
        traditional_skills=["silai", "grahak seva"], interests=["Apparel"],
        employment_preference=EmploymentPreference.WAGE_EMPLOYMENT,
        location=GeographicLocation(state="Demo State", district="Demo District"),
    )
    data.update(overrides)
    return BeneficiaryProfile(**data)


def test_candidate_generation_joins_canonical_occupation_course_and_active_opportunity():
    service = make_service()
    candidates = service.generate_candidates(RecommendationRequest(profile=strong_apparel_profile()))

    assert [(item.occupation.occupation_id, item.course.course_id) for item in candidates] == [("OCC-SYN-001", "CRS-SYN-001")]
    assert [item.opportunity_id for item in candidates[0].opportunities] == ["OPP-SYN-001"]


def test_hard_filters_apply_known_education_preference_and_explicit_ineligibility():
    service = make_service()
    low_education = BeneficiaryProfile(education_level=EducationLevel.NONE)
    apprenticeship = strong_apparel_profile(employment_preference=EmploymentPreference.APPRENTICESHIP)
    ineligible = EligibilityResult(scheme_name="Verified constraint", status=EligibilityStatus.INELIGIBLE, explanation="Explicitly failed.")

    assert all(item.occupation.occupation_id != "OCC-SYN-001" for item in service.generate_candidates(RecommendationRequest(profile=low_education)))
    assert [item.occupation.occupation_id for item in service.generate_candidates(RecommendationRequest(profile=apprenticeship))] == ["OCC-SYN-002"]
    assert service.generate_candidates(RecommendationRequest(profile=strong_apparel_profile(), eligibility_result=ineligible)) == []


def test_known_mobility_constraint_removes_remote_active_opportunity():
    service = make_service()
    remote = Opportunity(
        opportunity_id="OPP-REMOTE", title="Remote apparel", opportunity_type=OpportunityType.WAGE_EMPLOYMENT,
        sector="Textile and Apparel", required_skills=[],
        location=GeographicLocation(state="Other", district="Elsewhere"), collected_at=datetime.now(timezone.utc),
        lifecycle_status=OpportunityLifecycle.ACTIVE,
    )
    service._opportunities.add(remote)
    profile = strong_apparel_profile(willingness_to_travel=False)

    response = run(service, RecommendationRequest(profile=profile))
    assert "OPP-REMOTE" not in response.recommendations[0].opportunity_references


def test_each_score_component_and_weighted_total_are_explainable():
    response = run(make_service(), RecommendationRequest(profile=strong_apparel_profile()))
    recommendation = response.recommendations[0]
    scores = recommendation.score_breakdown

    assert scores.interest_similarity_score == 1.0
    assert scores.skill_match_score == 1.0
    assert scores.eligibility_score == 1.0
    assert scores.local_opportunity_score == 1.0
    assert scores.labour_demand_score == 0.0  # no market-demand seed data exists
    assert scores.employment_preference_score == 1.0
    assert recommendation.overall_score == 0.90


def test_ranking_top_three_limit_and_deterministic_repeated_results():
    service = make_service()
    for index in range(3, 6):
        occupation = Occupation(
            occupation_id=f"OCC-EXTRA-{index}", name=f"Extra apparel {index}", sector="Textile and Apparel",
            required_skills=["SKL-SYN-001"], employment_type=EmploymentType.FULL_TIME,
            nsqf_qualification_ids=[f"CRS-EXTRA-{index}"],
        )
        course = NSQFCourse(course_id=f"CRS-EXTRA-{index}", course_name=f"Extra course {index}", qualification_name="Extra",
                            nsqf_level=2, sector="Textile and Apparel", required_education=EducationLevel.PRIMARY)
        service._occupations.add(occupation)
        service._courses.add(course)
    request = RecommendationRequest(profile=strong_apparel_profile(), max_recommendations=20)
    first, second = run(service, request), run(service, request)

    assert len(first.recommendations) == 3
    assert [item.rank for item in first.recommendations] == [1, 2, 3]
    assert [item.recommendation_id for item in first.recommendations] == [item.recommendation_id for item in second.recommendations]


def test_incomplete_profile_is_safe_unknown_and_no_eligible_candidates_is_empty():
    service = make_service()
    incomplete = run(service, RecommendationRequest(profile=BeneficiaryProfile()))
    none = run(service, RecommendationRequest(profile=BeneficiaryProfile(), target_sector="Not in seed"))

    assert incomplete.recommendations
    assert all(item.eligibility_result.status == EligibilityStatus.UNKNOWN for item in incomplete.recommendations)
    assert all(item.overall_score == 0.0 for item in incomplete.recommendations)
    assert none.recommendations == []


def test_evidence_is_propagated_to_recommendation():
    evidence = SourceEvidence(source_id="SRC-TEST", source_type=SourceType.FIELD_SURVEY, source_name="Test intake")
    response = run(make_service(), RecommendationRequest(profile=strong_apparel_profile(evidence=[evidence])))

    assert [item.source_id for item in response.recommendations[0].evidence] == ["SRC-TEST"]
