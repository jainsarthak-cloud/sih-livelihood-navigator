"""Phase 5 deterministic, repository-backed livelihood recommendations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
import re
from typing import Iterable, Optional

from app.core.config import Settings, settings
from app.data.repositories.base import BaseRepository
from app.data.repositories.domain_repositories import SkillRepository
from app.schemas.common import EducationLevel, EmploymentPreference, SourceEvidence
from app.schemas.course import NSQFCourse
from app.schemas.eligibility import CriterionResult, EligibilityResult, EligibilityStatus
from app.schemas.occupation import EmploymentType, Occupation
from app.schemas.opportunity import Opportunity, OpportunityLifecycle
from app.schemas.profile import BeneficiaryProfile
from app.schemas.recommendation import PathwayType, Recommendation, RecommendationRequest, RecommendationResponse, ScoreBreakdown
from app.schemas.skill import GapStatus, PriorityLevel, SkillGap
from app.services.normalization.skill_normalizer import SkillNormalizationService


_EDUCATION_ORDER = {
    EducationLevel.NONE: 0, EducationLevel.PRIMARY: 1, EducationLevel.MIDDLE: 2,
    EducationLevel.SECONDARY_10TH: 3, EducationLevel.HIGHER_SECONDARY_12TH: 4,
    EducationLevel.DIPLOMA: 5, EducationLevel.ITI: 5, EducationLevel.GRADUATE: 6,
    EducationLevel.POST_GRADUATE: 7,
}


@dataclass(frozen=True)
class RecommendationCandidate:
    """Internal canonical pathway candidate generated from repository records."""

    occupation: Occupation
    course: Optional[NSQFCourse]
    opportunities: tuple[Opportunity, ...]


class BaseRecommendationService(ABC):
    """Contract for deterministic canonical-pathway recommendations."""

    @abstractmethod
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate at most three ranked livelihood pathways."""


class RecommendationService(BaseRecommendationService):
    """Composable deterministic scorer over canonical repository interfaces.

    Similarity components are separate methods so a later semantic adapter can
    replace one component without changing the recommendation contract.
    """

    def __init__(
        self,
        occupation_repository: BaseRepository[Occupation],
        course_repository: BaseRepository[NSQFCourse],
        opportunity_repository: BaseRepository[Opportunity],
        skill_repository: SkillRepository,
        skill_normalizer: Optional[SkillNormalizationService] = None,
        config: Settings = settings,
    ):
        self._occupations = occupation_repository
        self._courses = course_repository
        self._opportunities = opportunity_repository
        self._skills = skill_repository
        self._normalizer = skill_normalizer or SkillNormalizationService(skill_repository, config)
        self._weights = {
            "interest": config.RECOMMENDATION_INTEREST_WEIGHT,
            "skill": config.RECOMMENDATION_SKILL_WEIGHT,
            "eligibility": config.RECOMMENDATION_ELIGIBILITY_WEIGHT,
            "local_opportunity": config.RECOMMENDATION_LOCAL_OPPORTUNITY_WEIGHT,
            "labour_demand": config.RECOMMENDATION_LABOUR_DEMAND_WEIGHT,
            "employment_preference": config.RECOMMENDATION_EMPLOYMENT_PREFERENCE_WEIGHT,
        }
        if round(sum(self._weights.values()), 8) != 1.0:
            raise ValueError("Recommendation component weights must total 1.0")
        self._model_version = config.RECOMMENDATION_MODEL_VERSION

    @staticmethod
    def _key(value: str) -> str:
        return " ".join(re.sub(r"[^\w]+", " ", value.casefold()).split())

    @staticmethod
    def _employment_preference(occupation: Occupation) -> EmploymentPreference | None:
        if occupation.employment_type == EmploymentType.APPRENTICESHIP:
            return EmploymentPreference.APPRENTICESHIP
        if occupation.employment_type == EmploymentType.SELF_EMPLOYED:
            return EmploymentPreference.SELF_EMPLOYMENT
        if occupation.employment_type in {EmploymentType.FULL_TIME, EmploymentType.PART_TIME, EmploymentType.CONTRACT, EmploymentType.SEASONAL}:
            return EmploymentPreference.WAGE_EMPLOYMENT
        return None

    @staticmethod
    def _distance_km(profile: BeneficiaryProfile, opportunity: Opportunity) -> Optional[float]:
        if profile.location is None:
            return None
        points = (profile.location.latitude, profile.location.longitude, opportunity.location.latitude, opportunity.location.longitude)
        if any(point is None for point in points):
            return None
        lat1, lon1, lat2, lon2 = (radians(float(point)) for point in points)
        a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
        return 2 * 6371.0 * asin(sqrt(a))

    def _opportunity_accessible(self, profile: BeneficiaryProfile, opportunity: Opportunity) -> bool:
        """Filter only known distance/location violations; missing data stays unknown."""
        distance = self._distance_km(profile, opportunity)
        if distance is not None and profile.max_travel_distance_km is not None:
            return distance <= profile.max_travel_distance_km
        if profile.willingness_to_travel is False and profile.location is not None:
            return (profile.location.state.casefold() == opportunity.location.state.casefold()
                    and profile.location.district.casefold() == opportunity.location.district.casefold())
        return True

    def _course_eligibility(self, profile: BeneficiaryProfile, course: Optional[NSQFCourse], supplied: Optional[EligibilityResult]) -> EligibilityResult:
        if supplied is not None:
            return supplied
        if course is None or course.required_education is None:
            return EligibilityResult(scheme_name="No explicit eligibility rule supplied", status=EligibilityStatus.UNKNOWN,
                                     explanation="No explicit eligibility constraint is available for this pathway.")
        required = course.required_education
        if (profile.education_level == EducationLevel.UNKNOWN
                or profile.education_level not in _EDUCATION_ORDER
                or required not in _EDUCATION_ORDER):
            criterion = CriterionResult(criterion_id=f"EDU-{course.course_id}", name="Minimum education",
                                        status=EligibilityStatus.UNKNOWN, reason="Beneficiary education level cannot be compared to the course requirement.")
            return EligibilityResult(scheme_name=course.course_name, status=EligibilityStatus.UNKNOWN,
                                     unknown_criteria=[criterion], explanation="Education eligibility cannot be verified.")
        eligible = _EDUCATION_ORDER.get(profile.education_level, -1) >= _EDUCATION_ORDER.get(required, -1)
        criterion = CriterionResult(criterion_id=f"EDU-{course.course_id}", name="Minimum education",
                                    status=EligibilityStatus.ELIGIBLE if eligible else EligibilityStatus.INELIGIBLE,
                                    reason=f"Course requires {required.value}; profile records {profile.education_level.value}.")
        return EligibilityResult(scheme_name=course.course_name, status=criterion.status, overall_score=1.0 if eligible else 0.0,
                                 matched_criteria=[criterion] if eligible else [], unmet_criteria=[] if eligible else [criterion],
                                 explanation="Education requirement is satisfied." if eligible else "Education requirement is not satisfied.")

    def generate_candidates(self, request: RecommendationRequest) -> list[RecommendationCandidate]:
        """Join occupation, course, and active opportunity records after hard filters."""
        if request.eligibility_result and request.eligibility_result.status == EligibilityStatus.INELIGIBLE:
            return []
        candidates: list[RecommendationCandidate] = []
        active = [item for item in self._opportunities.list_all() if item.lifecycle_status == OpportunityLifecycle.ACTIVE]
        for occupation in sorted(self._occupations.list_all(), key=lambda item: item.occupation_id):
            if request.target_sector and occupation.sector.casefold() != request.target_sector.casefold():
                continue
            preference = request.profile.employment_preference
            expected = self._employment_preference(occupation)
            if (preference not in {EmploymentPreference.UNKNOWN, EmploymentPreference.ANY, EmploymentPreference.HOME_BASED}
                    and expected is not None and preference != expected):
                continue
            if request.preferred_pathway == PathwayType.APPRENTICESHIP and occupation.employment_type != EmploymentType.APPRENTICESHIP:
                continue
            courses = [course for course in self._courses.list_all()
                       if course.course_id in occupation.nsqf_qualification_ids or occupation.occupation_id in course.job_roles] or [None]
            opportunities = tuple(sorted((opportunity for opportunity in active
                                          if opportunity.sector.casefold() == occupation.sector.casefold()
                                          and self._opportunity_accessible(request.profile, opportunity)), key=lambda item: item.opportunity_id))
            for course in sorted(courses, key=lambda item: item.course_id if item else ""):
                if self._course_eligibility(request.profile, course, request.eligibility_result).status != EligibilityStatus.INELIGIBLE:
                    candidates.append(RecommendationCandidate(occupation, course, opportunities))
        return candidates

    def _profile_skill_ids(self, profile: BeneficiaryProfile) -> set[str]:
        skills = {skill.skill_id for skill in profile.normalized_skills}
        for raw_skill in profile.traditional_skills:
            result = self._normalizer.normalize(raw_skill)
            if result.canonical_skill_id:
                skills.add(result.canonical_skill_id)
        return skills

    @staticmethod
    def _required_skills(candidate: RecommendationCandidate) -> set[str]:
        skills = set(candidate.occupation.required_skills)
        if candidate.course:
            skills.update(candidate.course.required_skills)
        for opportunity in candidate.opportunities:
            skills.update(opportunity.required_skills)
        return skills

    def _interest_score(self, profile: BeneficiaryProfile, candidate: RecommendationCandidate) -> float:
        interests = [*profile.interests, *profile.aspirations]
        if not interests:
            return 0.0
        target = self._key(" ".join(filter(None, [candidate.occupation.name, *candidate.occupation.aliases, candidate.occupation.sector,
                                                    candidate.course.course_name if candidate.course else "", candidate.course.qualification_name if candidate.course else ""])))
        return sum(bool(self._key(item) and self._key(item) in target) for item in interests) / len(interests)

    @staticmethod
    def _eligibility_score(result: EligibilityResult) -> float:
        return 1.0 if result.status == EligibilityStatus.ELIGIBLE else 0.0

    def _local_opportunity_score(self, profile: BeneficiaryProfile, opportunities: Iterable[Opportunity]) -> float:
        if profile.location is None:
            return 0.0
        return float(any(opportunity.location.state.casefold() == profile.location.state.casefold()
                         and opportunity.location.district.casefold() == profile.location.district.casefold() for opportunity in opportunities))

    @staticmethod
    def _labour_demand_score(candidate: RecommendationCandidate) -> float:
        """No labour-demand repository exists yet; absent observed data scores zero."""
        return 0.0

    def _preference_score(self, profile: BeneficiaryProfile, candidate: RecommendationCandidate) -> float:
        expected = self._employment_preference(candidate.occupation)
        return float(profile.employment_preference == expected) if expected is not None else 0.0

    @staticmethod
    def _collect_evidence(profile: BeneficiaryProfile, candidate: RecommendationCandidate, eligibility: EligibilityResult) -> list[SourceEvidence]:
        evidence = [*profile.evidence]
        if candidate.occupation.source_metadata:
            evidence.append(candidate.occupation.source_metadata)
        if candidate.course and candidate.course.source_metadata:
            evidence.append(candidate.course.source_metadata)
        for opportunity in candidate.opportunities:
            if opportunity.source:
                evidence.append(opportunity.source)
            evidence.extend(opportunity.evidence)
        evidence.extend(eligibility.evidence)
        evidence.extend(item.evidence for item in (*eligibility.matched_criteria, *eligibility.unmet_criteria, *eligibility.unknown_criteria) if item.evidence)
        return list({item.source_id: item for item in evidence}.values())

    def _recommendation(self, request: RecommendationRequest, candidate: RecommendationCandidate) -> Recommendation:
        profile = request.profile
        eligibility = self._course_eligibility(profile, candidate.course, request.eligibility_result)
        known, required = self._profile_skill_ids(profile), self._required_skills(candidate)
        matched, missing = sorted(known & required), sorted(required - known)
        skill_score = len(matched) / len(required) if required else 0.0
        interest, local = self._interest_score(profile, candidate), self._local_opportunity_score(profile, candidate.opportunities)
        demand, preference, eligibility_score = self._labour_demand_score(candidate), self._preference_score(profile, candidate), self._eligibility_score(eligibility)
        scores = {"interest": interest, "skill": skill_score, "eligibility": eligibility_score, "local_opportunity": local,
                  "labour_demand": demand, "employment_preference": preference}
        overall = round(sum(scores[name] * self._weights[name] for name in scores), 6)
        gaps = [SkillGap(skill_id=skill_id, skill_name=(self._skills.get_by_id(skill_id).name if self._skills.get_by_id(skill_id) else skill_id),
                         gap_status=GapStatus.MISSING, priority=PriorityLevel.MEDIUM) for skill_id in missing]
        known_components = sum((bool(profile.interests or profile.aspirations), bool(required), eligibility.status != EligibilityStatus.UNKNOWN,
                                profile.location is not None, False, profile.employment_preference not in {EmploymentPreference.UNKNOWN, EmploymentPreference.ANY}))
        pathway = (PathwayType.APPRENTICESHIP if candidate.occupation.employment_type == EmploymentType.APPRENTICESHIP else
                   PathwayType.COMBINED if candidate.course and candidate.opportunities else
                   PathwayType.SKILL_TRAINING if candidate.course else PathwayType.DIRECT_EMPLOYMENT)
        return Recommendation(
            recommendation_id=f"REC-{candidate.occupation.occupation_id}-{candidate.course.course_id if candidate.course else 'NONE'}", pathway_type=pathway,
            occupation_reference=candidate.occupation.occupation_id, target_occupation=candidate.occupation,
            course_reference=candidate.course.course_id if candidate.course else None, target_course=candidate.course,
            opportunity_references=[item.opportunity_id for item in candidate.opportunities], associated_opportunities=list(candidate.opportunities),
            overall_score=overall,
            score_breakdown=ScoreBreakdown(interest_similarity_score=interest, skill_match_score=skill_score, eligibility_score=eligibility_score,
                                           local_opportunity_score=local, labour_demand_score=demand, employment_preference_score=preference,
                                           local_demand_score=demand, preference_alignment_score=preference),
            eligibility_result=eligibility, matched_skills=matched, skill_gaps=gaps, local_demand_signal=None,
            confidence=round(known_components / 6, 6),
            explanation=(f"{candidate.occupation.name}: {len(matched)} matched and {len(missing)} missing canonical skills. "
                         f"Eligibility is {eligibility.status.value}; unavailable signals are not assumed."),
            model_version=self._model_version, evidence=self._collect_evidence(profile, candidate, eligibility),
        )

    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        recommendations = [self._recommendation(request, candidate) for candidate in self.generate_candidates(request)]
        recommendations.sort(key=lambda item: (-item.overall_score, item.occupation_reference or "", item.course_reference or ""))
        recommendations = recommendations[:min(3, request.max_recommendations)]
        for rank, recommendation in enumerate(recommendations, start=1):
            recommendation.rank = rank
        return RecommendationResponse(candidate_id=request.profile.beneficiary_id, recommendations=recommendations,
                                      total_found=len(recommendations), status="completed")
