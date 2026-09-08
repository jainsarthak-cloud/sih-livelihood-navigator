"""
Standalone LocationRecord master-data schema.

Distinct from the embedded GeographicLocation used inside profile/opportunity models.
LocationRecord is a first-class queryable master-data entity with canonical ID,
full administrative hierarchy, optional coordinates, and provenance.

Architecture note:
- GeographicLocation (common.py) is an embedded value object used inline in other models.
- LocationRecord (this file) is a standalone master record in the location registry.

Do NOT fabricate geographic coordinates.
This schema is ready for authoritative location dataset ingestion (e.g. LGD codes).
"""

from typing import List, Optional

from pydantic import Field

from app.schemas.common import GeographicLocation
from app.schemas.ontology import OntologyRecord, DataClassification


class LocationRecord(OntologyRecord):
    """
    Canonical location master record.

    Supports the full Indian administrative hierarchy:
    Country → State → District → Block → Village

    Future authoritative ingestion: Local Government Directory (LGD) codes
    published by the Ministry of Panchayati Raj.  The external_id field should
    be used to store the LGD code for cross-reference.
    """

    location_id: str = Field(
        ...,
        description="Canonical location identifier (e.g. LOC-UP-VAR-001)",
    )
    country: str = Field(
        default="India", description="Country name (default: India)"
    )
    state: str = Field(..., description="State or Union Territory name")
    district: str = Field(..., description="District name")
    block: Optional[str] = Field(
        default=None, description="Block / Sub-district / Tehsil name"
    )
    village: Optional[str] = Field(
        default=None, description="Village or habitation name"
    )
    pincode: Optional[str] = Field(
        default=None, description="6-digit postal code"
    )
    latitude: Optional[float] = Field(
        default=None, ge=-90.0, le=90.0, description="Latitude [-90.0, 90.0]"
    )
    longitude: Optional[float] = Field(
        default=None, ge=-180.0, le=180.0, description="Longitude [-180.0, 180.0]"
    )
    lgd_state_code: Optional[str] = Field(
        default=None,
        description="LGD (Local Government Directory) state code for authoritative cross-reference",
    )
    lgd_district_code: Optional[str] = Field(
        default=None,
        description="LGD district code for authoritative cross-reference",
    )
    languages_spoken: List[str] = Field(
        default_factory=list,
        description="Primary languages spoken in this location (ISO codes)",
    )
    data_classification: DataClassification = Field(
        default=DataClassification.SYNTHETIC,
        description="Classification label (SYNTHETIC for demo, INGESTED for authoritative data)",
    )

    def to_geographic_location(self) -> GeographicLocation:
        """Convert to an embeddable GeographicLocation value object."""
        return GeographicLocation(
            state=self.state,
            district=self.district,
            block=self.block,
            village=self.village,
            pincode=self.pincode,
            latitude=self.latitude,
            longitude=self.longitude,
        )
