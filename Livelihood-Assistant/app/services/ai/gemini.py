"""Minimal Gemini JSON provider adapter used only for language extraction."""

from abc import ABC, abstractmethod
import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings, settings
from app.core.exceptions import ProviderConfigurationException, ProviderResponseException


class BaseStructuredExtractionProvider(ABC):
    """Provider boundary so callers can use a mock or future model adapter."""

    provider_name: str = "unknown"
    model_name: str = "unknown"

    @abstractmethod
    async def extract_json(self, prompt: str) -> dict[str, Any]:
        """Return a parsed JSON object; callers still validate its schema."""


class GeminiStructuredExtractionProvider(BaseStructuredExtractionProvider):
    """Gemini REST adapter with JSON-only generation and no SDK dependency."""

    provider_name = "gemini"

    def __init__(self, config: Settings = settings):
        self._api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_MODEL
        self._timeout = config.GEMINI_TIMEOUT_SECONDS

    async def extract_json(self, prompt: str) -> dict[str, Any]:
        if not self._api_key:
            raise ProviderConfigurationException("Gemini")
        return await asyncio.to_thread(self._request, prompt)

    def _request(self, prompt: str) -> dict[str, Any]:
        body = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
        }).encode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self._api_key}"
        request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self._timeout) as response:  # nosec B310 - fixed Google endpoint
                payload = json.loads(response.read().decode("utf-8"))
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            output = json.loads(text)
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError, OSError):
            # Do not include provider content, URL, or credentials in errors.
            raise ProviderResponseException("Gemini") from None
        if not isinstance(output, dict):
            raise ProviderResponseException("Gemini")
        return output
