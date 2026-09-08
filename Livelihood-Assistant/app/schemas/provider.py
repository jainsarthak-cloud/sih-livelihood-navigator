"""
Training provider / training partner master-data schema.

A TrainingProvider is any accredited institution that delivers NSQF-aligned
skilling programs. This includes NSDC Training Partners (TPs), State Govt
institutes, ITIs, and private vocational training institutes.

Do NOT populate with real accreditation numbers or real provider names.
This schema is ready for authoritative NSDC/NCVT provider registry ingestion.
"""

from enum import Enum
from typing import List, Optional

from pydantic import Field

from app.schemas.common import GeographicLocation, SourceEvidence
from app.schemas.ontology import OntologyRecord, DataClassification


class ProviderType(str, Enum):
    NSDC_TRAINING_PARTNER = "nsdc_training_partner"
    STATE_GOVT_ITI = "state_govt_iti"
    CENTRAL_GOVT = "central_govt"
    PRIVATE_INSTITUTE = "private_institute"
    NGO = "ngo"
    COMMUNITY_SKILL_CENTRE = "community_skill_centre"
    UNKNOWN = "unknown"


class AccreditationStatus(str, Enum):
    ACCREDITED = "accredited"
    PROVISIONAL = "provisional"
    EXPIRED = "expired"
    UNDER_REVIEW = "under_review"
    NOT_ACCREDITED = "not_accredited"
    UNKNOWN = "unknown"


class TrainingProvider(OntologyRecord):
    """
    Master record for an accredited training partner or vocational institute.

    Future authoritative ingestion: NSDC Training Partner portal,
    NCVT MIS, and state SLMC directories.
    """

    provider_id: str = Field(
        ...,
        description="Canonical provider identifier (e.g. PRV-NSDC-001)",
    )
    name: str = Field(..., description="Official registered name of the provider")
    provider_type: ProviderType = Field(
        default=ProviderType.UNKNOWN,
        description="Category of training provider",
    )
    accreditation_id: Optional[str] = Field(
        default=None,
        description=(
            "Official accreditation or registration number. "
            "Must only be populated from authoritative registry sources."
        ),
    )
    accreditation_status: AccreditationStatus = Field(
        default=AccreditationStatus.UNKNOWN,
        description="Current accreditation status of the provider",
    )
    location: Optional[GeographicLocation] = Field(
        default=None,
        description="Primary location of the training centre",
    )
    courses_offered: List[str] = Field(
        default_factory=list,
        description="Canonical course IDs (CRS-*) offered by this provider",
    )
    sectors_covered: List[str] = Field(
        default_factory=list,
        description="Industry sectors or Skill Councils this provider is affiliated with",
    )
    contact_info: Optional[str] = Field(
        default=None,
        description="Official contact details (email / phone). Redact PII if necessary.",
    )
    source_evidence: Optional[SourceEvidence] = Field(
        default=None,
        description="Authoritative registry reference for this provider record",
    )
    data_classification: DataClassification = Field(
        default=DataClassification.SYNTHETIC,
        description="Classification label (SYNTHETIC for demo, INGESTED for authoritative data)",
    )
