"""Pytest configuration and test fixtures."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """Provides a synchronous TestClient instance for API testing."""
    with TestClient(app) as test_client:
        yield test_client
