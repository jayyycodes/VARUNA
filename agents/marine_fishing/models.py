"""
Pydantic v2 models for INCOIS PFZ (Potential Fishing Zone) WFS responses.

These models are internal to the marine_fishing agent and are NOT part of
the shared AgentEnvelope contract (backend/schemas/envelope.py).

Owner: Jaish
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry.base import BaseGeometry


class PFZBoundingBox(BaseModel):
    """
    Bounding box for spatial filtering of PFZ features.

    Field names are explicit (min_lat, min_lon, max_lat, max_lon) rather
    than positional tuples, so the INCOIS-specific CQL BBOX axis order
    (min_lat, min_lon, max_lat, max_lon) is structurally impossible to
    get backwards at call sites.
    """

    min_lat: float = Field(
        ..., ge=-90, le=90, description="Southern boundary latitude"
    )
    min_lon: float = Field(
        ..., ge=-180, le=180, description="Western boundary longitude"
    )
    max_lat: float = Field(
        ..., ge=-90, le=90, description="Northern boundary latitude"
    )
    max_lon: float = Field(
        ..., ge=-180, le=180, description="Eastern boundary longitude"
    )

    @model_validator(mode="after")
    def validate_coordinate_ordering(self) -> PFZBoundingBox:
        if self.min_lat >= self.max_lat:
            raise ValueError(
                f"min_lat ({self.min_lat}) must be less than max_lat ({self.max_lat})"
            )
        if self.min_lon >= self.max_lon:
            raise ValueError(
                f"min_lon ({self.min_lon}) must be less than max_lon ({self.max_lon})"
            )
        return self


class PFZOutcome(str, Enum):
    """Discriminated outcome of a PFZ WFS query."""

    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    WFS_ERROR = "WFS_ERROR"
    TRANSIENT_ERROR = "TRANSIENT_ERROR"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


class PFZFeature(BaseModel):
    """
    A single PFZ line feature from the INCOIS WFS response.

    Field names map to the DescribeFeatureType schema for
    PFZ_Automation:pfzlines.  The geometry is a shapely MultiLineString
    (or other shapely geometry — remains multi-part safe).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    geometry: BaseGeometry
    sector_boundary: int | None = None  # SECTORBOUN (xsd:int)
    sector_boundary_1: int | None = None  # SECTORBO_1 (xsd:int)
    sector_name: str | None = None  # SECTORNAME (xsd:string)
    julian_day: str  # Julian_day (3-digit zero-padded string)
    serial_number: str | None = None  # Sno (xsd:string, preserves leading zeros e.g. "001")
    year: int  # Year (xsd:double/int)
    uid: float | None = None  # UID (xsd:double)
    length: float | None = None  # Length (xsd:double)


class PFZQueryResult(BaseModel):
    """
    Discriminated result of a PFZ WFS query.

    Callers should match on ``outcome`` to determine how to handle:

    - ``SUCCESS``:          ``features`` is non-empty, error fields are ``None``
    - ``EMPTY``:            ``features`` is empty list, error fields are ``None``
    - ``WFS_ERROR``:        OGC XML exception; ``exception_code`` / ``exception_text`` populated
    - ``TRANSIENT_ERROR``:  timeout / connection failure after retry exhaustion
    - ``UNEXPECTED_ERROR``: unexpected response format or HTTP error
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    outcome: PFZOutcome
    features: list[PFZFeature] = Field(default_factory=list)

    # Error context — populated for error outcomes only
    error_message: str | None = None
    exception_code: str | None = None  # OGC exceptionCode (WFS_ERROR only)
    exception_text: str | None = None  # OGC exceptionText (WFS_ERROR only)

    # Diagnostics
    attempts: int = 1
