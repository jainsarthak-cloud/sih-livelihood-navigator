"""
Tests for synthetic seed data integrity.

Verifies:
- All seed files load cleanly via domain loaders
- Every record has is_synthetic field in raw JSON
- No duplicate canonical IDs within any seed file
- No duplicate IDs across all seed domains
- Cross-domain references are internally consistent
- Seed records marked with correct data_classification text
"""

import json
from pathlib import Path
from typing import Dict, Set

import pytest

from app.data.loaders.domain_loaders import (
    CourseLoader,
    OccupationLoader,
    OpportunityLoader,
    ProviderLoader,
    SkillLoader,
)

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"

SEED_FILES = {
    "skills": ("skills.json", SkillLoader, "skill_id"),
    "occupations": ("occupations.json", OccupationLoader, "occupation_id"),
    "courses": ("courses.json", CourseLoader, "course_id"),
    "opportunities": ("opportunities.json", OpportunityLoader, "opportunity_id"),
    "providers": ("providers.json", ProviderLoader, "provider_id"),
}


def load_raw_json(filename: str) -> list:
    fpath = SEED_DIR / filename
    return json.loads(fpath.read_text(encoding="utf-8"))


# ─── File existence ───────────────────────────────────────────────────────────

class TestSeedFileExistence:
    @pytest.mark.parametrize("domain,info", list(SEED_FILES.items()))
    def test_seed_file_exists(self, domain, info):
        fname, _, _ = info
        fpath = SEED_DIR / fname
        assert fpath.exists(), f"Seed file missing: {fpath}"


# ─── Clean loading ────────────────────────────────────────────────────────────

class TestSeedDataLoadsCleanly:
    def test_skills_load_cleanly(self):
        result = SkillLoader(data_path=SEED_DIR / "skills.json").load()
        assert result.is_clean, f"Skill seed errors: {[e.reason for e in result.errors]}"
        assert result.total_valid >= 1

    def test_occupations_load_cleanly(self):
        result = OccupationLoader(data_path=SEED_DIR / "occupations.json").load()
        assert result.is_clean, f"Occupation seed errors: {[e.reason for e in result.errors]}"
        assert result.total_valid >= 1

    def test_courses_load_cleanly(self):
        result = CourseLoader(data_path=SEED_DIR / "courses.json").load()
        assert result.is_clean, f"Course seed errors: {[e.reason for e in result.errors]}"
        assert result.total_valid >= 1

    def test_opportunities_load_cleanly(self):
        result = OpportunityLoader(data_path=SEED_DIR / "opportunities.json").load()
        assert result.is_clean, f"Opportunity seed errors: {[e.reason for e in result.errors]}"
        assert result.total_valid >= 1

    def test_providers_load_cleanly(self):
        result = ProviderLoader(data_path=SEED_DIR / "providers.json").load()
        assert result.is_clean, f"Provider seed errors: {[e.reason for e in result.errors]}"
        assert result.total_valid >= 1


# ─── Synthetic / demo markers ─────────────────────────────────────────────────

class TestSeedDataSyntheticMarkers:
    """All seed records must carry is_synthetic=true in raw JSON."""

    @pytest.mark.parametrize("domain,info", list(SEED_FILES.items()))
    def test_is_synthetic_marked_in_raw_json(self, domain, info):
        fname, _, _ = info
        raw_records = load_raw_json(fname)
        for i, record in enumerate(raw_records):
            assert record.get("is_synthetic") is True, (
                f"{fname}[{i}]: 'is_synthetic' must be true. "
                "All seed records must be explicitly marked as synthetic demo data."
            )

    @pytest.mark.parametrize("domain,info", list(SEED_FILES.items()))
    def test_data_classification_synthetic_in_raw_json(self, domain, info):
        fname, _, _ = info
        raw_records = load_raw_json(fname)
        for i, record in enumerate(raw_records):
            classification = record.get("data_classification", "")
            assert "SYNTHETIC" in classification.upper(), (
                f"{fname}[{i}]: data_classification must include 'SYNTHETIC'. Got: {classification!r}"
            )


# ─── Duplicate ID checks ─────────────────────────────────────────────────────

class TestSeedDataNoDuplicates:
    def _collect_ids(self, fname: str, id_field: str) -> Set[str]:
        raw = load_raw_json(fname)
        return {r[id_field] for r in raw if id_field in r}

    def test_no_duplicate_skill_ids(self):
        raw = load_raw_json("skills.json")
        ids = [r["skill_id"] for r in raw]
        assert len(ids) == len(set(ids)), "Duplicate skill_id found in skills.json"

    def test_no_duplicate_occupation_ids(self):
        raw = load_raw_json("occupations.json")
        ids = [r["occupation_id"] for r in raw]
        assert len(ids) == len(set(ids)), "Duplicate occupation_id found in occupations.json"

    def test_no_duplicate_course_ids(self):
        raw = load_raw_json("courses.json")
        ids = [r["course_id"] for r in raw]
        assert len(ids) == len(set(ids)), "Duplicate course_id found in courses.json"

    def test_no_duplicate_opportunity_ids(self):
        raw = load_raw_json("opportunities.json")
        ids = [r["opportunity_id"] for r in raw]
        assert len(ids) == len(set(ids)), "Duplicate opportunity_id found in opportunities.json"

    def test_no_duplicate_provider_ids(self):
        raw = load_raw_json("providers.json")
        ids = [r["provider_id"] for r in raw]
        assert len(ids) == len(set(ids)), "Duplicate provider_id found in providers.json"

    def test_no_cross_domain_id_collisions(self):
        """IDs from different domains must not collide (SYN-001 prefix isolation)."""
        all_ids: Dict[str, str] = {}
        for domain, (fname, _, id_field) in SEED_FILES.items():
            raw = load_raw_json(fname)
            for r in raw:
                rid = r.get(id_field)
                if rid:
                    assert rid not in all_ids, (
                        f"ID {rid!r} appears in both {domain} and {all_ids[rid]}"
                    )
                    all_ids[rid] = domain


# ─── Cross-domain reference integrity ────────────────────────────────────────

class TestSeedDataCrossReferences:
    def test_occupation_required_skills_exist(self):
        skill_ids = {r["skill_id"] for r in load_raw_json("skills.json")}
        for occ in load_raw_json("occupations.json"):
            for sid in occ.get("required_skills", []):
                assert sid in skill_ids, (
                    f"Occupation {occ['occupation_id']} references unknown skill_id={sid!r}"
                )

    def test_course_acquired_skills_exist(self):
        skill_ids = {r["skill_id"] for r in load_raw_json("skills.json")}
        for crs in load_raw_json("courses.json"):
            for sid in crs.get("acquired_skills", []):
                assert sid in skill_ids, (
                    f"Course {crs['course_id']} references unknown skill_id={sid!r}"
                )

    def test_opportunity_required_skills_exist(self):
        skill_ids = {r["skill_id"] for r in load_raw_json("skills.json")}
        for opp in load_raw_json("opportunities.json"):
            for sid in opp.get("required_skills", []):
                assert sid in skill_ids, (
                    f"Opportunity {opp['opportunity_id']} references unknown skill_id={sid!r}"
                )

    def test_provider_courses_exist(self):
        course_ids = {r["course_id"] for r in load_raw_json("courses.json")}
        for prv in load_raw_json("providers.json"):
            for cid in prv.get("courses_offered", []):
                assert cid in course_ids, (
                    f"Provider {prv['provider_id']} references unknown course_id={cid!r}"
                )

    def test_courses_nsqf_level_valid(self):
        for crs in load_raw_json("courses.json"):
            level = crs.get("nsqf_level")
            assert isinstance(level, int) and 1 <= level <= 10, (
                f"Course {crs['course_id']} has invalid nsqf_level={level}"
            )
