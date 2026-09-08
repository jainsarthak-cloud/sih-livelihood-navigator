"""Unit tests for configuration management."""

from app.core.config import Settings


def test_default_settings():
    """Verify default settings initialization."""
    settings = Settings()
    assert settings.APP_NAME == "Livelihood-Assistant-AI"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.API_V1_PREFIX == "/v1"
    assert settings.PORT == 8000


def test_cors_origins_parsing():
    """Verify parsing of comma-separated CORS origins."""
    settings = Settings(ALLOWED_ORIGINS="http://localhost:3000, https://app.example.com")
    assert settings.ALLOWED_ORIGINS == ["http://localhost:3000", "https://app.example.com"]

    wildcard_settings = Settings(ALLOWED_ORIGINS="*")
    assert wildcard_settings.ALLOWED_ORIGINS == ["*"]
