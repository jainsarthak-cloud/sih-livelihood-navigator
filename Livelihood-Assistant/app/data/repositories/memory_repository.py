"""
In-memory repository — concrete implementation of BaseRepository.

Backed by a plain dict[str, T].  Used as the prototype store for Phase 3.
Suitable for unit tests and the AI engine prototype.
Thread safety: not guaranteed for concurrent writes; acceptable for single-process prototype.

Future migration path:
  Replace InMemoryRepository with SQLAlchemyRepository or MongoRepository
  by implementing the same BaseRepository interface.  The rest of the codebase
  does not change because it depends only on BaseRepository.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from app.data.repositories.base import BaseRepository

T = TypeVar("T")


class InMemoryRepository(BaseRepository[T], Generic[T]):
    """
    Generic in-memory repository backed by dict[str, T].

    The `id_field` constructor argument names the attribute used as the
    primary key (e.g. 'skill_id', 'occupation_id').
    """

    def __init__(self, id_field: str = "id"):
        self._store: Dict[str, T] = {}
        self._id_field = id_field

    def _get_id(self, item: T) -> str:
        item_id = getattr(item, self._id_field, None)
        if item_id is None:
            raise ValueError(
                f"Entity does not have attribute {self._id_field!r}: {item}"
            )
        return str(item_id)

    def get_by_id(self, item_id: str) -> Optional[T]:
        return self._store.get(item_id)

    def list_all(self) -> List[T]:
        return list(self._store.values())

    def add(self, item: T) -> T:
        item_id = self._get_id(item)
        if item_id in self._store:
            raise ValueError(
                f"Entity with {self._id_field}={item_id!r} already exists. "
                "Use add_or_replace() for upsert semantics."
            )
        self._store[item_id] = item
        return item

    def add_or_replace(self, item_id: str, item: T) -> T:
        self._store[item_id] = item
        return item

    def exists(self, item_id: str) -> bool:
        return item_id in self._store

    def count(self) -> int:
        return len(self._store)

    def find_by_field(self, field: str, value: Any) -> List[T]:
        results = []
        for item in self._store.values():
            try:
                if getattr(item, field) == value:
                    results.append(item)
            except AttributeError:
                raise AttributeError(
                    f"Field {field!r} does not exist on {type(item).__name__}"
                )
        return results

    def clear(self) -> None:
        self._store.clear()
