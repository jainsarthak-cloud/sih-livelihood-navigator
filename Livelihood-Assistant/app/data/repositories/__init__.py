"""Data repositories package."""

from app.data.repositories.base import BaseRepository
from app.data.repositories.memory_repository import InMemoryRepository
from app.data.repositories.domain_repositories import (
    CourseRepository,
    OccupationRepository,
    OpportunityRepository,
    ProviderRepository,
    SkillRepository,
)

__all__ = [
    "BaseRepository",
    "InMemoryRepository",
    "SkillRepository",
    "OccupationRepository",
    "CourseRepository",
    "OpportunityRepository",
    "ProviderRepository",
]
