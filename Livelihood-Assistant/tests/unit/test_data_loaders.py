"""
Unit tests for Phase 3 data loaders.

Covers:
- Valid JSON loading round-trip
- Malformed JSON syntax
- Malformed records (wrong Pydantic types)
- Duplicate ID detection by domain loaders
- Missing required fields caught by Pydantic
- JSONL loading (valid + mixed-invalid lines)
- File-not-found handling
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.data.loaders.base import LoadResult, RecordError
from app.data.loaders.domain_loaders import (
    CourseLoader,
    OccupationLoader,
    SkillLoader,
)
from app.data.loaders.json_loader import JSONFileLoader
from app.data.loaders.jsonl_loader import JSONLFileLoader
from app.schemas.skill import Skill
from app.schemas.occupation import Occupation


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _write_json(tmp_path: Path, data) -> Path:
    f = tmp_path / "test.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


def _write_jsonl(tmp_path: Path, lines: list) -> Path:
    f = tmp_path / "test.jsonl"
    f.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")
    return f


def _minimal_skill(skill_id: str = "SKL-TEST-001") -> dict:
    return {"skill_id": skill_id, "name": "Test Skill"}


def _minimal_occupation(occ_id: str = "OCC-TEST-001") -> dict:
    return {"occupation_id": occ_id, "name": "Test Occupation", "sector": "Test Sector"}


# ─── JSONFileLoader tests ─────────────────────────────────────────────────────

class TestJSONFileLoader:
    def test_valid_records_load(self, tmp_path):
        fpath = _write_json(tmp_path, [_minimal_skill("SKL-A"), _minimal_skill("SKL-B")])
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert result.is_clean
        assert result.total_valid == 2
        assert result.total_invalid == 0
        assert {r.skill_id for r in result.records} == {"SKL-A", "SKL-B"}

    def test_malformed_json_syntax(self, tmp_path):
        fpath = tmp_path / "bad.json"
        fpath.write_text("{not valid json[[[", encoding="utf-8")
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert not result.is_clean
        assert result.total_valid == 0
        assert result.total_invalid == 1
        assert "Malformed JSON" in result.errors[0].reason

    def test_non_list_top_level(self, tmp_path):
        fpath = _write_json(tmp_path, {"single": "object"})
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert not result.is_clean
        assert "Expected a JSON array" in result.errors[0].reason

    def test_malformed_record_mixed_with_valid(self, tmp_path):
        data = [
            _minimal_skill("SKL-OK"),
            {"skill_id": "SKL-BAD", "name": 999},  # name must be str; int forces coercion, OK
            {"not_a_skill": True},                   # missing required skill_id → invalid
        ]
        fpath = _write_json(tmp_path, data)
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        # Record with int name is coerced by Pydantic (name: 999 → "999" is valid)
        # Record missing skill_id should fail
        assert result.total_invalid >= 1
        assert any("skill_id" in e.reason or "Validation failed" in e.reason
                   for e in result.errors)

    def test_file_not_found(self, tmp_path):
        loader = JSONFileLoader(model=Skill, data_path=tmp_path / "missing.json")
        result = loader.load()

        assert not result.is_clean
        assert result.errors[0].index == -1
        assert "not found" in result.errors[0].reason.lower()

    def test_non_object_element_in_array(self, tmp_path):
        fpath = _write_json(tmp_path, [_minimal_skill(), "not-an-object", 42])
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert result.total_valid == 1
        assert result.total_invalid == 2  # "not-an-object" and 42

    def test_empty_array(self, tmp_path):
        fpath = _write_json(tmp_path, [])
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert result.is_clean
        assert result.total_valid == 0

    def test_load_result_summary(self, tmp_path):
        fpath = _write_json(tmp_path, [_minimal_skill("SKL-A")])
        loader = JSONFileLoader(model=Skill, data_path=fpath)
        result = loader.load()
        summary = result.summary()

        assert "total_read=1" in summary
        assert "valid=1" in summary
        assert "invalid=0" in summary


# ─── JSONLFileLoader tests ─────────────────────────────────────────────────────

class TestJSONLFileLoader:
    def test_valid_jsonl(self, tmp_path):
        fpath = _write_jsonl(tmp_path, [_minimal_skill("SKL-L1"), _minimal_skill("SKL-L2")])
        loader = JSONLFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert result.is_clean
        assert result.total_valid == 2

    def test_blank_lines_skipped(self, tmp_path):
        fpath = tmp_path / "blank.jsonl"
        fpath.write_text(
            json.dumps(_minimal_skill("SKL-X")) + "\n\n\n" + json.dumps(_minimal_skill("SKL-Y")),
            encoding="utf-8",
        )
        loader = JSONLFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert result.total_valid == 2
        assert result.total_invalid == 0

    def test_malformed_line_collected_not_raised(self, tmp_path):
        fpath = tmp_path / "mixed.jsonl"
        fpath.write_text(
            json.dumps(_minimal_skill("SKL-GOOD")) + "\n"
            + "{{broken json}}\n"
            + json.dumps(_minimal_skill("SKL-ALSO-GOOD")),
            encoding="utf-8",
        )
        loader = JSONLFileLoader(model=Skill, data_path=fpath)
        result = loader.load()

        assert result.total_valid == 2
        assert result.total_invalid == 1
        assert "Malformed JSON" in result.errors[0].reason

    def test_file_not_found(self, tmp_path):
        loader = JSONLFileLoader(model=Skill, data_path=tmp_path / "nope.jsonl")
        result = loader.load()

        assert not result.is_clean
        assert "not found" in result.errors[0].reason.lower()


# ─── Domain loader duplicate-ID detection ────────────────────────────────────

class TestDomainLoaderDuplicateDetection:
    def test_skill_loader_detects_duplicate_ids(self, tmp_path):
        fpath = _write_json(
            tmp_path,
            [_minimal_skill("SKL-DUP"), _minimal_skill("SKL-DUP"), _minimal_skill("SKL-UNIQUE")],
        )
        loader = SkillLoader(data_path=fpath)
        result = loader.load()

        # Only first occurrence kept; second is an error
        assert result.total_valid == 2  # SKL-DUP (first) + SKL-UNIQUE
        assert result.total_invalid == 1
        assert "Duplicate" in result.errors[0].reason

    def test_occupation_loader_detects_duplicate_ids(self, tmp_path):
        fpath = _write_json(
            tmp_path,
            [_minimal_occupation("OCC-DUP"), _minimal_occupation("OCC-DUP")],
        )
        loader = OccupationLoader(data_path=fpath)
        result = loader.load()

        assert result.total_valid == 1
        assert result.total_invalid == 1
        assert "Duplicate" in result.errors[0].reason

    def test_course_loader_valid_no_duplicates(self, tmp_path):
        records = [
            {
                "course_id": "CRS-A",
                "course_name": "Course A",
                "qualification_name": "Qual A",
                "nsqf_level": 3,
                "sector": "Test",
            },
            {
                "course_id": "CRS-B",
                "course_name": "Course B",
                "qualification_name": "Qual B",
                "nsqf_level": 4,
                "sector": "Test",
            },
        ]
        fpath = _write_json(tmp_path, records)
        loader = CourseLoader(data_path=fpath)
        result = loader.load()

        assert result.is_clean
        assert result.total_valid == 2

    def test_missing_required_field(self, tmp_path):
        # Occupation requires 'sector'; omitting it should fail validation
        fpath = _write_json(tmp_path, [{"occupation_id": "OCC-NO-SECTOR", "name": "No Sector"}])
        loader = OccupationLoader(data_path=fpath)
        result = loader.load()

        assert result.total_invalid == 1
        assert "Validation failed" in result.errors[0].reason
