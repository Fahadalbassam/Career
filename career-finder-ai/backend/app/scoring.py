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
    Return a score based on city/location match.

    Rules:
        No student city preference -> 0.5
        Exact preferred / primary / home city match -> 1.0
        Acceptable location match -> 0.85
        Same Eastern Province cluster -> 0.7
        Remote opportunity -> 0.5
        Saudi Arabia / Multiple / Remote city -> 0.5
        Not stated -> 0.3
        No match -> 0.0
    """
    preferred = {
        c.lower().strip()
        for c in profile.preferred_locations
        if c and c.strip()
    }
    acceptable = {
        c.lower().strip()
        for c in profile.acceptable_locations
        if c and c.strip()
    }
    student_city = (profile.city or "").lower().strip()
    home_city = (profile.home_city or profile.city or "").lower().strip()
    opportunity_city = opportunity.city.lower().strip()
    opportunity_work_mode = opportunity.work_mode.lower().strip()

    if not opportunity_city or opportunity_city == "not stated":
        return 0.3

    if preferred and opportunity_city in preferred:
        return 1.0

    if student_city and student_city == opportunity_city:
        return 1.0

    if home_city and home_city == opportunity_city:
        return 1.0

    if acceptable and opportunity_city in acceptable:
        return 0.85

    eastern_province = {"dammam", "khobar", "dhahran"}
    anchor = home_city or student_city

    if anchor in eastern_province and opportunity_city in eastern_province:
        return 0.7

    if "remote" in opportunity_work_mode:
        return 0.5

    flexible_locations = {"saudi arabia", "multiple", "remote"}

    if opportunity_city in flexible_locations:
        return 0.5

    if not student_city and not home_city and not preferred and not acceptable:
        return 0.5

    return 0.0

def _normalize_work_mode_for_scoring(value: str | None) -> str:
    """
    Normalize work mode values for scoring.

    Examples:
        "On-site" -> "onsite"
        "Onsite" -> "onsite"
        "In person" -> "onsite"
        "In-person" -> "onsite"
        "Remote" -> "remote"
        "Hybrid" -> "hybrid"
    """
    if not value:
        return ""

    text = value.lower().strip()

    if "remote" in text and "hybrid" in text:
        return "hybrid"

    if "hybrid" in text:
        return "hybrid"

    if "remote" in text:
        return "remote"

    if (
        "on-site" in text
        or "onsite" in text
        or "in person" in text
        or "in-person" in text
    ):
        return "onsite"

    return text


def work_mode_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return a score based on how well the work mode matches.

    Rules:
        No student preference -> 0.5
        Exact normalized match -> 1.0
        Student wants Remote and opportunity is Hybrid -> 0.7
        Student wants Hybrid and opportunity is Remote -> 0.7
        Opportunity work mode not stated -> 0.3
        No match -> 0.0
    """
    if not profile.work_mode:
        return 0.5

    student_mode = _normalize_work_mode_for_scoring(profile.work_mode)
    opportunity_mode = _normalize_work_mode_for_scoring(opportunity.work_mode)

    if not opportunity_mode or opportunity_mode == "not stated":
        return 0.3

    if student_mode == opportunity_mode:
        return 1.0

    # Remote and Hybrid are close, but not perfect
    if student_mode == "remote" and opportunity_mode == "hybrid":
        return 0.7

    if student_mode == "hybrid" and opportunity_mode == "remote":
        return 0.7

    return 0.0

def program_type_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    """
    Return a score based on how well the opportunity program type matches
    the student's requested program type.

    Rules:
        Exact match -> 1.0
        COOP/Internship matches COOP -> 1.0
        COOP/Internship matches Internship -> 1.0
        Training can partially match COOP/Internship -> 0.5
        No student preference -> 0.5
        No match -> 0.0
    """
    if not profile.program_type:
        return 0.5

    student_type = profile.program_type.lower().strip()
    opportunity_type = opportunity.program_type.lower().strip()

    if not opportunity_type:
        return 0.0

    # Exact match
    if student_type == opportunity_type:
        return 1.0

    # Normalize common mixed type
    mixed_types = {
        "coop/internship",
        "internship/coop",
        "coop internship",
        "internship coop",
    }

    if opportunity_type in mixed_types:
        if student_type in {"coop", "internship"}:
            return 1.0

    if student_type in mixed_types:
        if opportunity_type in {"coop", "internship"}:
            return 1.0

    # COOP-related matching
    if student_type == "coop" and "coop" in opportunity_type:
        return 1.0

    if student_type == "internship" and "intern" in opportunity_type:
        return 1.0

    # Training is somewhat related, but weaker
    if student_type in {"coop", "internship"} and "training" in opportunity_type:
        return 0.5

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
