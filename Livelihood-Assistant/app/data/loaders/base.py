"""
Enhanced base data-loader interface.

Key contracts:
- load() returns a LoadResult — never raises on bad records; errors are collected.
- validate_record() must be implemented by each concrete loader.
- LoadResult carries per-record errors so callers can report them clearly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class RecordError:
    """A single record that failed loading or validation."""

    index: int
    raw: Any
    reason: str


@dataclass
class LoadResult(Generic[T]):
    """
    Result of a loader run.

    Never raises on individual bad records — every bad record is collected into
    `errors` so the caller can report them clearly without stopping execution.
    """

    records: List[T] = field(default_factory=list)
    errors: List[RecordError] = field(default_factory=list)

    @property
    def total_read(self) -> int:
        return len(self.records) + len(self.errors)

    @property
    def total_valid(self) -> int:
        return len(self.records)

    @property
    def total_invalid(self) -> int:
        return len(self.errors)

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return (
            f"total_read={self.total_read}, "
            f"valid={self.total_valid}, "
            f"invalid={self.total_invalid}"
        )


class BaseDataLoader(ABC, Generic[T]):
    """
    Abstract data loader for dataset ingestion.

    Concrete loaders must:
    1. Read a file (JSON / JSONL / CSV).
    2. Parse raw records.
    3. Validate each record against a Pydantic model via validate_record().
    4. Return a LoadResult — never silently drop invalid records.
    5. Preserve source/provenance information from the file.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path

    @abstractmethod
    def load(self) -> LoadResult[T]:
        """Load, parse, validate, and return a LoadResult."""

    @abstractmethod
    def validate_record(self, raw: dict, index: int) -> Tuple[Optional[T], Optional[RecordError]]:
        """
        Validate a single raw dict against the domain model.

        Returns (record, None) on success.
        Returns (None, RecordError) on failure.
        """
