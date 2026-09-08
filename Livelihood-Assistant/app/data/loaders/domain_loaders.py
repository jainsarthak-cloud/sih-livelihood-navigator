"""
Domain-specific data loaders with duplicate-ID detection.

Each loader wraps JSONFileLoader with:
- The correct Pydantic model type
- Domain-specific primary-key field extraction
- Duplicate canonical-ID detection (raises DuplicateIDError, collected in LoadResult)
"""

from pathlib import Path
from typing import Dict, List, Set

from app.data.loaders.base import LoadResult, RecordError
from app.data.loaders.json_loader import JSONFileLoader
from app.schemas.course import NSQFCourse
from app.schemas.occupation import Occupation
from app.schemas.opportunity import Opportunity
from app.schemas.provider import TrainingProvider
from app.schemas.skill import Skill


def _check_duplicates(
    records: list,
    id_field: str,
    result: "LoadResult",
) -> List:
    """
    Detect duplicate canonical IDs within a loaded record set.

    Duplicate records are removed from the valid set and added to
    LoadResult.errors with a clear message.  The first occurrence is kept.
    """
    seen: Dict[str, int] = {}  # id -> first-seen index
    clean = []
    for i, rec in enumerate(records):
        rid = getattr(rec, id_field, None)
        if rid is None:
            clean.append(rec)
            continue
        if rid in seen:
            result.errors.append(
                RecordError(
                    index=i,
                    raw={id_field: rid},
                    reason=(
                        f"Duplicate {id_field}={rid!r} at index {i}; "
                        f"first occurrence was at index {seen[rid]}."
                    ),
                )
            )
        else:
            seen[rid] = i
            clean.append(rec)
    return clean


class SkillLoader:
    """Loads canonical Skill records from a JSON file."""

    def __init__(self, data_path: Path):
        self._loader = JSONFileLoader(model=Skill, data_path=data_path)

    def load(self) -> LoadResult[Skill]:
        result = self._loader.load()
        result.records = _check_duplicates(result.records, "skill_id", result)
        return result


class OccupationLoader:
    """Loads canonical Occupation records from a JSON file."""

    def __init__(self, data_path: Path):
        self._loader = JSONFileLoader(model=Occupation, data_path=data_path)

    def load(self) -> LoadResult[Occupation]:
        result = self._loader.load()
        result.records = _check_duplicates(result.records, "occupation_id", result)
        return result


class CourseLoader:
    """Loads canonical NSQFCourse records from a JSON file."""

    def __init__(self, data_path: Path):
        self._loader = JSONFileLoader(model=NSQFCourse, data_path=data_path)

    def load(self) -> LoadResult[NSQFCourse]:
        result = self._loader.load()
        result.records = _check_duplicates(result.records, "course_id", result)
        return result


class OpportunityLoader:
    """Loads canonical Opportunity records from a JSON file."""

    def __init__(self, data_path: Path):
        self._loader = JSONFileLoader(model=Opportunity, data_path=data_path)

    def load(self) -> LoadResult[Opportunity]:
        result = self._loader.load()
        result.records = _check_duplicates(result.records, "opportunity_id", result)
        return result


class ProviderLoader:
    """Loads canonical TrainingProvider records from a JSON file."""

    def __init__(self, data_path: Path):
        self._loader = JSONFileLoader(model=TrainingProvider, data_path=data_path)

    def load(self) -> LoadResult[TrainingProvider]:
        result = self._loader.load()
        result.records = _check_duplicates(result.records, "provider_id", result)
        return result
