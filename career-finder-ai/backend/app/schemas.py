"""
schemas.py – Pydantic models for request and response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    """Input for the /parse endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        description="Free-text student message describing their profile and needs.",
        examples=["I am a cybersecurity student in Dammam looking for remote COOP"],
    )


class RecommendRequest(BaseModel):
    """Input for the /recommend endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        description="Free-text student message used to derive filters and recommendations.",
        examples=["I am a data science student in Riyadh looking for an on-site internship"],
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ParsedProfile(BaseModel):
    """Structured student profile extracted from a free-text message."""

    major: Optional[str] = Field(None, description="Detected academic major code.")
    city: Optional[str] = Field(None, description="Detected preferred city.")
    interest: Optional[str] = Field(None, description="Detected area of interest.")
    work_mode: Optional[str] = Field(None, description="Remote, On-site, or Hybrid.")
    program_type: Optional[str] = Field(None, description="COOP or Internship.")
    skills: List[str] = Field(default_factory=list, description="List of detected skills.")


class Opportunity(BaseModel):
    """A single COOP/internship opportunity."""

    id: int
    company: str
    title: str
    city: str
    work_mode: str
    program_type: str
    major_fit: List[str] = Field(default_factory=list)
    source_url: str
    score: float = Field(0.0, ge=0.0, le=1.0, description="Composite fit score.")


class RecommendResponse(BaseModel):
    """Response from the /recommend endpoint."""

    profile: ParsedProfile
    recommendations: List[Opportunity]
    total_candidates: int


class StatsResponse(BaseModel):
    """Basic dataset statistics."""

    total_companies: int
    total_opportunities: int
    available_cities: List[str]
    available_majors: List[str]
    available_work_modes: List[str]


class HealthResponse(BaseModel):
    """Simple health check response."""

    status: str
    environment: str
