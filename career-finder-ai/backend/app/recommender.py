"""
recommender.py – Returns ranked COOP/internship opportunities for a student.

In this starter version the candidate pool is a hard-coded placeholder list.
Replace ``_get_placeholder_candidates`` with a database query once the dataset
is loaded and the ML model is trained.
"""

from typing import List

from app.parser import parse_message
from app.schemas import Opportunity, ParsedProfile, RecommendResponse
from app.scoring import compute_score


# ---------------------------------------------------------------------------
# Placeholder candidate pool
# ---------------------------------------------------------------------------

PLACEHOLDER_OPPORTUNITIES: List[Opportunity] = [
    Opportunity(
        id=1,
        company="Saudi Aramco",
        title="Data Science COOP",
        city="Dhahran",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["DS", "CS", "AI", "DE"],
        source_url="https://www.aramco.com/careers",
        score=0.0,
    ),
    Opportunity(
        id=2,
        company="STC",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS", "CS", "CE"],
        source_url="https://www.stc.com.sa/careers",
        score=0.0,
    ),
    Opportunity(
        id=3,
        company="Elm Company",
        title="Artificial Intelligence COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["AI", "CS", "DS"],
        source_url="https://www.elm.sa/careers",
        score=0.0,
    ),
    Opportunity(
        id=4,
        company="KPMG Saudi Arabia",
        title="FinTech Internship",
        city="Jeddah",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["FT", "CIS", "CS"],
        source_url="https://home.kpmg/sa/en/home/careers.html",
        score=0.0,
    ),
    Opportunity(
        id=5,
        company="Thiqah Business Services",
        title="Software Engineering COOP",
        city="Riyadh",
        work_mode="Remote",
        program_type="COOP",
        major_fit=["CS", "CE", "CIS"],
        source_url="https://www.thiqah.sa/careers",
        score=0.0,
    ),
    Opportunity(
        id=6,
        company="Madar",
        title="Data Engineering Internship",
        city="Dammam",
        work_mode="On-site",
        program_type="Internship",
        major_fit=["DE", "DS", "CS"],
        source_url="https://www.madar.com/careers",
        score=0.0,
    ),
    Opportunity(
        id=7,
        company="Siemens Saudi Arabia",
        title="Computer Engineering COOP",
        city="Jeddah",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CE", "CS"],
        source_url="https://www.siemens.com/sa/en/company/jobs.html",
        score=0.0,
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_candidates() -> List[Opportunity]:
    """
    Return the full candidate opportunity pool.

    Replace this function with a real database query when the dataset is ready.
    """
    return list(PLACEHOLDER_OPPORTUNITIES)


def recommend(profile: ParsedProfile, top_n: int = 5) -> List[Opportunity]:
    """
    Score and rank all candidate opportunities for the given student profile.

    Args:
        profile: Parsed student profile containing filters.
        top_n: Maximum number of recommendations to return.

    Returns:
        Sorted list of :class:`Opportunity` objects (highest score first).
    """
    candidates = get_candidates()

    scored: List[Opportunity] = []
    for opp in candidates:
        score = compute_score(profile, opp)
        # Create a new instance with the computed score
        scored.append(opp.model_copy(update={"score": score}))

    scored.sort(key=lambda o: o.score, reverse=True)
    return scored[:top_n]


def recommend_from_message(message: str, top_n: int = 5) -> RecommendResponse:
    """
    End-to-end helper: parse a raw message then return recommendations.

    Args:
        message: Free-text student input.
        top_n: Maximum number of recommendations to return.

    Returns:
        :class:`RecommendResponse` with profile and ranked opportunities.
    """
    profile = parse_message(message)
    recommendations = recommend(profile, top_n=top_n)
    total_candidates = len(get_candidates())

    return RecommendResponse(
        profile=profile,
        recommendations=recommendations,
        total_candidates=total_candidates,
    )
