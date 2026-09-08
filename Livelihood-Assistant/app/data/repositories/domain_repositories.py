"""
Domain-specific typed repositories with query helpers.

Each domain repository:
- Extends InMemoryRepository with the correct generic type
- Sets the correct id_field
- Adds domain-specific query helpers (find_by_sector, find_by_nsqf_level, etc.)

The AI engine should import these typed repositories, not InMemoryRepository directly.
"""

import re
import unicodedata
from typing import List, Optional

from app.data.repositories.memory_repository import InMemoryRepository
from app.schemas.course import NSQFCourse
from app.schemas.occupation import Occupation, EmploymentType
from app.schemas.opportunity import Opportunity, OpportunityLifecycle, OpportunityType
from app.schemas.provider import TrainingProvider
from app.schemas.skill import Skill, SkillCategory


class SkillRepository(InMemoryRepository[Skill]):
    """In-memory repository for canonical Skill master records."""

    def __init__(self):
        super().__init__(id_field="skill_id")

    def find_by_category(self, category: SkillCategory) -> List[Skill]:
        """Return all skills belonging to a given SkillCategory."""
        return self.find_by_field("category", category)

    def find_by_name(self, name: str) -> Optional[Skill]:
        """Case-insensitive lookup by canonical skill name."""
        name_lower = name.lower()
        for skill in self.list_all():
            if skill.name.lower() == name_lower:
                return skill
        return None

    def find_by_alias(self, alias: str) -> List[Skill]:
        """Return skills that include alias in their aliases list."""
        alias_lower = alias.lower()
        return [
            s for s in self.list_all()
            if any(a.lower() == alias_lower for a in s.aliases)
        ]

    @staticmethod
    def _normalization_key(value: str) -> str:
        """Create a deterministic comparison key without changing stored data."""
        value = unicodedata.normalize("NFKC", value).casefold()
        return " ".join(re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).split())

    def find_by_normalized_term(self, term: str) -> List[Skill]:
        """Find canonical names or aliases after case/spacing/punctuation folding."""
        key = self._normalization_key(term)
        if not key:
            return []
        return [
            skill
            for skill in self.list_all()
            if self._normalization_key(skill.name) == key
            or any(self._normalization_key(alias) == key for alias in skill.aliases)
        ]


class OccupationRepository(InMemoryRepository[Occupation]):
    """In-memory repository for canonical Occupation master records."""

    def __init__(self):
        super().__init__(id_field="occupation_id")

    def find_by_sector(self, sector: str) -> List[Occupation]:
        """Return all occupations in a given sector (case-insensitive)."""
        sector_lower = sector.lower()
        return [
            o for o in self.list_all()
            if o.sector.lower() == sector_lower
        ]

    def find_by_employment_type(self, employment_type: EmploymentType) -> List[Occupation]:
        """Return occupations filtered by employment type."""
        return self.find_by_field("employment_type", employment_type)

    def find_by_normalized_term(self, term: str) -> List[Occupation]:
        """Find canonical occupation names or aliases after deterministic text folding."""
        key = SkillRepository._normalization_key(term)
        if not key:
            return []
        return [
            occupation for occupation in self.list_all()
            if SkillRepository._normalization_key(occupation.name) == key
            or any(SkillRepository._normalization_key(alias) == key for alias in occupation.aliases)
        ]

    def find_requiring_skill(self, skill_id: str) -> List[Occupation]:
        """Return all occupations that list skill_id in required_skills."""
        return [
            o for o in self.list_all()
            if skill_id in o.required_skills
        ]


class CourseRepository(InMemoryRepository[NSQFCourse]):
    """In-memory repository for canonical NSQFCourse records."""

    def __init__(self):
        super().__init__(id_field="course_id")

    def find_by_nsqf_level(self, level: int) -> List[NSQFCourse]:
        """Return all courses at a given NSQF level (1–10)."""
        return self.find_by_field("nsqf_level", level)

    def find_by_sector(self, sector: str) -> List[NSQFCourse]:
        """Return courses in a given sector (case-insensitive)."""
        sector_lower = sector.lower()
        return [
            c for c in self.list_all()
            if c.sector.lower() == sector_lower
        ]

    def find_by_nsqf_level_range(self, min_level: int, max_level: int) -> List[NSQFCourse]:
        """Return courses within an NSQF level range [min_level, max_level]."""
        return [
            c for c in self.list_all()
            if min_level <= c.nsqf_level <= max_level
        ]

    def find_acquiring_skill(self, skill_id: str) -> List[NSQFCourse]:
        """Return courses that list skill_id in acquired_skills."""
        return [
            c for c in self.list_all()
            if skill_id in c.acquired_skills
        ]


class OpportunityRepository(InMemoryRepository[Opportunity]):
    """In-memory repository for Opportunity operational records."""

    def __init__(self):
        super().__init__(id_field="opportunity_id")

    def find_by_sector(self, sector: str) -> List[Opportunity]:
        """Return opportunities in a given sector (case-insensitive)."""
        sector_lower = sector.lower()
        return [
            o for o in self.list_all()
            if o.sector.lower() == sector_lower
        ]

    def find_by_type(self, opp_type: OpportunityType) -> List[Opportunity]:
        """Return opportunities of a given type."""
        return self.find_by_field("opportunity_type", opp_type)

    def find_active(self) -> List[Opportunity]:
        """Return all opportunities in ACTIVE lifecycle state."""
        return self.find_by_field("lifecycle_status", OpportunityLifecycle.ACTIVE)

    def find_by_district(self, district: str) -> List[Opportunity]:
        """Return opportunities located in a given district (case-insensitive)."""
        district_lower = district.lower()
        return [
            o for o in self.list_all()
            if o.location and o.location.district.lower() == district_lower
        ]

    def find_requiring_skill(self, skill_id: str) -> List[Opportunity]:
        """Return opportunities that require a given skill ID."""
        return [
            o for o in self.list_all()
            if skill_id in o.required_skills
        ]


class ProviderRepository(InMemoryRepository[TrainingProvider]):
    """In-memory repository for TrainingProvider master records."""

    def __init__(self):
        super().__init__(id_field="provider_id")

    def find_by_sector(self, sector: str) -> List[TrainingProvider]:
        """Return providers affiliated with a given sector (case-insensitive)."""
        sector_lower = sector.lower()
        return [
            p for p in self.list_all()
            if any(s.lower() == sector_lower for s in p.sectors_covered)
        ]

    def find_offering_course(self, course_id: str) -> List[TrainingProvider]:
        """Return providers that offer the given course ID."""
        return [
            p for p in self.list_all()
            if course_id in p.courses_offered
        ]
