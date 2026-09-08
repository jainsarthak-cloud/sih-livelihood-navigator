"""
JSONL (JSON Lines) file loader — reads a .jsonl file line-by-line,
validates each line against a Pydantic model, returns a LoadResult.

JSONL is preferred for large operational datasets (opportunities, market data)
because records can be streamed without loading the entire file into memory.

Format: one JSON object per line, blank lines are skipped.

Never raises on invalid individual records.
All errors are collected into LoadResult.errors for clear reporting.
"""

import json
from pathlib import Path
from typing import Generic, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.data.loaders.base import BaseDataLoader, LoadResult, RecordError

T = TypeVar("T", bound=BaseModel)


class JSONLFileLoader(BaseDataLoader[T], Generic[T]):
    """
    Loads a JSONL file where each line is a separate JSON record object.

    Expected file format (one object per line):
        {"field": "value", ...}
        {"field": "value", ...}

    Usage:
        loader = JSONLFileLoader(model=Opportunity, data_path=Path("data/seed/opportunities.jsonl"))
        result = loader.load()
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
            lines = self.data_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            result.errors.append(
                RecordError(index=-1, raw=None, reason=f"Cannot read file: {exc}")
            )
            return result

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue  # skip blank lines

            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                result.errors.append(
                    RecordError(
                        index=line_num,
                        raw=stripped[:200],
                        reason=f"Malformed JSON on line {line_num}: {exc}",
                    )
                )
                continue

            record, error = self.validate_record(raw, line_num)
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
                reason=f"Line {index} is not a JSON object (got {type(raw).__name__!r})",
            )
        try:
            record = self.model.model_validate(raw)
            return record, None
        except ValidationError as exc:
            return None, RecordError(
                index=index,
                raw=raw,
                reason=f"Validation failed on line {index}: {exc}",
            )
