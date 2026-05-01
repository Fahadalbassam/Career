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

def filter_candidates(
    profile: ParsedProfile,
    candidates: List[Opportunity],
) -> List[Opportunity]:
    """
    Filter candidate opportunities before scoring.

    This uses safe filtering:
    - If a filter keeps some results, we apply it.
    - If a filter would remove everything, we skip it.

    This prevents the recommender from returning zero results too easily.
    """
    filtered = list(candidates)

    # 1. Keep opportunities with a source URL.
    # For now, source_url is our simple verification signal.
    with_source = [opp for opp in filtered if opp.source_url]
    if with_source:
        filtered = with_source

    # 2. Prefer opportunities that match the student's major.
    if profile.major:
        major_matches = [
            opp for opp in filtered
            if not opp.major_fit or profile.major in opp.major_fit
        ]
        if major_matches:
            filtered = major_matches

    # 3. Prefer opportunities that match the requested program type.
    if profile.program_type:
        program_matches = [
            opp for opp in filtered
            if opp.program_type.lower() == profile.program_type.lower()
        ]
        if program_matches:
            filtered = program_matches

    return filtered

def build_recommendation_reasons(
    profile: ParsedProfile,
    opportunity: Opportunity,
) -> tuple[List[str], List[str]]:
    """
    Build human-readable reasons explaining why an opportunity was recommended.

    Args:
        profile: Parsed student profile.
        opportunity: Candidate opportunity.

    Returns:
        A tuple:
        - List of explanation reasons.
        - List of matched student skills.
    """
    reasons: List[str] = []

    # 1. Major match
    if profile.major and profile.major in opportunity.major_fit:
        reasons.append(f"Matches your major: {profile.major}")

    # 2. City match
    if profile.city and profile.city.lower() == opportunity.city.lower():
        reasons.append(f"Matches your preferred city: {profile.city}")

    # 3. Work mode match
    if profile.work_mode and profile.work_mode.lower() == opportunity.work_mode.lower():
        reasons.append(f"Matches your preferred work mode: {profile.work_mode}")

    # 4. Program type match
    if profile.program_type and profile.program_type.lower() == opportunity.program_type.lower():
        reasons.append(f"Matches your preferred program type: {profile.program_type}")

    # 5. Interest match
    if profile.interest and profile.interest.lower() in opportunity.title.lower():
        reasons.append(f"Matches your interest in {profile.interest}")

    # 6. Source URL / verification
    if opportunity.source_url:
        reasons.append("Has a verified source URL")

    # 7. Skill matches
    searchable_text = " ".join(
        [
            opportunity.title,
            opportunity.requirements,
            " ".join(opportunity.skills_list),
        ]
    ).lower()

    skills_matched = [
        skill for skill in profile.skills
        if skill.lower() in searchable_text
    ]

    if skills_matched:
        reasons.append(
            "Matches your skills: " + ", ".join(skills_matched)
        )

    # Fallback reason if no specific reason was found
    if not reasons:
        reasons.append("Recommended based on overall profile similarity")

    return reasons, skills_matched


def recommend(profile: ParsedProfile, top_n: int = 5) -> List[Opportunity]:
    """
    Filter, score, and rank candidate opportunities for the given student profile.

    Args:
        profile: Parsed student profile containing filters.
        top_n: Maximum number of recommendations to return.

    Returns:
        Sorted list of :class:`Opportunity` objects (highest score first).
    """
    candidates = get_candidates()

    # Step 1: filter weak candidates first
    candidates = filter_candidates(profile, candidates)

    # Step 2: score remaining candidates
    scored: List[Opportunity] = []
    for opp in candidates:
        score = compute_score(profile, opp)
        reasons, skills_matched = build_recommendation_reasons(profile, opp)

    # Create a new instance with the computed score and explanation fields.
        scored.append(
            opp.model_copy(
                update={
                    "score": score,
                    "why_recommended": reasons,
                    "skills_matched": skills_matched,
                }
            )
        )
    

    # Step 3: sort highest score first
    scored.sort(key=lambda o: o.score, reverse=True)

    # Step 4: return Top N
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
