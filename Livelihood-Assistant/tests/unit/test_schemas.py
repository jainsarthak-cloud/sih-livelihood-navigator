"""Unit tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError
from app.schemas.profile import BeneficiaryProfile, ProfileExtractRequest
from app.schemas.recommendation import RecommendationRequest
from app.schemas.course import NSQFCourse
from app.schemas.health import HealthResponse


def test_health_response_schema():
    """Verify HealthResponse schema validation."""
    response = HealthResponse(
        status="healthy",
        app_name="TestApp",
        version="1.0.0",
        environment="test",
        services={"api": "online"},
    )
    assert response.status == "healthy"
    assert response.services["api"] == "online"


def test_beneficiary_profile_defaults():
    """Verify BeneficiaryProfile defaults and structure."""
    profile = BeneficiaryProfile(
        beneficiary_id="cand_123",
        age=24,
        community="SC",
        traditional_skills=["carpentry"],
    )
    assert profile.beneficiary_id == "cand_123"
    assert profile.community == "SC"
    assert "carpentry" in profile.traditional_skills


def test_profile_extract_request_validation():
    """Verify ProfileExtractRequest validation rules."""
    req = ProfileExtractRequest(raw_text="Namaste, main ITI electrician hoon.")
    assert req.raw_text == "Namaste, main ITI electrician hoon."
    assert req.language == "hi"

    # raw_text is required
    with pytest.raises(ValidationError):
        ProfileExtractRequest()


def test_recommendation_request_validation():
    """Verify RecommendationRequest schema bounds."""
    profile = BeneficiaryProfile(beneficiary_id="c1")
    req = RecommendationRequest(profile=profile, max_recommendations=5)
    assert req.max_recommendations == 5

    # Out of bounds max_recommendations (> 20)
    with pytest.raises(ValidationError):
        RecommendationRequest(profile=profile, max_recommendations=50)


def test_nsqf_course_bounds():
    """Verify NSQF level boundary validation (1 to 10)."""
    course = NSQFCourse(
        course_id="CRS-001",
        course_name="Masonry Basics",
        qualification_name="Mason General",
        qp_code="CON/Q0101",
        nsqf_level=4,
        sector="Construction",
    )
    assert course.nsqf_level == 4

    # Invalid NSQF level
    with pytest.raises(ValidationError):
        NSQFCourse(
            course_id="INVALID",
            course_name="Invalid Role",
            qualification_name="Invalid",
            nsqf_level=12,
            sector="None",
        )
