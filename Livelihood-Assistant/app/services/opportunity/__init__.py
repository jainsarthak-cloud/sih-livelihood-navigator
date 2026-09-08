"""Opportunity Parser service package."""

from app.services.opportunity.parser import BaseOpportunityParsingService, OpportunityParsingService
from app.services.opportunity.intelligence import OpportunityIntelligenceService

__all__ = ["BaseOpportunityParsingService", "OpportunityParsingService", "OpportunityIntelligenceService"]
