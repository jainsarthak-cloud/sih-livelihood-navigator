"""
Unit tests for Phase 3 repository layer.

Covers:
- InMemoryRepository CRUD: add, get_by_id, list_all, exists, count
- Duplicate add raises ValueError
- add_or_replace upsert semantics
- find_by_field basic behaviour
- find_by_field with non-existent field raises AttributeError
- clear() empties repository
- Domain repository query helpers:
    SkillRepository.find_by_category / find_by_alias
    OccupationRepository.find_by_sector / find_requiring_skill
    CourseRepository.find_by_nsqf_level / find_by_nsqf_level_range
    OpportunityRepository.find_by_district / find_active / find_requiring_skill
    ProviderRepository.find_by_sector / find_offering_course
"""

from datetime import datetime, timezone

import pytest

from app.data.repositories.memory_repository import InMemoryRepository
from app.data.repositories.domain_repositories import (
    CourseRepository,
    OccupationRepository,
    OpportunityRepository,
    ProviderRepository,
    SkillRepository,
)
from app.schemas.skill import Skill, SkillCategory, SkillProficiency
from app.schemas.occupation import Occupation, EmploymentType
from app.schemas.course import NSQFCourse
from app.schemas.opportunity import Opportunity, OpportunityLifecycle, OpportunityType
from app.schemas.provider import TrainingProvider, ProviderType
from app.schemas.common import GeographicLocation


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_skill(skill_id: str, category: SkillCategory = SkillCategory.TECHNICAL) -> Skill:
    return Skill(skill_id=skill_id, name=f"Skill {skill_id}", category=category)


def make_occupation(
    occ_id: str,
    sector: str = "Test Sector",
    employment_type: EmploymentType = EmploymentType.FULL_TIME,
    required_skills: list = None,
) -> Occupation:
    return Occupation(
        occupation_id=occ_id,
        name=f"Occupation {occ_id}",
        sector=sector,
        employment_type=employment_type,
        required_skills=required_skills or [],
    )


def make_course(course_id: str, nsqf_level: int = 3, sector: str = "Test") -> NSQFCourse:
    return NSQFCourse(
        course_id=course_id,
        course_name=f"Course {course_id}",
        qualification_name=f"Qual {course_id}",
        nsqf_level=nsqf_level,
        sector=sector,
    )


def make_opportunity(
    opp_id: str,
    district: str = "Test District",
    opp_type: OpportunityType = OpportunityType.WAGE_EMPLOYMENT,
    lifecycle: OpportunityLifecycle = OpportunityLifecycle.ACTIVE,
    required_skills: list = None,
) -> Opportunity:
    return Opportunity(
        opportunity_id=opp_id,
        title=f"Opportunity {opp_id}",
        opportunity_type=opp_type,
        sector="Test Sector",
        location=GeographicLocation(state="Test State", district=district),
        collected_at=datetime.now(timezone.utc),
        lifecycle_status=lifecycle,
        required_skills=required_skills or [],
    )


def make_provider(
    provider_id: str,
    sectors: list = None,
    courses: list = None,
) -> TrainingProvider:
    return TrainingProvider(
        provider_id=provider_id,
        name=f"Provider {provider_id}",
        provider_type=ProviderType.COMMUNITY_SKILL_CENTRE,
        sectors_covered=sectors or [],
        courses_offered=courses or [],
    )


# ─── InMemoryRepository base tests ───────────────────────────────────────────

class TestInMemoryRepository:
    def _make_repo(self) -> InMemoryRepository[Skill]:
        return InMemoryRepository(id_field="skill_id")

    def test_add_and_get(self):
        repo = self._make_repo()
        skill = make_skill("SKL-001")
        repo.add(skill)
        fetched = repo.get_by_id("SKL-001")
        assert fetched is not None
        assert fetched.skill_id == "SKL-001"

    def test_get_missing_returns_none(self):
        repo = self._make_repo()
        assert repo.get_by_id("SKL-NONEXISTENT") is None

    def test_list_all(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-A"))
        repo.add(make_skill("SKL-B"))
        all_items = repo.list_all()
        assert len(all_items) == 2

    def test_exists(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-X"))
        assert repo.exists("SKL-X") is True
        assert repo.exists("SKL-MISSING") is False

    def test_count(self):
        repo = self._make_repo()
        assert repo.count() == 0
        repo.add(make_skill("SKL-1"))
        repo.add(make_skill("SKL-2"))
        assert repo.count() == 2

    def test_add_duplicate_raises(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-DUP"))
        with pytest.raises(ValueError, match="already exists"):
            repo.add(make_skill("SKL-DUP"))

    def test_add_or_replace_upsert(self):
        repo = self._make_repo()
        s1 = make_skill("SKL-UPSERT")
        repo.add(s1)
        s2 = Skill(skill_id="SKL-UPSERT", name="Updated Name")
        repo.add_or_replace("SKL-UPSERT", s2)
        assert repo.get_by_id("SKL-UPSERT").name == "Updated Name"

    def test_find_by_field(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-T1", category=SkillCategory.TECHNICAL))
        repo.add(make_skill("SKL-S1", category=SkillCategory.SOFT_SKILL))
        repo.add(make_skill("SKL-T2", category=SkillCategory.TECHNICAL))

        technical = repo.find_by_field("category", SkillCategory.TECHNICAL)
        assert len(technical) == 2

    def test_find_by_field_no_match(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-1", category=SkillCategory.TECHNICAL))
        results = repo.find_by_field("category", SkillCategory.AGRICULTURAL)
        assert results == []

    def test_find_by_field_bad_attribute_raises(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-1"))
        with pytest.raises(AttributeError):
            repo.find_by_field("nonexistent_field", "value")

    def test_clear(self):
        repo = self._make_repo()
        repo.add(make_skill("SKL-1"))
        repo.add(make_skill("SKL-2"))
        assert repo.count() == 2
        repo.clear()
        assert repo.count() == 0


# ─── SkillRepository domain query helpers ────────────────────────────────────

class TestSkillRepository:
    def test_find_by_category(self):
        repo = SkillRepository()
        repo.add(make_skill("S1", SkillCategory.TECHNICAL))
        repo.add(make_skill("S2", SkillCategory.SOFT_SKILL))
        repo.add(make_skill("S3", SkillCategory.TECHNICAL))
        results = repo.find_by_category(SkillCategory.TECHNICAL)
        assert len(results) == 2

    def test_find_by_name_case_insensitive(self):
        repo = SkillRepository()
        skill = Skill(skill_id="S1", name="Garment Stitching")
        repo.add(skill)
        found = repo.find_by_name("garment stitching")
        assert found is not None
        assert found.skill_id == "S1"

    def test_find_by_alias(self):
        repo = SkillRepository()
        skill = Skill(skill_id="S1", name="Stitching", aliases=["Silai", "Sewing"])
        repo.add(skill)
        results = repo.find_by_alias("silai")
        assert len(results) == 1

    def test_find_by_name_not_found(self):
        repo = SkillRepository()
        assert repo.find_by_name("does not exist") is None


# ─── OccupationRepository domain query helpers ───────────────────────────────

class TestOccupationRepository:
    def test_find_by_sector(self):
        repo = OccupationRepository()
        repo.add(make_occupation("O1", sector="Textile"))
        repo.add(make_occupation("O2", sector="Construction"))
        repo.add(make_occupation("O3", sector="textile"))  # case-insensitive
        results = repo.find_by_sector("Textile")
        assert len(results) == 2

    def test_find_requiring_skill(self):
        repo = OccupationRepository()
        repo.add(make_occupation("O1", required_skills=["SKL-A", "SKL-B"]))
        repo.add(make_occupation("O2", required_skills=["SKL-C"]))
        repo.add(make_occupation("O3", required_skills=["SKL-A"]))
        results = repo.find_requiring_skill("SKL-A")
        assert {r.occupation_id for r in results} == {"O1", "O3"}

    def test_find_by_employment_type(self):
        repo = OccupationRepository()
        repo.add(make_occupation("O1", employment_type=EmploymentType.FULL_TIME))
        repo.add(make_occupation("O2", employment_type=EmploymentType.SEASONAL))
        results = repo.find_by_employment_type(EmploymentType.FULL_TIME)
        assert len(results) == 1


# ─── CourseRepository domain query helpers ───────────────────────────────────

class TestCourseRepository:
    def test_find_by_nsqf_level(self):
        repo = CourseRepository()
        repo.add(make_course("C1", nsqf_level=3))
        repo.add(make_course("C2", nsqf_level=4))
        repo.add(make_course("C3", nsqf_level=3))
        results = repo.find_by_nsqf_level(3)
        assert len(results) == 2

    def test_find_by_nsqf_level_range(self):
        repo = CourseRepository()
        for level in [2, 3, 4, 5, 6]:
            repo.add(make_course(f"C{level}", nsqf_level=level))
        results = repo.find_by_nsqf_level_range(3, 5)
        assert len(results) == 3
        assert all(3 <= c.nsqf_level <= 5 for c in results)

    def test_find_acquiring_skill(self):
        repo = CourseRepository()
        c1 = NSQFCourse(
            course_id="C1",
            course_name="C1",
            qualification_name="Q1",
            nsqf_level=3,
            sector="Test",
            acquired_skills=["SKL-A", "SKL-B"],
        )
        c2 = NSQFCourse(
            course_id="C2",
            course_name="C2",
            qualification_name="Q2",
            nsqf_level=4,
            sector="Test",
            acquired_skills=["SKL-C"],
        )
        repo.add(c1)
        repo.add(c2)
        results = repo.find_acquiring_skill("SKL-A")
        assert len(results) == 1
        assert results[0].course_id == "C1"


# ─── OpportunityRepository domain query helpers ──────────────────────────────

class TestOpportunityRepository:
    def test_find_active(self):
        repo = OpportunityRepository()
        repo.add(make_opportunity("O1", lifecycle=OpportunityLifecycle.ACTIVE))
        repo.add(make_opportunity("O2", lifecycle=OpportunityLifecycle.REPORTED))
        repo.add(make_opportunity("O3", lifecycle=OpportunityLifecycle.ACTIVE))
        active = repo.find_active()
        assert len(active) == 2

    def test_find_by_district_case_insensitive(self):
        repo = OpportunityRepository()
        repo.add(make_opportunity("O1", district="Varanasi"))
        repo.add(make_opportunity("O2", district="Patna"))
        results = repo.find_by_district("varanasi")
        assert len(results) == 1

    def test_find_requiring_skill(self):
        repo = OpportunityRepository()
        repo.add(make_opportunity("O1", required_skills=["SKL-A"]))
        repo.add(make_opportunity("O2", required_skills=["SKL-B"]))
        results = repo.find_requiring_skill("SKL-A")
        assert len(results) == 1
        assert results[0].opportunity_id == "O1"

    def test_find_by_type(self):
        repo = OpportunityRepository()
        repo.add(make_opportunity("O1", opp_type=OpportunityType.APPRENTICESHIP))
        repo.add(make_opportunity("O2", opp_type=OpportunityType.WAGE_EMPLOYMENT))
        results = repo.find_by_type(OpportunityType.APPRENTICESHIP)
        assert len(results) == 1


# ─── ProviderRepository domain query helpers ─────────────────────────────────

class TestProviderRepository:
    def test_find_by_sector(self):
        repo = ProviderRepository()
        repo.add(make_provider("P1", sectors=["Textile", "Apparel"]))
        repo.add(make_provider("P2", sectors=["Construction"]))
        results = repo.find_by_sector("textile")
        assert len(results) == 1

    def test_find_offering_course(self):
        repo = ProviderRepository()
        repo.add(make_provider("P1", courses=["CRS-001", "CRS-002"]))
        repo.add(make_provider("P2", courses=["CRS-003"]))
        results = repo.find_offering_course("CRS-001")
        assert len(results) == 1
        assert results[0].provider_id == "P1"
