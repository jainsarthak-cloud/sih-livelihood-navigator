"""
JSON file loader — reads a .json file containing a list of objects,
validates each against a Pydantic model, returns a LoadResult.

Never raises on invalid individual records.
All errors are collected into LoadResult.errors for clear reporting.
"""

import json
from pathlib import Path
from typing import Generic, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.data.loaders.base import BaseDataLoader, LoadResult, RecordError

T = TypeVar("T", bound=BaseModel)


class JSONFileLoader(BaseDataLoader[T], Generic[T]):
    """
    Loads a JSON file containing a top-level list of record objects.

    Expected file format:
        [
            { "field": "value", ... },
            ...
        ]

    Usage:
        loader = JSONFileLoader(model=Skill, data_path=Path("data/seed/skills.json"))
        result = loader.load()
        for err in result.errors:
            print(f"  Record #{err.index}: {err.reason}")
    """

    def __init__(self, model: Type[T], data_path: Path):
        super().__init__(data_path=data_path)
        self.model = model

    def load(self) -> LoadResult[T]:
        result: LoadResult[T] = LoadResult()

        if not self.data_path or not self.data_path.exists():
            result.errors.append(
                RecordError(
                    index=-1,
                    raw=None,
                    reason=f"File not found: {self.data_path}",
                )
            )
            return result

        try:
            raw_text = self.data_path.read_text(encoding="utf-8")
        except OSError as exc:
            result.errors.append(
                RecordError(index=-1, raw=None, reason=f"Cannot read file: {exc}")
            )
            return result

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            result.errors.append(
                RecordError(
                    index=-1,
                    raw=raw_text[:200],
                    reason=f"Malformed JSON: {exc}",
                )
            )
            return result

        if not isinstance(data, list):
            result.errors.append(
                RecordError(
                    index=-1,
                    raw=type(data).__name__,
                    reason=(
                        f"Expected a JSON array at top level, "
                        f"got {type(data).__name__!r}"
                    ),
                )
            )
            return result

        for idx, raw in enumerate(data):
            record, error = self.validate_record(raw, idx)
            if record is not None:
                result.records.append(record)
            else:
                result.errors.append(error)

        return result

    def validate_record(
        self, raw: dict, index: int
    ) -> Tuple[Optional[T], Optional[RecordError]]:
        if not isinstance(raw, dict):
            return None, RecordError(
                index=index,
                raw=raw,
                reason=f"Record at index {index} is not a JSON object (got {type(raw).__name__!r})",
            )
        try:
            record = self.model.model_validate(raw)
            return record, None
        except ValidationError as exc:
            return None, RecordError(
                index=index,
                raw=raw,
                reason=f"Validation failed at index {index}: {exc}",
            )
