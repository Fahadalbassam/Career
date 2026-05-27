"""
schemas.py – Pydantic models for request and response validation.
"""

from typing import Dict, List, Optional
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

    Represents major, university, locations, skills, qualifications, interests,
    work/program preferences, role intent, and interview preference.
    """

    major: Optional[str] = Field(
        default=None,
        description="Student major code, e.g. CS, AI, CYS, CIS, DS, DE, CE, FT.",
    )

    university: Optional[str] = Field(
        default=None,
        description="University code or name, e.g. IAU, KFUPM, KSU, KAU, PSU.",
    )

    city: Optional[str] = Field(
        default=None,
        description="Primary city, e.g. Riyadh, Jeddah, Dammam, Khobar, Dhahran.",
    )

    preferred_locations: List[str] = Field(
        default_factory=list,
        description="Acceptable cities when multiple locations are mentioned.",
    )

    skills: List[str] = Field(
        default_factory=list,
        description="Student skills, e.g. Python, SQL, Linux.",
    )

    qualifications: List[str] = Field(
        default_factory=list,
        description="Certifications, credentials, or GPA tokens, e.g. AWS, GPA 4.5.",
    )

    interest: Optional[str] = Field(
        default=None,
        description="Student interest area, e.g. Cybersecurity, Data Science, Software Development.",
    )

    program_type: Optional[str] = Field(
        default=None,
        description="Preferred opportunity type, e.g. COOP or Internship.",
    )

    work_mode: Optional[str] = Field(
        default=None,
        description="Preferred work mode, e.g. Remote, On-site, Hybrid.",
    )

    preferred_roles: List[str] = Field(
        default_factory=list,
        description="Role titles or clusters the student is targeting.",
    )

    interview_preference: Optional[str] = Field(
        default=None,
        description='Interview stance, e.g. "No interview preferred" or "Interview okay".',
    )


class ParsedProfile(StudentProfile):
    """Structured profile returned by the parser and /parse, /recommend APIs."""
    pass

class Opportunity(BaseModel):
    """A single COOP/internship opportunity."""
    
    id: int
    rank: int = 0
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
    score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Legacy composite fit score in [0, 1]. Equals match_score / 100.",
    )
    match_score: int = Field(
        0,
        ge=0,
        le=100,
        description="0–100 recommendation score derived from the rubric.",
    )

    role_cluster: str = Field(
        default="",
        description=(
            "Inferred role cluster, e.g. Software Engineering, Cybersecurity, "
            "Data Science, Cloud Engineering."
        ),
    )

    interview_required: str = Field(
        default="Not stated",
        description='One of: "Required", "Not required", "Not stated".',
    )

    missing_skills: List[str] = Field(
        default_factory=list,
        description="Opportunity skills the student does not appear to have.",
    )

    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Per-component rubric scores in [0, 1] used to derive match_score. "
            "Keys: major_fit_score, skill_match_score, role_interest_score, "
            "city_match_score, program_type_score, work_mode_score, "
            "verification_score, interview_score."
        ),
    )

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
