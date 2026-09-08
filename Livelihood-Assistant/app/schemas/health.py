"""Health check response models."""

from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Overall health status of service")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Running environment (development/staging/production)")
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Subsystem registration and availability status",
    )
