"""Phase 15 runtime readiness and optional-provider tests."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.exceptions import ProviderConfigurationException
from app.main import create_application
from app.services.ai.gemini import GeminiStructuredExtractionProvider
from app.services.speech.providers import WhisperASRProvider


def test_production_rejects_cors_wildcard_and_malformed_runtime_settings():
    with pytest.raises(ValueError, match="ALLOWED_ORIGINS"):
        Settings(APP_ENV="production", ALLOWED_ORIGINS="*")
    with pytest.raises(ValueError, match="APP_ENV"):
        Settings(APP_ENV="demo")
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings(LOG_LEVEL="verbose")


def test_application_starts_and_exposes_health_and_openapi_without_optional_providers():
    # Creating the app does not construct Gemini or Whisper models.
    with TestClient(create_application()) as client:
        health = client.get("/v1/health")
        openapi = client.get("/openapi.json")
    assert health.status_code == 200
    assert health.json()["services"]["ai_extractor"] == "not_configured"
    assert health.json()["services"]["speech_transcriber"] == "not_configured"
    assert openapi.status_code == 200
    assert "/v1/livelihood/assess" in openapi.json()["paths"]


def test_missing_optional_gemini_and_unavailable_whisper_fail_explicitly_without_downloads(tmp_path):
    gemini = GeminiStructuredExtractionProvider(Settings(GEMINI_API_KEY=""))
    with pytest.raises(ProviderConfigurationException):
        asyncio.run(gemini.extract_json("ignored"))

    whisper = WhisperASRProvider(Settings(ASR_MODEL_PATH=str(tmp_path / "not-provisioned")))
    with pytest.raises(ProviderConfigurationException):
        asyncio.run(whisper.transcribe(b"audio", "wav", "hi"))
