"""Phase 11 orchestration over existing deterministic services.

This layer intentionally performs no extraction, scoring, normalization, or
roadmap logic of its own. It only coordinates existing service contracts.
"""

from app.core.config import Settings, settings
from app.schemas.livelihood import (
    LivelihoodAssessRequest,
    LivelihoodAssessResponse,
    LivelihoodAssessmentMetadata,
    LivelihoodPathwayAssessment,
)
from app.schemas.market import MarketDemandRequest
from app.schemas.opportunity import OpportunityMatchRequest
from app.schemas.recommendation import RecommendationRequest
from app.schemas.roadmap import RoadmapRequest
from app.services.market.demand import MarketDemandService
from app.services.opportunity.intelligence import OpportunityIntelligenceService
from app.services.recommendation.recommender import RecommendationService
from app.services.roadmap.generator import RoadmapService


class LivelihoodAssessmentService:
    """Coordinates the existing services using one profile and repository snapshot."""

    def __init__(
        self,
        recommendation_service: RecommendationService,
        opportunity_service: OpportunityIntelligenceService,
        market_service: MarketDemandService,
        roadmap_service: RoadmapService,
        config: Settings = settings,
    ):
        self._recommendations = recommendation_service
        self._opportunities = opportunity_service
        self._market = market_service
        self._roadmaps = roadmap_service
        self._version = config.LIVELIHOOD_ASSESSMENT_VERSION
        self._recommendation_version = config.RECOMMENDATION_MODEL_VERSION

    @staticmethod
    def _dedupe_evidence(evidence):
        return list({item.source_id: item for item in evidence}.values())

    @staticmethod
    def _profile_limitations(profile):
        limitations = []
        if not profile.normalized_skills and not profile.traditional_skills:
            limitations.append("Beneficiary canonical skills are unknown; skill suitability and gaps remain incomplete.")
        if profile.location is None:
            limitations.append("Beneficiary location is unknown; local opportunity and market observations are unavailable.")
        if profile.education_level.value == "unknown":
            limitations.append("Beneficiary education is unknown; course eligibility may be unknown.")
        return limitations

    async def assess(self, request: LivelihoodAssessRequest) -> LivelihoodAssessResponse:
        profile = request.profile
        limitations = self._profile_limitations(profile)
        recommendation_response = await self._recommendations.get_recommendations(RecommendationRequest(
            profile=profile, target_sector=request.target_sector,
            preferred_pathway=request.preferred_pathway,
            eligibility_result=request.eligibility_result,
            max_recommendations=request.max_recommendations,
        ))
        local_matches_response = await self._opportunities.match_opportunities(OpportunityMatchRequest(
            profile=profile, eligibility_result=request.eligibility_result,
        ))
        limitations.extend(local_matches_response.limitations)
        market = None
        if profile.location:
            market = await self._market.analyze_demand(MarketDemandRequest(
                state=profile.location.state, district=profile.location.district,
                sector_filter=request.target_sector,
            ))
            limitations.extend(market.limitations)
        pathways = []
        evidence = [*profile.evidence]
        for recommendation in recommendation_response.recommendations:
            matching = [
                match for match in local_matches_response.matches
                if not recommendation.occupation_reference
                or match.canonical_occupation_id == recommendation.occupation_reference
            ]
            roadmap_response = await self._roadmaps.generate_roadmap(RoadmapRequest(
                profile=profile, recommendation=recommendation,
            ))
            pathway_limits = []
            if roadmap_response.roadmap is None:
                pathway_limits.append("No canonical roadmap target was available for this recommendation.")
            else:
                pathway_limits.extend(roadmap_response.roadmap.limitations)
                evidence.extend(roadmap_response.roadmap.evidence)
            evidence.extend(recommendation.evidence)
            for match in matching:
                evidence.extend(match.evidence)
                pathway_limits.extend(match.limitations)
            pathways.append(LivelihoodPathwayAssessment(
                recommendation=recommendation, opportunity_matches=matching,
                roadmap=roadmap_response.roadmap, limitations=list(dict.fromkeys(pathway_limits)),
            ))
        if not recommendation_response.recommendations:
            limitations.append("No eligible canonical livelihood pathways were found for the structured profile and filters.")
        if market:
            evidence.extend(market.evidence)
        for match in local_matches_response.matches:
            evidence.extend(match.evidence)
        metadata = LivelihoodAssessmentMetadata(
            assessment_version=self._version,
            recommendation_model_version=self._recommendation_version,
            services=["phase-4-skill-normalization", "phase-5-recommendation", "phase-9-roadmap", "phase-10-opportunity-intelligence", "phase-10-market-observations"],
        )
        return LivelihoodAssessResponse(
            profile=profile, pathways=pathways,
            local_opportunity_evidence=local_matches_response.matches,
            market_observation=market, evidence=self._dedupe_evidence(evidence),
            limitations=list(dict.fromkeys(limitations)), metadata=metadata,
            status="completed" if pathways else "incomplete_or_no_pathway",
        )
