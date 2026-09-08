"""Unit tests for Phase 2 Canonical Domain Schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.common import (
    EducationLevel,
    EmploymentPreference,
    Gender,
    GeographicLocation,
    ProfileSource,
    SourceEvidence,
    SourceType,
    VerificationStatus,
)
from app.schemas.course import NSQFCourse
from app.schemas.eligibility import (
    CriterionResult,
    EligibilityResult,
    EligibilityStatus,
)
from app.schemas.occupation import EmploymentType, Occupation
from app.schemas.opportunity import (
    Opportunity,
    OpportunityLifecycle,
    OpportunityType,
)
from app.schemas.profile import (
    BeneficiaryProfile,
    EducationEntry,
    WorkHistoryEntry,
)
from app.schemas.recommendation import (
    PathwayType,
    Recommendation,
    ScoreBreakdown,
)
from app.schemas.roadmap import (
    Roadmap,
    RoadmapStep,
    StepStatus,
    StepType,
)
from app.schemas.skill import (
    GapStatus,
    PriorityLevel,
    RawSkill,
    Skill,
    SkillCategory,
    SkillGap,
    SkillProficiency,
    SkillSource,
)


# 1. Beneficiary Profile Tests
def test_valid_beneficiary_profile():
    """Verify fully populated beneficiary profile."""
    profile = BeneficiaryProfile(
        beneficiary_id="BEN-2026-001",
        age=24,
        gender=Gender.FEMALE,
        community="SC",
        education_level=EducationLevel.SECONDARY_10TH,
        education_field="General",
        location=GeographicLocation(
            state="Uttar Pradesh",
            district="Varanasi",
            block="Kashi Vidyapeeth",
            village="Shivpur",
            pincode="221002",
            latitude=25.3176,
            longitude=82.9739,
        ),
        current_occupation="Apparel Stitching Helper",
        current_income_range="< 1.0 Lakh",
        normalized_skills=[
            Skill(
                skill_id="SKL-APP-001",
                name="Basic Stitching",
                category=SkillCategory.TECHNICAL,
                proficiency=SkillProficiency.INTERMEDIATE,
            )
        ],
        traditional_skills=["Zari embroidery"],
        interests=["Fashion design", "Boutique management"],
        aspirations=["Self-employed boutique owner"],
        employment_preference=EmploymentPreference.SELF_EMPLOYMENT,
        willingness_to_travel=True,
        max_travel_distance_km=15.0,
        preferred_language="hi",
        profile_completion_pct=85.0,
        profile_source=ProfileSource.VOICE_INTERVIEW,
    )
    assert profile.beneficiary_id == "BEN-2026-001"
    assert profile.gender == Gender.FEMALE
    assert profile.education_level == EducationLevel.SECONDARY_10TH
    assert profile.location.district == "Varanasi"
    assert len(profile.normalized_skills) == 1
    assert profile.profile_completion_pct == 85.0


def test_incomplete_beneficiary_profile_with_unknowns():
    """Verify that unknown real-world data is represented explicitly without forcing fake values."""
    profile = BeneficiaryProfile(
        beneficiary_id="BEN-PARTIAL-002",
        preferred_language="hi",
        # All other fields remain optional/unknown
    )
    assert profile.gender == Gender.UNKNOWN
    assert profile.education_level == EducationLevel.UNKNOWN
    assert profile.employment_preference == EmploymentPreference.UNKNOWN
    assert profile.profile_source == ProfileSource.UNKNOWN
    assert profile.age is None
    assert profile.location is None
    assert profile.normalized_skills == []


# 2. Skill & Raw Skill Tests
def test_raw_vs_normalized_skill_representation():
    """Verify mapping of raw vernacular skill phrases to a canonical skill."""
    raw1 = RawSkill(
        raw_text="silai ka kaam karti hoon",
        language="hi",
        extracted_confidence=0.92,
        context="Main pichle do saal se ghar pe silai ka kaam karti hoon.",
    )
    raw2 = RawSkill(
        raw_text="stitching and alteration",
        language="en",
        extracted_confidence=0.88,
    )

    canonical_skill = Skill(
        skill_id="SKL-TEX-002",
        name="Garment Construction and Stitching",
        aliases=["Tailoring", "Silai", "Sewing Machine Operation"],
        category=SkillCategory.TECHNICAL,
        proficiency=SkillProficiency.INTERMEDIATE,
        source=SkillSource.INFERRED_FROM_WORK,
        confidence=0.90,
        mapped_raw_skills=[raw1, raw2],
    )
    assert canonical_skill.skill_id == "SKL-TEX-002"
    assert len(canonical_skill.mapped_raw_skills) == 2
    assert canonical_skill.mapped_raw_skills[0].raw_text == "silai ka kaam karti hoon"
    assert "Silai" in canonical_skill.aliases


def test_skill_gap_with_unknown_proficiency():
    """Verify skill gap model handles unknown baseline proficiency explicitly."""
    gap = SkillGap(
        skill_id="SKL-SOL-004",
        skill_name="Solar Inverter Wiring",
        current_proficiency=SkillProficiency.UNKNOWN,
        target_proficiency=SkillProficiency.ADVANCED,
        gap_status=GapStatus.MISSING,
        priority=PriorityLevel.HIGH,
    )
    assert gap.current_proficiency == SkillProficiency.UNKNOWN
    assert gap.gap_status == GapStatus.MISSING
    assert gap.priority == PriorityLevel.HIGH


# 3. Occupation Tests
def test_valid_occupation():
    """Verify canonical occupation creation."""
    occupation = Occupation(
        occupation_id="OCC-SOL-001",
        name="Solar PV System Installer",
        aliases=["Rooftop Solar Technician", "Solar Panel Installer"],
        sector="Green Jobs",
        description="Installs and commissions solar photovoltaic systems on rooftops.",
        required_skills=["SKL-ELE-001", "SKL-SOL-004"],
        nsqf_qualification_ids=["ELE/Q1401"],
        employment_type=EmploymentType.FULL_TIME,
    )
    assert occupation.occupation_id == "OCC-SOL-001"
    assert occupation.sector == "Green Jobs"
    assert "ELE/Q1401" in occupation.nsqf_qualification_ids


# 4. NSQF Course Tests
def test_valid_nsqf_course():
    """Verify NSQF course creation with validated level and hours."""
    course = NSQFCourse(
        course_id="CRS-NSQF-401",
        course_name="Solar PV Installation & Maintenance",
        qualification_name="Solar PV System Installer",
        qp_code="SGJ/Q0101",
        nsqf_level=4,
        sector="Green Jobs",
        job_roles=["Solar PV Installer"],
        required_education=EducationLevel.SECONDARY_10TH,
        required_skills=["Basic Electrical Knowledge"],
        acquired_skills=["Solar PV Assembly", "Grid Connection", "Safety Protocol"],
        duration_hours=200,
    )
    assert course.nsqf_level == 4
    assert course.duration_hours == 200
    assert course.required_education == EducationLevel.SECONDARY_10TH


def test_invalid_nsqf_level():
    """Verify NSQF levels outside 1..10 raise ValidationError."""
    with pytest.raises(ValidationError):
        NSQFCourse(
            course_id="INVALID",
            course_name="Invalid Level Course",
            qualification_name="Invalid",
            nsqf_level=12,  # Invalid
            sector="General",
        )

    with pytest.raises(ValidationError):
        NSQFCourse(
            course_id="INVALID-0",
            course_name="Zero Level Course",
            qualification_name="Invalid",
            nsqf_level=0,  # Invalid
            sector="General",
        )


# 5. Eligibility Tests
def test_unknown_eligibility_representation():
    """Verify eligibility model preserves UNKNOWN status when criteria cannot be verified."""
    crit_caste = CriterionResult(
        criterion_id="CRIT-SC-01",
        name="Scheduled Caste Community Verification",
        status=EligibilityStatus.ELIGIBLE,
        reason="Beneficiary self-reported SC community under PM-AJAY mandate.",
    )
    crit_income = CriterionResult(
        criterion_id="CRIT-INC-02",
        name="Annual Family Income Threshold",
        status=EligibilityStatus.UNKNOWN,
        reason="Income certificate or self-declaration is not yet collected.",
    )

    eligibility = EligibilityResult(
        scheme_name="PM-AJAY Skill Grant",
        status=EligibilityStatus.UNKNOWN,  # Must NOT assume ELIGIBLE
        overall_score=None,
        matched_criteria=[crit_caste],
        unmet_criteria=[],
        unknown_criteria=[crit_income],
        explanation="Income criteria is unknown; further documentation is required before final eligibility determination.",
    )
    assert eligibility.status == EligibilityStatus.UNKNOWN
    assert len(eligibility.unknown_criteria) == 1
    assert eligibility.overall_score is None


# 6. Opportunity Tests
def test_valid_opportunity_and_lifecycle():
    """Verify opportunity model and lifecycle status representation."""
    now = datetime.now(timezone.utc)
    opp = Opportunity(
        opportunity_id="OPP-VAR-101",
        title="Apprentice Solar Technician",
        opportunity_type=OpportunityType.APPRENTICESHIP,
        sector="Green Jobs",
        location=GeographicLocation(state="Uttar Pradesh", district="Varanasi"),
        collected_at=now,
        verification_status=VerificationStatus.VERIFIED,
        lifecycle_status=OpportunityLifecycle.ACTIVE,
        financial_assistance="Stipend: ₹8,500/month",
    )
    assert opp.opportunity_id == "OPP-VAR-101"
    assert opp.lifecycle_status == OpportunityLifecycle.ACTIVE
    assert opp.collected_at.tzinfo is not None

    # Test all lifecycle states can be set explicitly
    for status in [
        OpportunityLifecycle.REPORTED,
        OpportunityLifecycle.VERIFIED,
        OpportunityLifecycle.ACTIVE,
        OpportunityLifecycle.EXPIRED,
        OpportunityLifecycle.FILLED,
    ]:
        opp.lifecycle_status = status
        assert opp.lifecycle_status == status


# 7. Recommendation Tests
def test_valid_recommendation_and_score_bounds():
    """Verify recommendation model with score breakdown and bounds."""
    rec = Recommendation(
        recommendation_id="REC-001",
        pathway_type=PathwayType.SKILL_TRAINING,
        occupation_reference="OCC-SOL-001",
        course_reference="CRS-NSQF-401",
        overall_score=0.88,
        score_breakdown=ScoreBreakdown(
            skill_match_score=0.85,
            local_demand_score=0.90,
            eligibility_score=0.95,
            preference_alignment_score=0.82,
        ),
        confidence=0.90,
        explanation="Strong local demand in Varanasi for Solar PV Installers matching candidate baseline skills.",
    )
    assert rec.overall_score == 0.88
    assert rec.score_breakdown.local_demand_score == 0.90
    assert rec.pathway_type == PathwayType.SKILL_TRAINING

    # Test score out of bounds
    with pytest.raises(ValidationError):
        Recommendation(
            recommendation_id="REC-INVALID",
            pathway_type=PathwayType.DIRECT_EMPLOYMENT,
            overall_score=1.5,  # Invalid > 1.0
            score_breakdown=ScoreBreakdown(skill_match_score=0.8, local_demand_score=0.8),
            confidence=0.8,
            explanation="Invalid score",
        )


# 8. Roadmap Tests
def test_valid_roadmap_and_step_ordering():
    """Verify roadmap model with ordered milestones."""
    step1 = RoadmapStep(
        step_id="STP-1",
        step_number=1,
        title="Enroll in NSQF Level 4 Solar Course",
        description="Join accredited NSDC training center in Varanasi under PM-AJAY subsidy.",
        step_type=StepType.TRAINING,
        status=StepStatus.PENDING,
        estimated_duration_weeks=12,
    )
    step2 = RoadmapStep(
        step_id="STP-2",
        step_number=2,
        title="Pass Assessment & Receive Certificate",
        description="Undergo assessment by Skill Council for Green Jobs.",
        step_type=StepType.CERTIFICATION,
        status=StepStatus.PENDING,
        estimated_duration_weeks=2,
        prerequisites=["STP-1"],
    )

    roadmap = Roadmap(
        roadmap_id="RDM-2026-001",
        beneficiary_id="BEN-2026-001",
        target_occupation_id="OCC-SOL-001",
        target_pathway=PathwayType.SKILL_TRAINING,
        steps=[step1, step2],
        total_estimated_duration_weeks=14,
    )
    assert len(roadmap.steps) == 2
    assert roadmap.steps[0].step_number == 1
    assert roadmap.steps[1].prerequisites == ["STP-1"]
    assert roadmap.total_estimated_duration_weeks == 14


# 9. Source / Evidence & Coordinate Tests
def test_source_evidence_metadata_and_tz():
    """Verify SourceEvidence model requires timezone-aware datetime."""
    now_utc = datetime.now(timezone.utc)
    evidence = SourceEvidence(
        source_id="EVD-001",
        source_type=SourceType.PM_AJAY_GUIDELINES,
        source_name="Ministry of Social Justice & Empowerment Guidelines 2024",
        source_url="https://socialjustice.gov.in/schemes/pm-ajay",
        collected_at=now_utc,
        verification_status=VerificationStatus.VERIFIED,
    )
    assert evidence.source_id == "EVD-001"
    assert evidence.collected_at.tzinfo is not None

    # Naive datetime should fail validation
    naive_dt = datetime.now()
    if naive_dt.tzinfo is None:
        with pytest.raises(ValidationError):
            SourceEvidence(
                source_id="EVD-NAIVE",
                source_type=SourceType.OTHER,
                source_name="Naive Test",
                collected_at=naive_dt,
            )


def test_invalid_coordinates():
    """Verify latitude [-90, 90] and longitude [-180, 180] bounds."""
    with pytest.raises(ValidationError):
        GeographicLocation(state="UP", district="Varanasi", latitude=95.0)  # > 90

    with pytest.raises(ValidationError):
        GeographicLocation(state="UP", district="Varanasi", longitude=-185.0)  # < -180


def test_invalid_percentages_and_ages():
    """Verify bounds for profile completion percentage and age."""
    with pytest.raises(ValidationError):
        BeneficiaryProfile(age=150)  # > 130

    with pytest.raises(ValidationError):
        BeneficiaryProfile(profile_completion_pct=105.0)  # > 100.0


def test_json_roundtrip_serialization():
    """Verify JSON serialization and deserialization retains fidelity."""
    profile = BeneficiaryProfile(
        beneficiary_id="BEN-RT-01",
        age=22,
        gender=Gender.MALE,
        education_level=EducationLevel.ITI,
        location=GeographicLocation(state="Bihar", district="Patna"),
        normalized_skills=[
            Skill(skill_id="S1", name="Electrician", category=SkillCategory.TECHNICAL)
        ],
    )
    json_str = profile.model_dump_json()
    reloaded = BeneficiaryProfile.model_validate_json(json_str)
    assert reloaded.beneficiary_id == profile.beneficiary_id
    assert reloaded.education_level == EducationLevel.ITI
    assert reloaded.location.district == "Patna"
    assert reloaded.normalized_skills[0].name == "Electrician"
