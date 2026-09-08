"""Common Pydantic models, wrappers, geographic types, source evidence, and core enums."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class ServiceStatus(str, Enum):
    READY = "ready"
    NOT_IMPLEMENTED = "not_implemented"
    ERROR = "error"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    TRANSGENDER = "transgender"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    UNKNOWN = "unknown"


class EducationLevel(str, Enum):
    NONE = "none"
    PRIMARY = "primary"  # 1st - 5th
    MIDDLE = "middle"  # 6th - 8th
    SECONDARY_10TH = "secondary_10th"
    HIGHER_SECONDARY_12TH = "higher_secondary_12th"
    DIPLOMA = "diploma"
    ITI = "iti"
    GRADUATE = "graduate"
    POST_GRADUATE = "post_graduate"
    OTHER = "other"
    UNKNOWN = "unknown"


class EmploymentPreference(str, Enum):
    WAGE_EMPLOYMENT = "wage_employment"
    SELF_EMPLOYMENT = "self_employment"
    APPRENTICESHIP = "apprenticeship"
    HOME_BASED = "home_based"
    ANY = "any"
    UNKNOWN = "unknown"


class ProfileSource(str, Enum):
    VOICE_INTERVIEW = "voice_interview"
    TEXT_INPUT = "text_input"
    FIELD_WORKER_SURVEY = "field_worker_survey"
    COUNSELOR_INPUT = "counselor_input"
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"
    PENDING = "pending"


class SourceType(str, Enum):
    OFFICIAL_GAZETTE = "official_gazette"
    NSQF_PORTAL = "nsqf_portal"
    PM_AJAY_GUIDELINES = "pm_ajay_guidelines"
    JOB_PORTAL = "job_portal"
    FIELD_SURVEY = "field_survey"
    VOICE_INTERVIEW = "voice_interview"
    COUNSELOR_INPUT = "counselor_input"
    OTHER = "other"


class GeographicLocation(BaseModel):
    """Geographic location supporting district/block/village and validated coordinates."""

    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    block: Optional[str] = Field(default=None, description="Sub-district / Block / Tehsil")
    village: Optional[str] = Field(default=None, description="Village or Habitation name")
    pincode: Optional[str] = Field(default=None, description="6-digit postal code")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude [-90.0, 90.0]")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude [-180.0, 180.0]")


class SourceEvidence(BaseModel):
    """Reusable source/evidence metadata for traceability of facts, skills, and recommendations."""

    source_id: str = Field(..., description="Unique identifier for the evidence entry")
    source_type: SourceType = Field(..., description="Type/category of source")
    source_name: str = Field(..., description="Name or title of source")
    source_url: Optional[str] = Field(default=None, description="Reference URL when available")
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware collection timestamp",
    )
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="Verification state of this evidence",
    )
    notes: Optional[str] = Field(default=None, description="Additional context or notes")

    @field_validator("collected_at")
    @classmethod
    def validate_tz_aware(cls, dt: datetime) -> datetime:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise ValueError("Timestamp must be timezone-aware (e.g. UTC).")
        return dt


class ErrorDetail(BaseModel):
    message: str
    status_code: int
    details: Optional[dict[str, Any]] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
