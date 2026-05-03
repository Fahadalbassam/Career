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

class StudentProfile(BaseModel):
    """
    Structured student profile used by the recommendation engine.

    This represents the student's major, location, interests, preferred work mode,
    preferred program type, and skills.
    """

    major: Optional[str] = Field(
        default=None,
        description="Student major code, e.g. CS, AI, CYS, CIS, DS, DE, CE, FT.",
    )

    city: Optional[str] = Field(
        default=None,
        description="Preferred city, e.g. Riyadh, Jeddah, Dammam, Khobar, Dhahran.",
    )

    interest: Optional[str] = Field(
        default=None,
        description="Student interest area, e.g. Cybersecurity, Data Science, Software Development.",
    )

    work_mode: Optional[str] = Field(
        default=None,
        description="Preferred work mode, e.g. Remote, On-site, Hybrid.",
    )

    program_type: Optional[str] = Field(
        default=None,
        description="Preferred opportunity type, e.g. COOP or Internship.",
    )

    skills: List[str] = Field(
        default_factory=list,
        description="Student skills, e.g. Python, SQL, Linux, Power BI.",
    )


class ParsedProfile(StudentProfile):
    """
    Backward-compatible name used by the parser and API.

    For now, ParsedProfile and StudentProfile have the same fields.
    Later, the parser will return ParsedProfile after reading a student message.
    """
    pass

class Opportunity(BaseModel):
    """A single COOP/internship opportunity."""

    id: int
    company: str
    title: str
    city: str
    work_mode: str
    program_type: str
    major_fit: List[str] = Field(default_factory=list)

    # Extra details used for matching and explanations
    requirements: str = ""
    skills_list: List[str] = Field(default_factory=list)

    source_url: str
    score: float = Field(0.0, ge=0.0, le=1.0, description="Composite fit score.")

    # Explanation fields returned to the frontend
    why_recommended: List[str] = Field(default_factory=list)
    skills_matched: List[str] = Field(default_factory=list)

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
