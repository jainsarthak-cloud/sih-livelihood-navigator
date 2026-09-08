"""Location-scoped opportunity observation counts, not inferred market forecasts."""

from abc import ABC, abstractmethod

from app.data.repositories.domain_repositories import OpportunityRepository
from app.schemas.common import VerificationStatus
from app.schemas.market import DemandEvidenceStatus, MarketDemandRequest, MarketDemandResponse, SectorDemand
from app.schemas.opportunity import OpportunityLifecycle
from app.services.opportunity.intelligence import OpportunityIntelligenceService


class BaseMarketDemandService(ABC):
    @abstractmethod
    async def analyze_demand(self, request: MarketDemandRequest) -> MarketDemandResponse:
        """Summarize recorded local opportunity observations without forecasting demand."""


class MarketDemandService(BaseMarketDemandService):
    """Creates transparent counts from active records in the configured repository scope."""

    def __init__(self, opportunity_repository: OpportunityRepository, intelligence_service: OpportunityIntelligenceService):
        self._opportunities = opportunity_repository
        self._intelligence = intelligence_service

    @staticmethod
    def _evidence(opportunities):
        evidence = []
        for opportunity in opportunities:
            if opportunity.source:
                evidence.append(opportunity.source)
            evidence.extend(opportunity.evidence)
        return list({item.source_id: item for item in evidence}.values())

    async def analyze_demand(self, request: MarketDemandRequest) -> MarketDemandResponse:
        observed = [
            opportunity for opportunity in self._opportunities.list_all()
            if opportunity.lifecycle_status == OpportunityLifecycle.ACTIVE
            and opportunity.location.state.casefold() == request.state.casefold()
            and opportunity.location.district.casefold() == request.district.casefold()
            and (request.sector_filter is None or opportunity.sector.casefold() == request.sector_filter.casefold())
        ]
        if not observed:
            return MarketDemandResponse(
                state=request.state, district=request.district,
                limitations=["No active opportunity observations exist in the configured repository for this location and filter; market demand is unknown."],
                status="completed",
            )
        sectors = []
        for sector in sorted({opportunity.sector for opportunity in observed}, key=str.casefold):
            opportunities = [item for item in observed if item.sector == sector]
            occupation_ids = []
            for opportunity in opportunities:
                mappings = self._intelligence.occupation_matches(opportunity)
                if len(mappings) == 1:
                    occupation_ids.append(mappings[0].occupation_id)
            skills = sorted({skill for item in opportunities for skill in item.required_skills})
            verified = sum(item.verification_status == VerificationStatus.VERIFIED for item in opportunities)
            synthetic = all(item.is_synthetic for item in opportunities)
            sectors.append(SectorDemand(
                sector_name=sector, evidence_status=DemandEvidenceStatus.OBSERVED,
                active_opportunity_count=len(opportunities), verified_active_opportunity_count=verified,
                top_in_demand_roles=sorted(set(occupation_ids)), observed_skill_ids=skills,
                evidence=self._evidence(opportunities),
                scope_note=("Counts are observations of active synthetic/demo opportunity records in the configured in-memory repository; they are not a market-demand estimate."
                            if synthetic else "Counts are observations of active opportunity records in the configured repository; they are not a market-demand estimate."),
            ))
        limitations = ["Opportunity counts describe only records in the configured repository and do not establish statistical market demand or a trend."]
        if any(item.is_synthetic for item in observed):
            limitations.append("Synthetic/demo records are included and must not be treated as production labor-market evidence.")
        return MarketDemandResponse(
            state=request.state, district=request.district, top_sectors=sectors,
            limitations=limitations, evidence=self._evidence(observed), status="completed",
        )
