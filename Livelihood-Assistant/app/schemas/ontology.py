"""
Ontology base model and identifier strategy documentation.

All master-data records (Skill, Occupation, NSQFCourse, etc.) extend OntologyRecord
to guarantee uniform identifier format, data classification, and versioning fields.

Identifier Strategy
-------------------
Canonical identifiers follow a structured prefix scheme:

  Domain      | Prefix    | Example
  ------------|-----------|----------------------------
  Skill       | SKL-      | SKL-TEX-001
  Occupation  | OCC-      | OCC-SOL-001
  Course/QP   | CRS-      | CRS-NSQF-401
  Sector      | SEC-      | SEC-GREEN-01
  Job Role    | ROLE-     | ROLE-SOL-INST
  Location    | LOC-      | LOC-UP-VAR-01
  Provider    | PRV-      | PRV-NSDC-001
  Opportunity | OPP-      | OPP-VAR-101
  Source      | SRC-      | SRC-GOI-001

Rules:
1. IDs are IMMUTABLE once assigned — never reuse a retired ID.
2. IDs must be ASCII, uppercase, hyphen-separated, max 32 chars.
3. Synthetic/demo records use the infix SYN: SKL-SYN-001, OCC-SYN-002, etc.
4. Future authoritative dataset ingestion must map external IDs to this scheme
   and store the original external ID in the `external_id` field for cross-reference.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    """
    Classification label for all data records.

    SYNTHETIC: Test / demo data.  Must NEVER be used in production outputs.
    INGESTED:  Imported from an authoritative source; traceability required.
    OBSERVED:  Field-collected observation data (surveys, interviews).
    DERIVED:   Computed or inferred by the AI engine from other records.
    """

    SYNTHETIC = "SYNTHETIC"
    INGESTED = "INGESTED"
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"


class OntologyRecord(BaseModel):
    """
    Common base for all master-data ontology records.

    Provides: data classification, synthetic flag, version tracking, and
    external ID cross-reference for authoritative dataset ingestion.
    """

    record_version: str = Field(
        default="1.0",
        description=(
            "Semantic version of this record (e.g. '1.0', '2.1'). "
            "Increment the minor version when a field is updated; "
            "increment major when the identity changes."
        ),
    )
    data_classification: DataClassification = Field(
        default=DataClassification.SYNTHETIC,
        description=(
            "Classification label. All SYNTHETIC records must be excluded "
            "from production recommendation outputs."
        ),
    )
    is_synthetic: bool = Field(
        default=True,
        description=(
            "True for all demo/test records. Must be set to False only after "
            "authoritative dataset ingestion and human review."
        ),
    )
    external_id: Optional[str] = Field(
        default=None,
        description=(
            "Original identifier from the authoritative source system "
            "(e.g. NSDC QP code, NIC occupation code). "
            "Preserved for cross-reference; do not use as primary key."
        ),
    )
    source_id: Optional[str] = Field(
        default=None,
        description=(
            "Reference to a DataSourceRecord.source_id that documents "
            "the authority and provenance of this record."
        ),
    )
