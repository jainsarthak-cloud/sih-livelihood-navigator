"""Integration tests for all initial API routes."""

from fastapi.testclient import TestClient


def test_profile_extract_endpoint(client: TestClient):
    """Verify POST /v1/profile/extract safely reports an unconfigured Gemini provider."""
    payload = {
        "raw_text": "Mera naam Rajesh hai, 10th pass hoon, solar work sikhna chahta hoon.",
        "language": "hi",
        "source": "voice_interview",
    }
    response = client.post("/v1/profile/extract", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["error"]["details"] == {"provider": "Gemini"}


def test_profile_extract_validation_error(client: TestClient):
    """Verify POST /v1/profile/extract returns 422 on invalid payload."""
    response = client.post("/v1/profile/extract", json={})
    assert response.status_code == 422


def test_language_validation_rejects_unsupported_codes_before_provider_calls(client: TestClient):
    profile = client.post("/v1/profile/extract", json={"raw_text": "bonjour", "language": "fr"})
    interview = client.post("/v1/interview/turn", json={"user_text": "bonjour", "language": "fr"})
    speech = client.post("/v1/speech/transcribe", json={
        "audio_content_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
        "language_code": "fr", "audio_format": "wav",
    })
    assert profile.status_code == interview.status_code == speech.status_code == 422


def test_interview_turn_endpoint_reports_unconfigured_extractor_safely(client: TestClient):
    response = client.post("/v1/interview/turn", json={"user_text": "मैं सिलाई करती हूँ", "language": "hi"})
    assert response.status_code == 503
    assert response.json()["error"]["details"] == {"provider": "Gemini"}


def test_interview_turn_validation_error(client: TestClient):
    response = client.post("/v1/interview/turn", json={"user_text": ""})
    assert response.status_code == 422


def test_channel_interact_endpoint_validates_external_contract_before_provider_use(client: TestClient):
    invalid = client.post("/v1/channel/interact", json={
        "channel": "future_connector", "external_user_reference": "opaque", "language": "fr", "text": "bonjour",
    })
    assert invalid.status_code == 422

    # A syntactically valid text interaction reaches the existing Phase 6
    # provider boundary; it remains unconfigured in the test environment.
    valid = client.post("/v1/channel/interact", json={
        "channel": "future_connector", "external_user_reference": "opaque", "language": "hi", "text": "मैं सिलाई करती हूँ",
    })
    assert valid.status_code == 503
    assert valid.json()["error"]["details"] == {"provider": "Gemini"}


def test_livelihood_assessment_endpoint_works_without_llm_or_asr(client: TestClient):
    response = client.post("/v1/livelihood/assess", json={
        "profile": {
            "education_level": "primary", "traditional_skills": ["silai"],
            "employment_preference": "wage_employment",
            "location": {"state": "Demo State", "district": "Demo District"},
        }
    })
    assert response.status_code == 200
    assert response.json()["metadata"]["deterministic"] is True


def test_livelihood_assessment_validation_error(client: TestClient):
    response = client.post("/v1/livelihood/assess", json={"profile": {}, "max_recommendations": 4})
    assert response.status_code == 422


def test_profile_validate_endpoint(client: TestClient):
    """Verify POST /v1/profile/validate handles valid payload and returns 501 placeholder."""
    payload = {
        "profile": {
            "candidate_id": "cand_001",
            "demographics": {"name": "Aman", "community": "SC", "age": 21},
        },
        "scheme": "PM-AJAY",
    }
    response = client.post("/v1/profile/validate", json=payload)
    assert response.status_code == 501
    data = response.json()
    assert data["success"] is False
    assert "ProfileExtractionService.validate_profile" in data["error"]["message"]


def test_recommendations_endpoint(client: TestClient):
    """Verify POST /v1/recommendations returns deterministic Phase 5 results."""
    payload = {
        "profile": {
            "candidate_id": "cand_001",
            "existing_skills": ["welding"],
        },
        "target_sector": "Automotive",
        "max_recommendations": 3,
    }
    response = client.post("/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["recommendations"] == []


def test_speech_transcribe_endpoint(client: TestClient):
    """Verify POST /v1/speech/transcribe reports missing local ASR configuration safely."""
    payload = {
        "audio_content_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
        "language_code": "hi",
        "audio_format": "wav",
    }
    response = client.post("/v1/speech/transcribe", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["error"]["details"] == {"provider": "Whisper ASR"}


def test_opportunities_parse_endpoint(client: TestClient):
    """Verify POST /v1/opportunities/parse does not infer an opportunity from raw text."""
    payload = {
        "raw_content": "PM-AJAY Special Drive: Free NSQF Level 4 training in Lucknow.",
        "scheme_context": "PM-AJAY",
    }
    response = client.post("/v1/opportunities/parse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "structured_record_required"
    assert data["parsed_opportunities"] == []


def test_opportunities_match_endpoint_excludes_reported_records_by_default(client: TestClient):
    response = client.post("/v1/opportunities/match", json={
        "profile": {
            "employment_preference": "apprenticeship",
            "location": {"state": "Demo State", "district": "Demo District"},
            "traditional_skills": ["silai"],
        }
    })
    assert response.status_code == 200
    ids = [item["opportunity"]["opportunity_id"] for item in response.json()["matches"]]
    assert ids == ["OPP-SYN-001"]
    assert "OPP-SYN-002" not in ids


def test_market_demand_endpoint(client: TestClient):
    """Verify POST /v1/market/demand returns repository-scoped observation evidence."""
    payload = {
        "state": "Demo State",
        "district": "Demo District",
    }
    response = client.post("/v1/market/demand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["top_sectors"][0]["active_opportunity_count"] == 1


def test_roadmap_endpoint(client: TestClient):
    """Verify POST /v1/roadmap safely reports a canonical target absent from the seed repository."""
    payload = {
        "profile": {
            "beneficiary_id": "cand_001",
            "traditional_skills": ["basic electrician"],
        },
        "target_occupation_id": "OCC-SOL-001",
        "timeframe_months": 6,
    }
    response = client.post("/v1/roadmap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "target_not_found"
    assert data["roadmap"] is None


def test_profile_validate_validation_error(client: TestClient):
    """Verify POST /v1/profile/validate returns 422 on missing profile."""
    response = client.post("/v1/profile/validate", json={})
    assert response.status_code == 422


def test_recommendations_validation_error(client: TestClient):
    """Verify POST /v1/recommendations returns 422 on invalid max_recommendations or missing profile."""
    # Missing profile
    response = client.post("/v1/recommendations", json={"max_recommendations": 5})
    assert response.status_code == 422

    # Out of bounds max_recommendations
    response = client.post(
        "/v1/recommendations",
        json={"profile": {"candidate_id": "c1"}, "max_recommendations": 99},
    )
    assert response.status_code == 422


def test_speech_transcribe_validation_error(client: TestClient):
    """Verify POST /v1/speech/transcribe returns 422 on wrong types."""
    response = client.post(
        "/v1/speech/transcribe",
        json={"audio_content_base64": 12345},  # should be str
    )
    assert response.status_code == 422


def test_opportunities_parse_validation_error(client: TestClient):
    """Verify POST /v1/opportunities/parse returns 422 on missing raw_content."""
    response = client.post("/v1/opportunities/parse", json={})
    assert response.status_code == 422


def test_market_demand_validation_error(client: TestClient):
    """Verify POST /v1/market/demand returns 422 on missing state/district."""
    response = client.post("/v1/market/demand", json={"state": "Uttar Pradesh"})
    assert response.status_code == 422


def test_roadmap_validation_error(client: TestClient):
    """Verify POST /v1/roadmap returns 422 on missing target_role."""
    response = client.post(
        "/v1/roadmap",
        json={"profile": {"candidate_id": "c1"}},
    )
    assert response.status_code == 422
