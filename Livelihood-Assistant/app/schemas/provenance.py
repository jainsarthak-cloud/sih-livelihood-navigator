"""
Data source registry and provenance models.

Every imported master/operational record must be traceable to a DataSourceRecord.
Provenance is a first-class concern — conflicting sources must never be silently merged.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SourceType, VerificationStatus


class SourcePrecedence(str, Enum):
    """
    Precedence ranking when multiple sources provide conflicting definitions.

    Lower number = higher authority.  When two sources conflict, keep the record
    from the source with the lowest precedence rank and log the conflict in
    conflict_notes.  Do NOT silently merge differing definitions.
    """

    OFFICIAL_GOVERNMENT = "official_government"  # Gazettes, MoLE, MSDE, NSDA
    NSQF_PORTAL = "nsqf_portal"  # NQR / NSDC QP database
    SECTOR_SKILL_COUNCIL = "sector_skill_council"  # SSC published NOS
    STATE_GOVERNMENT = "state_government"  # State gazettes, SLMC circulars
    FIELD_SURVEY = "field_survey"  # Directly collected from beneficiaries
    SYNTHETIC_DEMO = "synthetic_demo"  # Demo / test data — NOT authoritative
    UNKNOWN = "unknown"


class DataSourceRecord(BaseModel):
    """
    Registry entry for an authoritative or observational data source.

    All master-data records must reference a DataSourceRecord via source_id.
    This enables full lineage tracking and conflict resolution.
    """

    source_id: str = Field(
        ...,
        description="Unique identifier for this source registry entry (e.g. SRC-GOI-001)",
    )
    source_name: str = Field(
        ..., description="Human-readable title of the source publication or dataset"
    )
    source_type: SourceType = Field(
        ..., description="Broad category of the source (gazette, portal, survey, etc.)"
    )
    publisher: Optional[str] = Field(
        default=None,
        description="Organisation or ministry responsible for publishing this source",
    )
    url: Optional[str] = Field(
        default=None, description="Canonical URL or document reference when available"
    )
    version: Optional[str] = Field(
        default=None,
        description="Version or edition of the source document (e.g. '2024-Q1')",
    )
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware timestamp when this source was registered",
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="Verification state of the source itself",
    )
    precedence: SourcePrecedence = Field(
        default=SourcePrecedence.UNKNOWN,
        description="Authority rank of this source for conflict resolution",
    )
    conflict_notes: Optional[str] = Field(
        default=None,
        description=(
            "Notes on known conflicts with other sources. "
            "Must be populated when a record from this source contradicts another. "
            "Do NOT silently merge conflicting definitions."
        ),
    )
    notes: Optional[str] = Field(
        default=None, description="Additional context, caveats, or metadata"
    )

    @field_validator("collected_at")
    @classmethod
    def validate_tz_aware(cls, dt: datetime) -> datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise ValueError("collected_at must be timezone-aware (e.g. UTC).")
        return dt
