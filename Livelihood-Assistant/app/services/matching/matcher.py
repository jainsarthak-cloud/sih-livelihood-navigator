"""
Skill Matching Service Interface and Placeholder.
Matches beneficiary existing skills and experience to NSQF qualification packs and competencies.
"""

from abc import ABC, abstractmethod
from typing import List
from app.core.exceptions import ServiceNotImplementedException
from app.schemas.course import NSQFCourse
from app.schemas.profile import BeneficiaryProfile
from app.schemas.recommendation import Recommendation


class BaseSkillMatchingService(ABC):
    """Abstract base interface for matching candidate skills to NSQF packs."""

    @abstractmethod
    async def match_skills(
        self, profile: BeneficiaryProfile, target_courses: List[NSQFCourse]
    ) -> List[Recommendation]:
        """Perform semantic matching between candidate skills and qualification packs."""
        pass


class SkillMatchingService(BaseSkillMatchingService):
    """Production service placeholder for skill matching."""

    async def match_skills(
        self, profile: BeneficiaryProfile, target_courses: List[NSQFCourse]
    ) -> List[Recommendation]:
        raise ServiceNotImplementedException(
            service_name="SkillMatchingService.match_skills",
            details={
                "beneficiary_id": profile.beneficiary_id,
                "num_target_courses": len(target_courses),
            },
        )
