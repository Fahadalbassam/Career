"""
recommender.py – Returns ranked COOP/internship opportunities for a student.

In this starter version the candidate pool is a hard-coded placeholder list.
Replace ``_get_placeholder_candidates`` with a database query once the dataset
is loaded and the ML model is trained.
"""


from pathlib import Path
from typing import List

import pandas as pd

from app.parser import parse_message
from app.rubric import (
    SCORE_BREAKDOWN_KEYS,
    compute_missing_preferred_skills,
    compute_missing_required_skills,
    compute_missing_skills,
    infer_interview_required,
    infer_role_cluster,
    score_profile_opportunity_pair,
)
from app.schemas import Opportunity, ParsedProfile, RecommendResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
OPPORTUNITIES_XLSX_PATH = REPO_ROOT / "data" / "processed" / "Opportunities_Clean.xlsx"


# ---------------------------------------------------------------------------
# Placeholder candidate pool
# ---------------------------------------------------------------------------

PLACEHOLDER_OPPORTUNITIES = [
    Opportunity(
        id=1,
        company="Aramco Digital",
        title="AI and Data Science COOP",
        city="Dhahran",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["AI", "DS", "CS"],
        requirements="Python, machine learning, data analysis, SQL, statistics",
        skills_list=["python", "machine learning", "data analysis", "sql", "statistics"],
        source_url="https://aramcodigital.com/careers",
    ),
    Opportunity(
        id=2,
        company="STC",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS", "CS", "CE"],
        requirements="Network security, SOC monitoring, vulnerability assessment, Linux",
        skills_list=["network security", "soc", "vulnerability assessment", "linux"],
        source_url="https://www.stc.com.sa/careers",
    ),
    Opportunity(
        id=3,
        company="Elm",
        title="Software Engineering COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CS", "CIS", "AI"],
        requirements="Backend development, APIs, databases, Java, Python",
        skills_list=["backend", "api", "databases", "java", "python"],
        source_url="https://www.elm.sa/careers",
    ),
    Opportunity(
        id=4,
        company="Tamara",
        title="FinTech Product Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["FT", "CIS", "CS", "DS"],
        requirements="Product analytics, fintech, SQL, dashboards, business analysis",
        skills_list=["fintech", "sql", "dashboards", "analytics", "business analysis"],
        source_url="https://tamara.co/careers",
    ),
    Opportunity(
        id=5,
        company="Mozn",
        title="Machine Learning Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["AI", "DS", "CS"],
        requirements="Python, machine learning, NLP, model evaluation, data preprocessing",
        skills_list=["python", "machine learning", "nlp", "model evaluation", "data preprocessing"],
        source_url="https://mozn.sa/careers",
    ),
    Opportunity(
        id=6,
        company="SDAIA",
        title="Data Engineering Training",
        city="Riyadh",
        work_mode="On-site",
        program_type="Training",
        major_fit=["DE", "DS", "AI", "CS"],
        requirements="Data pipelines, ETL, SQL, Python, big data concepts",
        skills_list=["data pipelines", "etl", "sql", "python", "big data"],
        source_url="https://sdaia.gov.sa",
    ),
    Opportunity(
        id=7,
        company="Cyberani",
        title="Cybersecurity COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CYS", "CS", "CE"],
        requirements="Cybersecurity fundamentals, network security, Linux, incident response",
        skills_list=["cybersecurity", "network security", "linux", "incident response"],
        source_url="https://cyberani.sa",
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _split_list_value(value) -> List[str]:
    """
    Convert a separated string into a clean list.

    Supports commas and semicolons.

    Examples:
        "AI, DS, CS" -> ["AI", "DS", "CS"]
        "python; sql; linux" -> ["python", "sql", "linux"]
    """
    if value is None:
        return []

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return []

    # Normalize semicolons to commas
    value = value.replace(";", ",")

    return [
        item.strip()
        for item in value.split(",")
        if item.strip() and item.strip().lower() not in {"not stated", "nan", "none", "n/a"}
    ]


def _get_first_available(row: dict, possible_keys: List[str], default: str = "") -> str:
    """
    Read the first existing value from an Excel row using multiple possible column names.

    This helps us support different dataset column names like:
        company / company_name / Company_Name
        title / program_name / Program_Name
    """
    for key in possible_keys:
        value = row.get(key)

        if value is not None and str(value).strip() and str(value).lower() != "nan":
            return str(value).strip()

    return default

def load_opportunities_from_xlsx(
    xlsx_path: Path = OPPORTUNITIES_XLSX_PATH,
) -> List[Opportunity]:
    """
    Load real opportunities from data/processed/opportunities_clean.xlsx.

    If the Excel file does not exist, return an empty list.
    The fallback to placeholders happens inside get_candidates().
    """
    if not xlsx_path.exists():
        return []

    # Try to read the Opportunities sheet first.
    # If it does not exist, read the first sheet.
    try:
        df = pd.read_excel(xlsx_path, sheet_name="opportunities_clean")
    except ValueError:
        df = pd.read_excel(xlsx_path)

    opportunities: List[Opportunity] = []

    for index, row_data in df.iterrows():
        row = row_data.to_dict()

        opportunity_id_raw = _get_first_available(
            row,
            ["id", "opportunity_id", "Opportunity_ID"],
            default=str(index + 1),
        )

        try:
            opportunity_id = int(float(opportunity_id_raw))
        except ValueError:
            opportunity_id = index + 1

        company = _get_first_available(
            row,
            ["company", "company_name", "Company", "Company_Name"],
            default="Unknown Company",
        )

        title = _get_first_available(
            row,
            ["title", "program_name", "Program_Name", "opportunity_title", "Opportunity_Title"],
            default="Untitled Opportunity",
        )

        city = _get_first_available(
            row,
            ["city", "City", "location", "Location"],
            default="Not stated",
        )

        work_mode = _get_first_available(
            row,
            ["work_mode", "Work_Mode"],
            default="Not stated",
        )

        program_type = _get_first_available(
            row,
            ["program_type", "Program_Type", "type", "Type"],
            default="Not stated",
        )

        major_fit_raw = _get_first_available(
            row,
            ["major_fit", "degree_tags", "Degree_Tags"],
            default="",
        )

        requirements = _get_first_available(
            row,
            ["requirements", "Requirements", "eligibility_summary", "Eligibility_Summary"],
            default="",
        )

        skills_raw = _get_first_available(
            row,
            ["skills_list", "Skills_List", "technical_skills", "Technical_Skills"],
            default="",
        )

        source_url = _get_first_available(
            row,
            ["source_url", "Source_URL", "application_url", "Application_URL"],
            default="",
        )

        opportunities.append(
            Opportunity(
                id=opportunity_id,
                company=company,
                title=title,
                city=city,
                work_mode=work_mode,
                program_type=program_type,
                major_fit=_split_list_value(major_fit_raw),
                requirements=requirements,
                skills_list=_split_list_value(skills_raw),
                source_url=source_url,
            )
        )

    return opportunities

def get_candidates() -> List[Opportunity]:
    """
    Return the full candidate opportunity pool.

    First, try to load real opportunities from the cleaned Excel file.
    If the Excel file does not exist or is empty, use placeholder opportunities.
    """
    xlsx_opportunities = load_opportunities_from_xlsx()

    if xlsx_opportunities:
        return xlsx_opportunities

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

    Each returned opportunity is enriched with rubric outputs:
        - ``match_score``: 0–100 recommendation score.
        - ``score``: legacy 0–1 score = ``match_score / 100`` (kept for backward
          compatibility).
        - ``score_breakdown``: per-component rubric scores in [0, 1].
        - ``role_cluster``: inferred role/category for the opportunity.
        - ``interview_required``: inferred from opportunity text.
        - ``missing_skills``: opportunity skills the student does not list.
        - ``why_recommended`` / ``skills_matched``: human-readable reasons.

    Args:
        profile: Parsed student profile containing filters.
        top_n: Maximum number of recommendations to return.

    Returns:
        Sorted list of :class:`Opportunity` objects (highest score first).
    """
    candidates = get_candidates()

    # Step 1: filter weak candidates first
    candidates = filter_candidates(profile, candidates)

    # Step 2: score remaining candidates with the shared rubric
    scored: List[Opportunity] = []
    for opp in candidates:
        rubric = score_profile_opportunity_pair(profile, opp)
        raw_target = float(rubric.pop("target_score"))

        match_score = int(round(max(0.0, min(100.0, raw_target))))
        legacy_score = round(match_score / 100.0, 4)

        score_breakdown = {
            key: round(float(rubric[key]), 4) for key in SCORE_BREAKDOWN_KEYS
        }

        reasons, skills_matched = build_recommendation_reasons(profile, opp)

        scored.append(
            opp.model_copy(
                update={
                    "score": legacy_score,
                    "match_score": match_score,
                    "score_breakdown": score_breakdown,
                    "role_cluster": infer_role_cluster(opp),
                    "interview_required": infer_interview_required(opp),
                    "missing_skills": compute_missing_skills(profile, opp),
                    "missing_required_skills": compute_missing_required_skills(profile, opp),
                    "missing_preferred_skills": compute_missing_preferred_skills(profile, opp),
                    "why_recommended": reasons,
                    "skills_matched": skills_matched,
                }
            )
        )

    # Step 3: sort by match_score (highest first); legacy score is monotone with it
    scored.sort(key=lambda o: o.match_score, reverse=True)

    # Step 4: return Top N with rank numbers
    top_results = scored[:top_n]

    ranked_results: List[Opportunity] = []
    for rank, opp in enumerate(top_results, start=1):
        ranked_results.append(
            opp.model_copy(
                update={
                    "rank": rank,
                }
            )
        )

    return ranked_results


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
