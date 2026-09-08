"""
Enhanced base repository interface.

Adds find_by_field, exists, and count to the original get_by_id / list_all / add
contract so that domain repositories can provide richer query capability
without depending directly on a specific storage backend.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Generic base repository defining the storage contract.

    Implementations may back this with:
    - In-memory dict (prototype / tests)
    - JSON file store
    - SQLAlchemy ORM session
    - MongoDB collection

    The recommendation engine must depend ONLY on this interface,
    never on a concrete implementation.
    """

    @abstractmethod
    def get_by_id(self, item_id: str) -> Optional[T]:
        """Fetch entity by unique canonical identifier."""

    @abstractmethod
    def list_all(self) -> List[T]:
        """Return all entities currently held in the repository."""

    @abstractmethod
    def add(self, item: T) -> T:
        """
        Add a new entity.

        Raises ValueError if an entity with the same ID already exists.
        Use add_or_replace() for upsert semantics.
        """

    @abstractmethod
    def add_or_replace(self, item_id: str, item: T) -> T:
        """Insert or overwrite an entity by ID (upsert semantics)."""

    @abstractmethod
    def exists(self, item_id: str) -> bool:
        """Return True if an entity with item_id is present."""

    @abstractmethod
    def count(self) -> int:
        """Return the total number of entities in the repository."""

    @abstractmethod
    def find_by_field(self, field: str, value: Any) -> List[T]:
        """
        Return all entities where getattr(entity, field) == value.

        Raises AttributeError if the field does not exist on the model.
        Returns an empty list if no entities match.
        """

    @abstractmethod
    def clear(self) -> None:
        """Remove all entities.  Primarily used in tests."""
