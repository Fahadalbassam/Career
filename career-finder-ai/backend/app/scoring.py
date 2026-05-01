"""
scoring.py – Weighted scoring functions for ranking opportunities.

Each scorer returns a float in [0.0, 1.0].
The final composite score is a weighted average.
"""

from typing import Optional

from app.schemas import Opportunity, ParsedProfile


# ---------------------------------------------------------------------------
# Individual score components
# ---------------------------------------------------------------------------

def major_fit_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return 1.0 if the student's major is in the opportunity's major_fit list,
    0.5 if the list is empty (any major accepted), otherwise 0.0.

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity.

    Returns:
        Float score in [0.0, 1.0].
    """
    if not opportunity.major_fit:
        return 0.5  # opportunity open to all majors
    if profile.major and profile.major in opportunity.major_fit:
        return 1.0
    return 0.0


def city_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return 1.0 when the student's preferred city matches the opportunity city,
    0.5 for remote opportunities regardless of city preference, otherwise 0.0.

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity.

    Returns:
        Float score in [0.0, 1.0].
    """
    if opportunity.work_mode.lower() == "remote":
        return 0.5
    if profile.city and profile.city.lower() == opportunity.city.lower():
        return 1.0
    if not profile.city:
        return 0.5  # no preference expressed
    return 0.0


def work_mode_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return 1.0 when work modes match exactly, 0.5 when either side is unknown.

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity.

    Returns:
        Float score in [0.0, 1.0].
    """
    if not profile.work_mode:
        return 0.5
    if profile.work_mode.lower() == opportunity.work_mode.lower():
        return 1.0
    return 0.0

def program_type_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return a score based on how well the opportunity program type matches
    the student's requested program type.

    Examples:
        Student wants COOP + opportunity is COOP -> 1.0
        Student wants COOP + opportunity is Internship -> 0.0
        Student did not specify program type -> 0.5

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity.

    Returns:
        Float score in [0.0, 1.0].
    """
    if not profile.program_type:
        return 0.5

    if profile.program_type.lower() == opportunity.program_type.lower():
        return 1.0

    return 0.0


def interest_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return 1.0 when the student's interest keyword appears in the opportunity title,
    0.5 when no interest is detected, otherwise 0.0.

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity.

    Returns:
        Float score in [0.0, 1.0].
    """
    if not profile.interest:
        return 0.5
    if profile.interest.lower() in opportunity.title.lower():
        return 1.0
    return 0.0

def skills_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return a score based on how many student skills appear in the opportunity.

    Examples:
        Student skills: ["python", "sql"]
        Opportunity text: "Python and SQL required"
        Score: 1.0

        Student skills: ["python", "sql"]
        Opportunity text: "Python required"
        Score: 0.5

        Student has no skills listed
        Score: 0.5
    """
    if not profile.skills:
        return 0.5

    searchable_text = " ".join(
        [
            opportunity.title,
            getattr(opportunity, "requirements", ""),
            " ".join(getattr(opportunity, "skills_list", [])),
        ]
    ).lower()

    matched_count = 0

    for skill in profile.skills:
        if skill.lower() in searchable_text:
            matched_count += 1

    return matched_count / len(profile.skills)


def verified_source_bonus(opportunity: Opportunity) -> float:
    """
    Return a small bonus (0.1) when the opportunity has a non-empty source URL.

    Args:
        opportunity: Candidate opportunity.

    Returns:
        Float score in {0.0, 0.1}.
    """
    return 0.1 if opportunity.source_url else 0.0


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

WEIGHTS = {
    "major_fit": 0.25,
    "city_match": 0.18,
    "work_mode": 0.15,
    "program_type": 0.15,
    "interest": 0.12,
    "skills": 0.10,
    "verified": 0.05,
}


def compute_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Compute a weighted composite fit score for an opportunity.

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity to score.

    Returns:
        Composite float score in [0.0, 1.0].
    """
    raw = (
        WEIGHTS["major_fit"] * major_fit_score(profile, opportunity)
        + WEIGHTS["city_match"] * city_match_score(profile, opportunity)
        + WEIGHTS["work_mode"] * work_mode_match_score(profile, opportunity)
        + WEIGHTS["program_type"] * program_type_match_score(profile, opportunity)
        + WEIGHTS["interest"] * interest_match_score(profile, opportunity)
        + WEIGHTS["skills"] * skills_match_score(profile, opportunity)
        + WEIGHTS["verified"] * verified_source_bonus(opportunity)
    )
    # Clip to [0.0, 1.0] to handle floating-point edge cases
    return round(min(max(raw, 0.0), 1.0), 4)
