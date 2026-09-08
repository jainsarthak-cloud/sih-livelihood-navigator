"""Evidence-backed local opportunity matching over canonical repositories."""

from math import asin, cos, radians, sin, sqrt

from app.data.repositories.domain_repositories import OccupationRepository, OpportunityRepository
from app.schemas.common import EmploymentPreference
from app.schemas.eligibility import EligibilityStatus
from app.schemas.occupation import EmploymentType, Occupation
from app.schemas.opportunity import (
    Opportunity,
    OpportunityLifecycle,
    OpportunityMatch,
    OpportunityMatchRequest,
    OpportunityMatchResponse,
    OpportunityType,
)
from app.services.normalization.skill_normalizer import SkillNormalizationService


class OpportunityIntelligenceService:
    """Filters only on recorded lifecycle, profile preferences, location, and skills."""

    def __init__(
        self, opportunity_repository: OpportunityRepository, occupation_repository: OccupationRepository,
        skill_normalizer: SkillNormalizationService,
    ):
        self._opportunities = opportunity_repository
        self._occupations = occupation_repository
        self._normalizer = skill_normalizer

    @staticmethod
    def _distance_km(profile_location, opportunity_location):
        points = (profile_location.latitude, profile_location.longitude,
                  opportunity_location.latitude, opportunity_location.longitude)
        if any(point is None for point in points):
            return None
        lat1, lon1, lat2, lon2 = (radians(float(point)) for point in points)
        value = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
        return 2 * 6371.0 * asin(sqrt(value))

    @staticmethod
    def _preference_for(opportunity: Opportunity):
        return {
            OpportunityType.WAGE_EMPLOYMENT: EmploymentPreference.WAGE_EMPLOYMENT,
            OpportunityType.SELF_EMPLOYMENT: EmploymentPreference.SELF_EMPLOYMENT,
            OpportunityType.APPRENTICESHIP: EmploymentPreference.APPRENTICESHIP,
        }.get(opportunity.opportunity_type)

    def _profile_skill_ids(self, profile):
        ids = {skill.skill_id for skill in profile.normalized_skills}
        for raw in profile.traditional_skills:
            normalized = self._normalizer.normalize(raw)
            if normalized.canonical_skill_id:
                ids.add(normalized.canonical_skill_id)
        return ids

    def occupation_matches(self, opportunity: Opportunity) -> list[Occupation]:
        """Use sector plus required-skill compatibility; collisions are left unknown."""
        opportunity_skills = set(opportunity.required_skills)
        return [
            occupation for occupation in self._occupations.find_by_sector(opportunity.sector)
            if not opportunity_skills or opportunity_skills.issubset(set(occupation.required_skills))
        ]

    def _location_match(self, profile, opportunity: Opportunity):
        if profile.location is None:
            return None, []
        same_district = (profile.location.state.casefold() == opportunity.location.state.casefold()
                         and profile.location.district.casefold() == opportunity.location.district.casefold())
        distance = self._distance_km(profile.location, opportunity.location)
        if distance is not None and profile.max_travel_distance_km is not None and distance > profile.max_travel_distance_km:
            return False, []
        if profile.willingness_to_travel is False and not same_district:
            return False, []
        limitations = []
        if distance is None and profile.max_travel_distance_km is not None:
            limitations.append("Distance radius could not be evaluated because coordinates are unavailable.")
        if distance is None:
            return True if same_district else None, limitations
        if profile.max_travel_distance_km is None:
            return True if same_district else None, limitations
        return True, limitations

    @staticmethod
    def _evidence(opportunity):
        evidence = ([opportunity.source] if opportunity.source else []) + list(opportunity.evidence)
        return list({item.source_id: item for item in evidence}.values())

    async def match_opportunities(self, request: OpportunityMatchRequest) -> OpportunityMatchResponse:
        if request.eligibility_result and request.eligibility_result.status == EligibilityStatus.INELIGIBLE:
            return OpportunityMatchResponse(limitations=["Explicit eligibility result is ineligible; no opportunities were returned."], status="completed")
        profile_skills = self._profile_skill_ids(request.profile)
        matches = []
        global_limits = []
        if not profile_skills:
            global_limits.append("Beneficiary canonical skills are unknown; skill suitability cannot be confirmed.")
        if request.profile.location is None:
            global_limits.append("Beneficiary location is unknown; local relevance cannot be confirmed.")
        allowed_lifecycle = {OpportunityLifecycle.ACTIVE}
        if request.include_reported:
            allowed_lifecycle.add(OpportunityLifecycle.REPORTED)
        for opportunity in sorted(self._opportunities.list_all(), key=lambda item: item.opportunity_id):
            if opportunity.lifecycle_status not in allowed_lifecycle:
                continue
            expected_preference = self._preference_for(opportunity)
            preference = request.profile.employment_preference
            if (preference not in {EmploymentPreference.UNKNOWN, EmploymentPreference.ANY, EmploymentPreference.HOME_BASED}
                    and expected_preference is not None and preference != expected_preference):
                continue
            occupations = self.occupation_matches(opportunity)
            if request.occupation_id and all(item.occupation_id != request.occupation_id for item in occupations):
                continue
            location_match, limitations = self._location_match(request.profile, opportunity)
            if location_match is False:
                continue
            if len(occupations) > 1:
                limitations.append("Occupation mapping is ambiguous for this opportunity.")
            if not occupations:
                limitations.append("No canonical occupation mapping is supported by this opportunity's sector and skills.")
            required = set(opportunity.required_skills)
            matches.append(OpportunityMatch(
                opportunity=opportunity,
                canonical_occupation_id=occupations[0].occupation_id if len(occupations) == 1 else None,
                matched_skill_ids=sorted(profile_skills & required),
                missing_skill_ids=sorted(required - profile_skills) if profile_skills else [],
                location_match=location_match, limitations=limitations, evidence=self._evidence(opportunity),
            ))
        return OpportunityMatchResponse(matches=matches, total_matches=len(matches), limitations=global_limits, status="completed")
