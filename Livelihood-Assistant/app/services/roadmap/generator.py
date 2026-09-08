"""Deterministic skill-gap analysis and evidence-grounded career roadmaps."""

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from app.data.repositories.base import BaseRepository
from app.data.repositories.domain_repositories import SkillRepository
from app.schemas.course import NSQFCourse
from app.schemas.occupation import Occupation
from app.schemas.opportunity import Opportunity
from app.schemas.recommendation import PathwayType, Recommendation
from app.schemas.roadmap import Roadmap, RoadmapRequest, RoadmapResponse, RoadmapStep, StepStatus, StepType
from app.schemas.skill import GapStatus, PriorityLevel, SkillGap, SkillProficiency
from app.services.normalization.skill_normalizer import SkillNormalizationService


class BaseRoadmapService(ABC):
    """Contract for deterministic roadmap generation from canonical data."""

    @abstractmethod
    async def generate_roadmap(self, request: RoadmapRequest) -> RoadmapResponse:
        """Generate an ordered roadmap or explicitly report an unavailable target."""


class RoadmapService(BaseRoadmapService):
    """Compares canonical skills and creates only evidence-backed action steps."""

    def __init__(
        self,
        occupation_repository: BaseRepository[Occupation],
        course_repository: BaseRepository[NSQFCourse],
        opportunity_repository: BaseRepository[Opportunity],
        skill_repository: SkillRepository,
        skill_normalizer: Optional[SkillNormalizationService] = None,
    ):
        self._occupations = occupation_repository
        self._courses = course_repository
        self._opportunities = opportunity_repository
        self._skills = skill_repository
        self._normalizer = skill_normalizer or SkillNormalizationService(skill_repository)

    def _profile_skill_ids(self, request: RoadmapRequest) -> set[str]:
        skill_ids = {skill.skill_id for skill in request.profile.normalized_skills}
        for raw_skill in request.profile.traditional_skills:
            result = self._normalizer.normalize(raw_skill)
            if result.canonical_skill_id:
                skill_ids.add(result.canonical_skill_id)
        return skill_ids

    @staticmethod
    def _required_skill_ids(occupation: Occupation, courses: Iterable[NSQFCourse]) -> set[str]:
        required = set(occupation.required_skills)
        for course in courses:
            required.update(course.required_skills)
        return required

    def analyze_skill_gaps(
        self, profile_skill_ids: set[str], required_skill_ids: set[str], has_skill_information: bool, courses: Iterable[NSQFCourse]
    ) -> list[SkillGap]:
        """Classify each requirement without turning absent skill data into a gap."""
        acquired_by_courses = {skill_id for course in courses for skill_id in course.acquired_skills}
        gaps = []
        for skill_id in sorted(required_skill_ids):
            canonical = self._skills.get_by_id(skill_id)
            skill_name = canonical.name if canonical else skill_id
            if not has_skill_information:
                status, priority = GapStatus.UNKNOWN, PriorityLevel.MEDIUM
            elif skill_id in profile_skill_ids:
                status, priority = GapStatus.ACQUIRED, PriorityLevel.LOW
            else:
                status = GapStatus.MISSING
                priority = PriorityLevel.HIGH if skill_id in acquired_by_courses else PriorityLevel.MEDIUM
            gaps.append(SkillGap(
                skill_id=skill_id, skill_name=skill_name,
                current_proficiency=SkillProficiency.UNKNOWN,
                gap_status=status, priority=priority,
            ))
        return gaps

    @staticmethod
    def _course_evidence(courses: Iterable[NSQFCourse]):
        return [course.source_metadata for course in courses if course.source_metadata]

    @staticmethod
    def _dedupe_evidence(evidence):
        return list({item.source_id: item for item in evidence}.values())

    def _courses_for_target(self, occupation: Occupation, recommendation: Optional[Recommendation]) -> list[NSQFCourse]:
        requested_id = recommendation.course_reference if recommendation else None
        courses = []
        for course in self._courses.list_all():
            is_linked = course.course_id in occupation.nsqf_qualification_ids or occupation.occupation_id in course.job_roles
            if requested_id and course.course_id == requested_id and is_linked:
                courses.append(course)
            elif is_linked:
                courses.append(course)
        return sorted({course.course_id: course for course in courses}.values(), key=lambda item: item.course_id)

    def _opportunities_for_recommendation(self, recommendation: Optional[Recommendation]) -> list[Opportunity]:
        if recommendation is None:
            return []
        return [
            opportunity for identifier in recommendation.opportunity_references
            if (opportunity := self._opportunities.get_by_id(identifier)) is not None
        ]

    def _make_steps(
        self, gaps: list[SkillGap], courses: list[NSQFCourse], opportunities: list[Opportunity], limitations: list[str]
    ) -> list[RoadmapStep]:
        steps: list[RoadmapStep] = []
        missing = [gap for gap in gaps if gap.gap_status == GapStatus.MISSING]
        unknown = [gap for gap in gaps if gap.gap_status == GapStatus.UNKNOWN]
        if unknown:
            steps.append(RoadmapStep(
                step_id="STEP-1", step_number=1, step_type=StepType.VERIFICATION, status=StepStatus.BLOCKED,
                title="Confirm current skills", description="Current skill information is insufficient to verify required skills.",
            ))
        mapped_courses = [
            course for course in courses
            if any(gap.skill_id in course.acquired_skills for gap in missing)
        ]
        if missing and mapped_courses:
            prerequisites = [steps[-1].step_id] if steps else []
            course_ids = [course.course_id for course in mapped_courses]
            steps.append(RoadmapStep(
                step_id=f"STEP-{len(steps) + 1}", step_number=len(steps) + 1,
                step_type=StepType.TRAINING, status=StepStatus.PENDING,
                title="Complete linked skill training",
                description="Complete the listed canonical course(s) that explicitly acquire the missing target skills.",
                course_references=course_ids, prerequisites=prerequisites,
                evidence=self._dedupe_evidence(self._course_evidence(mapped_courses)),
            ))
        elif missing:
            limitations.append("No linked course in the repository explicitly acquires the missing required skills.")
            steps.append(RoadmapStep(
                step_id=f"STEP-{len(steps) + 1}", step_number=len(steps) + 1,
                step_type=StepType.VERIFICATION, status=StepStatus.BLOCKED,
                title="Verify relevant training availability",
                description="No valid linked course mapping is available for the missing skills; verify training options before proceeding.",
                prerequisites=[steps[-1].step_id] if steps else [],
            ))
        if opportunities:
            evidence = []
            for opportunity in opportunities:
                if opportunity.source:
                    evidence.append(opportunity.source)
                evidence.extend(opportunity.evidence)
            steps.append(RoadmapStep(
                step_id=f"STEP-{len(steps) + 1}", step_number=len(steps) + 1,
                step_type=StepType.JOB_APPLICATION, status=StepStatus.PENDING,
                title="Review linked opportunity and apply when ready",
                description="Review the referenced opportunity details and apply only after confirming its current requirements and availability.",
                opportunity_references=[item.opportunity_id for item in opportunities],
                prerequisites=[steps[-1].step_id] if steps else [], evidence=self._dedupe_evidence(evidence),
            ))
        return steps

    async def generate_roadmap(self, request: RoadmapRequest) -> RoadmapResponse:
        recommendation = request.recommendation
        occupation_id = request.target_occupation_id or (recommendation.occupation_reference if recommendation else None)
        occupation = self._occupations.get_by_id(occupation_id) if occupation_id else None
        if occupation is None:
            return RoadmapResponse(roadmap=None, status="target_not_found")
        courses = self._courses_for_target(occupation, recommendation)
        profile_skills = self._profile_skill_ids(request)
        has_skill_information = bool(profile_skills)
        required = self._required_skill_ids(occupation, courses)
        gaps = self.analyze_skill_gaps(profile_skills, required, has_skill_information, courses)
        matched = [gap.skill_id for gap in gaps if gap.gap_status == GapStatus.ACQUIRED]
        limitations = []
        if not has_skill_information:
            limitations.append("Beneficiary canonical skills are unknown; required skills cannot be classified as missing.")
        if not courses:
            limitations.append("No linked course or training record is available for the target occupation.")
        opportunities = self._opportunities_for_recommendation(recommendation)
        if recommendation and recommendation.opportunity_references and not opportunities:
            limitations.append("Referenced opportunities are unavailable in the repository.")
        steps = self._make_steps(gaps, courses, opportunities, limitations)
        evidence = [*request.profile.evidence]
        if occupation.source_metadata:
            evidence.append(occupation.source_metadata)
        evidence.extend(self._course_evidence(courses))
        if recommendation:
            evidence.extend(recommendation.evidence)
        roadmap = Roadmap(
            roadmap_id=f"RDM-{request.profile.beneficiary_id or 'UNASSIGNED'}-{occupation.occupation_id}",
            beneficiary_id=request.profile.beneficiary_id, target_occupation_id=occupation.occupation_id,
            target_pathway=(recommendation.pathway_type if recommendation else request.target_pathway or PathwayType.SKILL_TRAINING),
            current_state_summary=(f"{len(matched)} of {len(required)} required canonical skills are matched."
                                   if has_skill_information else "Current canonical skills are unknown."),
            skill_gaps=gaps, matched_skills=matched, limitations=limitations, steps=steps,
            evidence=self._dedupe_evidence(evidence),
        )
        return RoadmapResponse(roadmap=roadmap, status="completed")
