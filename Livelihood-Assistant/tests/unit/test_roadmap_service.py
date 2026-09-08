"""Phase 9 deterministic skill-gap analysis and roadmap tests."""

import asyncio
from pathlib import Path

import pytest

from app.data.loaders.domain_loaders import CourseLoader, OccupationLoader, OpportunityLoader, SkillLoader
from app.data.repositories.domain_repositories import CourseRepository, OccupationRepository, OpportunityRepository, SkillRepository
from app.schemas.common import SourceEvidence, SourceType
from app.schemas.course import NSQFCourse
from app.schemas.occupation import Occupation
from app.schemas.profile import BeneficiaryProfile
from app.schemas.recommendation import PathwayType, Recommendation, ScoreBreakdown
from app.schemas.roadmap import RoadmapRequest
from app.schemas.skill import GapStatus, PriorityLevel, Skill
from app.services.roadmap.generator import RoadmapService


def make_service():
    repositories = (SkillRepository(), OccupationRepository(), CourseRepository(), OpportunityRepository())
    loaders = (SkillLoader(Path("data/seed/skills.json")), OccupationLoader(Path("data/seed/occupations.json")),
               CourseLoader(Path("data/seed/courses.json")), OpportunityLoader(Path("data/seed/opportunities.json")))
    for repository, loader in zip(repositories, loaders):
        loaded = loader.load()
        assert not loaded.errors
        for record in loaded.records:
            repository.add(record)
    skills, occupations, courses, opportunities = repositories
    return RoadmapService(occupations, courses, opportunities, skills), repositories


def run(service, request):
    return asyncio.run(service.generate_roadmap(request))


def profile(*skill_ids):
    return BeneficiaryProfile(beneficiary_id="BEN-ROADMAP", normalized_skills=[
        Skill(skill_id=skill_id, name=skill_id) for skill_id in skill_ids
    ])


def recommendation(**overrides):
    values = dict(
        recommendation_id="REC-SYN", pathway_type=PathwayType.COMBINED,
        occupation_reference="OCC-SYN-001", course_reference="CRS-SYN-001",
        overall_score=0.5, score_breakdown=ScoreBreakdown(skill_match_score=0, local_demand_score=0),
        confidence=0.5, explanation="Selected pathway",
    )
    values.update(overrides)
    return Recommendation(**values)


def test_complete_skill_match_marks_requirements_acquired_without_training_step():
    service, _ = make_service()
    response = run(service, RoadmapRequest(profile=profile("SKL-SYN-001", "SKL-SYN-003"), target_occupation_id="OCC-SYN-001"))

    assert all(gap.gap_status == GapStatus.ACQUIRED for gap in response.roadmap.skill_gaps)
    assert response.roadmap.matched_skills == ["SKL-SYN-001", "SKL-SYN-003"]
    assert not any(step.step_type.value == "training" for step in response.roadmap.steps)


def test_partial_match_identifies_missing_skill_with_high_explainable_priority_and_course():
    service, _ = make_service()
    response = run(service, RoadmapRequest(profile=profile("SKL-SYN-001"), recommendation=recommendation()))
    gaps = {gap.skill_id: gap for gap in response.roadmap.skill_gaps}

    assert gaps["SKL-SYN-001"].gap_status == GapStatus.ACQUIRED
    assert gaps["SKL-SYN-003"].gap_status == GapStatus.MISSING
    assert gaps["SKL-SYN-003"].priority == PriorityLevel.HIGH
    training = next(step for step in response.roadmap.steps if step.step_type.value == "training")
    assert training.course_references == ["CRS-SYN-001"]


def test_multiple_gaps_are_sorted_and_unknown_profile_does_not_claim_missing_skills():
    service, repositories = make_service()
    skills, occupations, courses, _ = repositories
    skills.add(Skill(skill_id="SKL-EXTRA", name="Extra Skill"))
    occupations.add(Occupation(occupation_id="OCC-MULTI", name="Multi", sector="Demo",
                               required_skills=["SKL-SYN-001", "SKL-EXTRA"]))
    known = run(service, RoadmapRequest(profile=profile("SKL-SYN-002"), target_occupation_id="OCC-MULTI"))
    unknown = run(service, RoadmapRequest(profile=BeneficiaryProfile(), target_occupation_id="OCC-MULTI"))

    assert [gap.skill_id for gap in known.roadmap.skill_gaps] == ["SKL-EXTRA", "SKL-SYN-001"]
    assert all(gap.gap_status == GapStatus.UNKNOWN for gap in unknown.roadmap.skill_gaps)
    assert "Beneficiary canonical skills are unknown" in unknown.roadmap.limitations[0]


def test_missing_course_mapping_is_explicitly_blocked_not_invented():
    service, repositories = make_service()
    _, occupations, _, _ = repositories
    occupations.add(Occupation(occupation_id="OCC-NO-COURSE", name="No course", sector="Demo", required_skills=["SKL-SYN-001"]))
    response = run(service, RoadmapRequest(profile=profile("SKL-SYN-002"), target_occupation_id="OCC-NO-COURSE"))

    assert any("No linked course" in item for item in response.roadmap.limitations)
    assert response.roadmap.steps[0].status.value == "blocked"
    assert response.roadmap.steps[0].step_type.value == "verification"


def test_roadmap_steps_are_ordered_and_propagate_course_recommendation_and_opportunity_evidence():
    service, repositories = make_service()
    _, _, courses, _ = repositories
    evidence = SourceEvidence(source_id="SRC-ROADMAP", source_type=SourceType.FIELD_SURVEY, source_name="Roadmap test")
    course = courses.get_by_id("CRS-SYN-001").model_copy(update={"source_metadata": evidence})
    courses.add_or_replace(course.course_id, course)
    selected = recommendation(opportunity_references=["OPP-SYN-001"], evidence=[evidence])
    response = run(service, RoadmapRequest(profile=profile("SKL-SYN-001"), recommendation=selected))

    assert [step.step_number for step in response.roadmap.steps] == list(range(1, len(response.roadmap.steps) + 1))
    assert [step.step_type.value for step in response.roadmap.steps] == ["training", "job_application"]
    assert response.roadmap.steps[1].prerequisites == [response.roadmap.steps[0].step_id]
    assert [item.source_id for item in response.roadmap.steps[0].evidence] == ["SRC-ROADMAP"]
    assert [item.source_id for item in response.roadmap.evidence] == ["SRC-ROADMAP"]


def test_repeated_generation_is_deterministic_and_malformed_request_is_rejected():
    service, _ = make_service()
    request = RoadmapRequest(profile=profile("SKL-SYN-001"), recommendation=recommendation())
    first, second = run(service, request), run(service, request)

    assert first.model_dump() == second.model_dump()
    with pytest.raises(ValueError):
        RoadmapRequest(profile=BeneficiaryProfile())
