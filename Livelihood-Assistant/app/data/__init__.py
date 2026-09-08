"""Data layer package."""

from app.data.loaders.base import BaseDataLoader, LoadResult, RecordError
from app.data.loaders.json_loader import JSONFileLoader
from app.data.loaders.jsonl_loader import JSONLFileLoader
from app.data.loaders.domain_loaders import (
    CourseLoader,
    OccupationLoader,
    OpportunityLoader,
    ProviderLoader,
    SkillLoader,
)
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
    # Loaders
    "BaseDataLoader",
    "LoadResult",
    "RecordError",
    "JSONFileLoader",
    "JSONLFileLoader",
    "SkillLoader",
    "OccupationLoader",
    "CourseLoader",
    "OpportunityLoader",
    "ProviderLoader",
    # Repositories
    "BaseRepository",
    "InMemoryRepository",
    "SkillRepository",
    "OccupationRepository",
    "CourseRepository",
    "OpportunityRepository",
    "ProviderRepository",
]
