"""
rubric.py – Shared rubric scoring helpers for CareerFinder.ai.

Provides component scorers and a combined ``target_score`` in [0, 100] used by
both the live recommender (``app.recommender``) and the regression dataset
builder (``app.build_regression_dataset``).

Pure logic only — this module has no I/O and depends only on ``app.schemas``.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple

from app.schemas import Opportunity, ParsedProfile


# ---------------------------------------------------------------------------
# Rubric constants
# ---------------------------------------------------------------------------

EASTERN_PROVINCE = {"dammam", "khobar", "dhahran"}
FLEXIBLE_CITIES = {"saudi arabia", "multiple", "remote"}

GENERIC_TECHNICAL_TERMS = {
    "python",
    "sql",
    "linux",
    "git",
    "api",
    "cloud",
    "data",
    "software",
    "engineering",
    "technology",
    "technical",
    "computer",
}

TARGET_WEIGHTS = {
    "major_fit_score": 0.35,
    "skill_match_score": 0.20,
    "role_interest_score": 0.15,
    "city_match_score": 0.10,
    "program_type_score": 0.10,
    "work_mode_score": 0.05,
    "verification_score": 0.03,
    "interview_score": 0.02,
}

RELATED_MAJORS: dict[str, set[str]] = {
    "CS": {"CE", "CIS", "AI", "DS", "DE"},
    "AI": {"CS", "DS", "DE", "CE"},
    "DS": {"AI", "CS", "DE", "FT", "CIS"},
    "DE": {"DS", "AI", "CS"},
    "CYS": {"CE", "CS"},
    "CE": {"CS", "CYS"},
    "CIS": {"CS", "FT", "DS"},
    "FT": {"CS", "DS", "CIS"},
}

ROLE_CLUSTER_PATTERNS: List[Tuple[str, List[str]]] = [
    ("Software Engineering", ["software engineer", "software engineering", "backend", "frontend", "full stack"]),
    ("Data Science", ["data science", "data scientist"]),
    ("Data Analytics", ["data analyst", "data analytics", "power bi", "dashboard"]),
    ("Machine Learning", ["machine learning", "ml engineer", "deep learning"]),
    ("AI Engineering", ["ai engineer", "artificial intelligence"]),
    ("Cybersecurity", ["cybersecurity", "cyber security", "information security"]),
    ("SOC Operations", ["soc analyst", "soc monitoring", "security operations"]),
    ("Network Engineering", ["network engineer", "network security", "networking"]),
    ("Cloud Engineering", ["cloud engineer", "cloud infrastructure", "aws", "azure"]),
    ("Data Engineering", ["data engineer", "data engineering", "etl", "data pipeline"]),
    ("DevOps", ["devops", "ci/cd", "kubernetes"]),
    ("Business Analysis", ["business analyst", "business analysis"]),
    ("Systems Analysis", ["systems analyst"]),
    ("FinTech", ["fintech", "financial technology", "banking technology"]),
    ("Embedded Systems", ["embedded", "firmware", "iot hardware"]),
]

ROLE_FAMILY_KEYWORDS: dict[str, List[str]] = {
    "software": ["software", "backend", "frontend", "full stack", "developer", "engineering"],
    "data": ["data science", "data analyst", "data engineering", "analytics", "etl", "pipeline"],
    "security": ["cybersecurity", "soc", "security", "network security", "incident response"],
    "cloud": ["cloud", "devops", "infrastructure", "aws", "azure"],
    "business": ["business analyst", "systems analyst", "product analyst"],
    "fintech": ["fintech", "finance", "banking"],
}

ROLE_EXACT_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("Software Engineer", ["software engineer", "software engineering"]),
    ("Backend Developer", ["backend developer", "backend development", "backend engineer"]),
    ("Frontend Developer", ["frontend developer", "front end developer"]),
    ("Full Stack Developer", ["full stack", "fullstack"]),
    ("Data Scientist", ["data scientist", "data science"]),
    ("Data Analyst", ["data analyst"]),
    ("Machine Learning Engineer", ["machine learning engineer", "machine learning"]),
    ("AI Engineer", ["ai engineer"]),
    ("Cybersecurity Analyst", ["cybersecurity analyst", "cyber security analyst"]),
    ("SOC Analyst", ["soc analyst"]),
    ("Network Engineer", ["network engineer"]),
    ("Cloud Engineer", ["cloud engineer"]),
    ("DevOps Engineer", ["devops engineer", "devops"]),
    ("Business Analyst", ["business analyst"]),
    ("Systems Analyst", ["systems analyst"]),
]

SCORE_BREAKDOWN_KEYS: Tuple[str, ...] = (
    "major_fit_score",
    "skill_match_score",
    "role_interest_score",
    "city_match_score",
    "program_type_score",
    "work_mode_score",
    "verification_score",
    "interview_score",
)

INTERVIEW_REQUIRED_VALUES: Tuple[str, ...] = ("Required", "Not required", "Not stated")

SKILL_NOISE_TOKENS = {"", "not stated", "nan", "n/a", "none"}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(value: Optional[str]) -> str:
    """Lowercase, strip, and collapse whitespace."""
    if not value:
        return ""
    text = str(value).lower().strip()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_list(values: Optional[Iterable[str]]) -> List[str]:
    """Normalize a list of strings, dropping empties while preserving order."""
    if not values:
        return []
    normalized: List[str] = []
    seen: set[str] = set()
    for value in values:
        text = normalize_text(value)
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def contains_any(text: str, phrases: Sequence[str]) -> bool:
    """Return True when any phrase appears in normalized text."""
    haystack = normalize_text(text)
    return any(normalize_text(phrase) in haystack for phrase in phrases)


def _normalize_work_mode(value: Optional[str]) -> str:
    text = normalize_text(value)
    if not text or text == "not stated":
        return "not_stated"
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text:
        return "remote"
    if "on-site" in text or "onsite" in text or "in person" in text or "in-person" in text:
        return "onsite"
    return text


def _normalize_program_type(value: Optional[str]) -> str:
    text = normalize_text(value)
    if not text or text == "not stated":
        return "not_stated"
    if ("coop" in text or "co-op" in text) and "intern" in text:
        return "coop_internship"
    if "coop" in text or "co-op" in text:
        return "coop"
    if "intern" in text:
        return "internship"
    if "tamheer" in text:
        return "tamheer"
    if "training" in text:
        return "training"
    return text


def _opportunity_base_text(opportunity: Opportunity) -> str:
    return normalize_text(
        " ".join(
            [
                opportunity.title,
                opportunity.requirements,
                " ".join(opportunity.skills_list),
            ]
        )
    )


def _opportunity_search_text(opportunity: Opportunity) -> str:
    return normalize_text(
        " ".join([_opportunity_base_text(opportunity), infer_role_cluster(opportunity)])
    )


def _profile_skill_tokens(profile: ParsedProfile) -> List[str]:
    tokens: List[str] = []
    for item in list(profile.skills) + list(profile.qualifications):
        norm = normalize_text(item)
        if norm:
            tokens.append(norm)
            tokens.extend(part for part in norm.split() if len(part) > 1)
    return normalize_list(tokens)


# ---------------------------------------------------------------------------
# Opportunity inference
# ---------------------------------------------------------------------------

def infer_role_cluster(opportunity: Opportunity) -> str:
    """Infer a role cluster label from opportunity text."""
    text = _opportunity_base_text(opportunity)
    for label, keywords in ROLE_CLUSTER_PATTERNS:
        if contains_any(text, keywords):
            return label
    return "General Computing"


def infer_interview_required(opportunity: Opportunity) -> str:
    """Infer interview requirement from opportunity text.

    Returns one of ``"Required"``, ``"Not required"``, or ``"Not stated"``.
    """
    text = _opportunity_search_text(opportunity)

    not_required_phrases = [
        "no interview",
        "without interview",
        "interview not required",
        "not required",
        "accepts right away",
        "direct acceptance",
        "immediate acceptance",
    ]
    required_phrases = [
        "interview required",
        "must attend interview",
        "panel interview",
        "requires interview",
    ]

    if contains_any(text, not_required_phrases):
        return "Not required"
    if contains_any(text, required_phrases):
        return "Required"
    return "Not stated"


def infer_verified_opportunity(opportunity: Opportunity) -> bool:
    """Treat non-empty source URLs in the cleaned dataset as verified listings."""
    return bool(normalize_text(opportunity.source_url))


# ---------------------------------------------------------------------------
# Component scorers (each returns 0.0–1.0)
# ---------------------------------------------------------------------------

def compute_major_fit_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    if not profile.major:
        return 0.3

    accepted = {code.upper() for code in opportunity.major_fit}
    student_major = profile.major.upper()

    if not accepted:
        return 0.3

    if student_major in accepted:
        return 1.0

    related = RELATED_MAJORS.get(student_major, set())
    if accepted & related:
        return 0.6

    return 0.0


def compute_skill_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    if not profile.skills and not profile.qualifications:
        return 0.4

    searchable = _opportunity_search_text(opportunity)
    tokens = _profile_skill_tokens(profile)
    if not tokens:
        return 0.4

    matched = sum(1 for token in tokens if token in searchable)
    return matched / len(tokens)


def _role_tokens(profile: ParsedProfile) -> List[str]:
    tokens: List[str] = []
    if profile.interest:
        tokens.append(normalize_text(profile.interest))
    tokens.extend(normalize_list(profile.preferred_roles))
    return tokens


def _role_family_for_token(token: str) -> Optional[str]:
    for family, keywords in ROLE_FAMILY_KEYWORDS.items():
        if contains_any(token, keywords):
            return family
    return None


def compute_role_interest_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    role_text = _opportunity_search_text(opportunity)
    role_cluster = normalize_text(infer_role_cluster(opportunity))
    profile_roles = _role_tokens(profile)

    if not profile_roles and not profile.interest:
        return 0.3

    for role in profile_roles:
        role_norm = normalize_text(role)
        if role_norm and (role_norm in role_text or role_norm in role_cluster):
            return 1.0

    for _, keywords in ROLE_EXACT_KEYWORDS:
        if contains_any(role_text, keywords):
            for role in profile_roles:
                if contains_any(role, keywords):
                    return 1.0

    profile_families = {
        family
        for role in profile_roles
        for family in [_role_family_for_token(role)]
        if family
    }
    opp_families = {
        family
        for family, keywords in ROLE_FAMILY_KEYWORDS.items()
        if contains_any(role_text, keywords)
    }
    if profile_families & opp_families:
        return 0.6

    if any(term in role_text for term in GENERIC_TECHNICAL_TERMS):
        return 0.3

    return 0.0


def compute_city_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    opp_city = normalize_text(opportunity.city)
    if not opp_city or opp_city == "not stated":
        return 0.3

    preferred = {normalize_text(c) for c in profile.preferred_locations}
    preferred.discard("")
    student_city = normalize_text(profile.city)

    if opp_city in preferred:
        return 1.0

    if student_city and student_city == opp_city:
        return 1.0

    if student_city in EASTERN_PROVINCE and opp_city in EASTERN_PROVINCE:
        return 0.7

    if opp_city in FLEXIBLE_CITIES:
        return 0.5

    if _normalize_work_mode(opportunity.work_mode) == "remote":
        return 0.5

    if not student_city and not preferred:
        return 0.5

    return 0.0


def compute_program_type_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    student_type = _normalize_program_type(profile.program_type)
    opp_type = _normalize_program_type(opportunity.program_type)

    if not student_type:
        return 0.5

    if opp_type == "not_stated":
        return 0.3

    if student_type == opp_type:
        return 1.0

    if opp_type == "coop_internship" and student_type in {"coop", "internship"}:
        return 0.9
    if student_type == "coop_internship" and opp_type in {"coop", "internship"}:
        return 0.9

    if student_type in {"coop", "internship", "tamheer"} and opp_type == "training":
        return 0.5
    if student_type == "training" and opp_type in {"coop", "internship", "tamheer"}:
        return 0.5

    return 0.0


def compute_work_mode_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    student_mode = _normalize_work_mode(profile.work_mode)
    opp_mode = _normalize_work_mode(opportunity.work_mode)

    if not student_mode:
        return 0.5

    if opp_mode == "not_stated":
        return 0.3

    if student_mode == opp_mode:
        return 1.0

    if {student_mode, opp_mode} == {"remote", "hybrid"}:
        return 0.7
    if {student_mode, opp_mode} == {"onsite", "hybrid"}:
        return 0.7

    return 0.0


def compute_verification_score(opportunity: Opportunity) -> float:
    if infer_verified_opportunity(opportunity):
        return 1.0
    if normalize_text(opportunity.source_url):
        return 0.7
    return 0.2


def compute_interview_score(
    profile: ParsedProfile,
    opportunity: Opportunity,
) -> float:
    preference = profile.interview_preference
    requirement = infer_interview_required(opportunity)

    if preference is None:
        return 0.5

    if preference == "No interview preferred":
        if requirement == "Not required":
            return 1.0
        if requirement == "Required":
            return 0.2
        return 0.5

    if preference == "Interview okay":
        if requirement == "Required":
            return 1.0
        if requirement == "Not required":
            return 0.8
        return 0.5

    return 0.5


# ---------------------------------------------------------------------------
# Combined target score and helpers
# ---------------------------------------------------------------------------

def compute_target_score(
    major_fit_score: float,
    skill_match_score: float,
    role_interest_score: float,
    city_match_score: float,
    program_type_score: float,
    work_mode_score: float,
    verification_score: float,
    interview_score: float,
) -> float:
    """Weighted rubric score on a 0–100 scale."""
    composite = (
        TARGET_WEIGHTS["major_fit_score"] * major_fit_score
        + TARGET_WEIGHTS["skill_match_score"] * skill_match_score
        + TARGET_WEIGHTS["role_interest_score"] * role_interest_score
        + TARGET_WEIGHTS["city_match_score"] * city_match_score
        + TARGET_WEIGHTS["program_type_score"] * program_type_score
        + TARGET_WEIGHTS["work_mode_score"] * work_mode_score
        + TARGET_WEIGHTS["verification_score"] * verification_score
        + TARGET_WEIGHTS["interview_score"] * interview_score
    )
    return round(min(max(composite * 100, 0.0), 100.0), 2)


def score_profile_opportunity_pair(
    profile: ParsedProfile,
    opportunity: Opportunity,
) -> dict[str, float]:
    """Return all rubric component scores plus ``target_score`` (0–100)."""
    major_fit = compute_major_fit_score(profile, opportunity)
    skill_match = compute_skill_match_score(profile, opportunity)
    role_interest = compute_role_interest_score(profile, opportunity)
    city_match = compute_city_match_score(profile, opportunity)
    program_type = compute_program_type_score(profile, opportunity)
    work_mode = compute_work_mode_score(profile, opportunity)
    verification = compute_verification_score(opportunity)
    interview = compute_interview_score(profile, opportunity)

    target = compute_target_score(
        major_fit,
        skill_match,
        role_interest,
        city_match,
        program_type,
        work_mode,
        verification,
        interview,
    )

    return {
        "major_fit_score": major_fit,
        "skill_match_score": skill_match,
        "role_interest_score": role_interest,
        "city_match_score": city_match,
        "program_type_score": program_type,
        "work_mode_score": work_mode,
        "verification_score": verification,
        "interview_score": interview,
        "target_score": target,
    }


def compute_missing_skills(
    profile: ParsedProfile,
    opportunity: Opportunity,
) -> List[str]:
    """Return opportunity skills the student does not appear to have.

    Rules:
        - Case-insensitive comparison.
        - Whitespace is stripped.
        - "Not stated", "nan", "n/a", "none", and empty tokens are filtered out.
        - Output preserves the original spelling from the opportunity.
        - Duplicates are removed while preserving first-seen order.
    """
    student = {
        skill.strip().lower()
        for skill in (profile.skills or [])
        if skill and skill.strip().lower() not in SKILL_NOISE_TOKENS
    }

    seen: set[str] = set()
    missing: List[str] = []
    for skill in opportunity.skills_list or []:
        if not skill:
            continue
        cleaned = str(skill).strip()
        normalized = cleaned.lower()
        if not normalized or normalized in SKILL_NOISE_TOKENS:
            continue
        if normalized in student:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        missing.append(cleaned)
    return missing
