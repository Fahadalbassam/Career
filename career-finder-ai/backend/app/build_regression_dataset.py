"""
build_regression_dataset.py – Supervised regression training pairs.

Pairs deterministic synthetic student profiles with loaded opportunities and
assigns a rubric-based target_score in [0, 100].

Run from the backend directory:
    python -m app.build_regression_dataset

Output:
    data/processed/student_opportunity_regression_dataset.csv
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from app.recommender import (
    OPPORTUNITIES_XLSX_PATH,
    get_candidates,
    load_opportunities_from_xlsx,
)
from app.schemas import Opportunity, ParsedProfile

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "student_opportunity_regression_dataset.csv"

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

CSV_COLUMNS: List[str] = [
    "profile_id",
    "chat_message",
    "major",
    "university",
    "city",
    "preferred_locations",
    "skills",
    "qualifications",
    "interest",
    "program_type",
    "work_mode",
    "preferred_roles",
    "interview_preference",
    "opportunity_id",
    "company_name",
    "program_name",
    "opportunity_city",
    "opportunity_program_type",
    "opportunity_work_mode",
    "opportunity_skills",
    "opportunity_requirements",
    "opportunity_role_cluster",
    "interview_required",
    "source_url",
    "verified_opportunity",
    "major_fit_score",
    "skill_match_score",
    "role_interest_score",
    "city_match_score",
    "program_type_score",
    "work_mode_score",
    "verification_score",
    "interview_score",
    "target_score",
]


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


def _join_list(values: Sequence[str]) -> str:
    return "; ".join(values)


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
    """Opportunity text used for matching (title, requirements, skills)."""
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
    """
    Infer interview requirement from opportunity text.

    Returns: ``Required``, ``Not required``, or ``Not stated``.
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
# Rubric component scorers (each returns 0.0–1.0)
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
    """Return all component scores and target_score for one pair."""
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


# ---------------------------------------------------------------------------
# Synthetic profiles (deterministic, >= 40)
# ---------------------------------------------------------------------------

def _profile(
    profile_id: str,
    chat_message: str,
    *,
    major: Optional[str] = None,
    university: Optional[str] = None,
    city: Optional[str] = None,
    preferred_locations: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    qualifications: Optional[List[str]] = None,
    interest: Optional[str] = None,
    program_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    preferred_roles: Optional[List[str]] = None,
    interview_preference: Optional[str] = None,
) -> Tuple[str, str, ParsedProfile]:
    return (
        profile_id,
        chat_message,
        ParsedProfile(
            major=major,
            university=university,
            city=city,
            preferred_locations=preferred_locations or [],
            skills=skills or [],
            qualifications=qualifications or [],
            interest=interest,
            program_type=program_type,
            work_mode=work_mode,
            preferred_roles=preferred_roles or [],
            interview_preference=interview_preference,
        ),
    )


def build_synthetic_profiles() -> List[Tuple[str, str, ParsedProfile]]:
    """Return at least 40 deterministic synthetic student profiles."""
    profiles = [
        _profile(
            "cs-backend-riyadh-coop",
            "CS student at KSU in Riyadh seeking on-site COOP in backend development with Python and SQL.",
            major="CS",
            university="KSU",
            city="Riyadh",
            skills=["python", "sql", "git"],
            interest="Software Development",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Backend Developer"],
        ),
        _profile(
            "cs-frontend-jeddah-intern",
            "Computer science student in Jeddah looking for a hybrid frontend developer internship with React and JavaScript.",
            major="CS",
            city="Jeddah",
            skills=["javascript", "react", "typescript"],
            interest="Software Development",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Frontend Developer"],
        ),
        _profile(
            "cs-fullstack-remote",
            "I am a CS student who wants a remote full stack developer COOP using Python, Docker, and REST APIs.",
            major="CS",
            city="Riyadh",
            skills=["python", "docker", "javascript"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["Full Stack Developer"],
        ),
        _profile(
            "cs-software-eng-dammam",
            "Software engineering student in Dammam looking for software engineering COOP on-site.",
            major="CS",
            city="Dammam",
            skills=["java", "python", "git"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "cs-iau-backend",
            "CS student at IAU with Python and SQL seeking backend developer internship in Riyadh or Dammam.",
            major="CS",
            university="IAU",
            city="Riyadh",
            preferred_locations=["Riyadh", "Dammam"],
            skills=["python", "sql"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Backend Developer"],
        ),
        _profile(
            "cys-soc-riyadh",
            "Cybersecurity student at KFUPM in Dhahran targeting SOC analyst COOP with Linux and network security.",
            major="CYS",
            university="KFUPM",
            city="Dhahran",
            skills=["linux", "network security"],
            interest="Cybersecurity",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["SOC Analyst"],
        ),
        _profile(
            "cys-analyst-jeddah",
            "Cyber security student in Jeddah seeking cybersecurity analyst internship with Security+ and CCNA.",
            major="CYS",
            city="Jeddah",
            skills=["linux"],
            qualifications=["Security+", "CCNA"],
            interest="Cybersecurity",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Cybersecurity Analyst"],
        ),
        _profile(
            "cys-network-dammam",
            "CYS student in Dammam or Khobar looking for network security COOP without interview.",
            major="CYS",
            city="Dammam",
            preferred_locations=["Dammam", "Khobar"],
            skills=["network security", "linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Network Engineer"],
            interview_preference="No interview preferred",
        ),
        _profile(
            "cys-remote-intern",
            "Cybersecurity student seeking remote internship in incident response and SOC monitoring.",
            major="CYS",
            skills=["linux", "python"],
            interest="Cybersecurity",
            program_type="Internship",
            work_mode="Remote",
            preferred_roles=["SOC Analyst"],
        ),
        _profile(
            "cys-ceh-riyadh",
            "Information security student in Riyadh with CEH and CompTIA pursuing cybersecurity COOP.",
            major="CYS",
            city="Riyadh",
            qualifications=["CEH", "CompTIA"],
            skills=["linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Cybersecurity Analyst"],
        ),
        _profile(
            "ai-ml-riyadh",
            "AI student at KSU in Riyadh seeking machine learning engineer internship with Python and TensorFlow.",
            major="AI",
            university="KSU",
            city="Riyadh",
            skills=["python", "tensorflow", "pytorch"],
            interest="Artificial Intelligence",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Machine Learning Engineer"],
        ),
        _profile(
            "ai-engineer-remote",
            "Artificial intelligence student looking for remote AI engineer COOP with NLP experience.",
            major="AI",
            skills=["python", "machine learning"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["AI Engineer"],
        ),
        _profile(
            "ai-ds-cross",
            "ML student in Dhahran open to data science and AI engineering roles with scikit-learn.",
            major="AI",
            city="Dhahran",
            skills=["python", "scikit-learn", "sql"],
            interest="Artificial Intelligence",
            program_type="COOP/Internship",
            work_mode="On-site",
            preferred_roles=["Machine Learning Engineer", "Data Scientist"],
        ),
        _profile(
            "ds-analyst-riyadh",
            "Data science student in Riyadh seeking data analyst internship with SQL, Python, and Power BI.",
            major="DS",
            city="Riyadh",
            skills=["python", "sql", "pandas"],
            qualifications=["Power BI"],
            interest="Data Science",
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "ds-scientist-jeddah",
            "Data science student at KAU in Jeddah looking for data scientist COOP with statistics and Python.",
            major="DS",
            university="KAU",
            city="Jeddah",
            skills=["python", "sql", "numpy"],
            interest="Data Science",
            program_type="COOP",
            work_mode="Hybrid",
            preferred_roles=["Data Scientist"],
        ),
        _profile(
            "ds-remote-coop",
            "DS student seeking remote COOP in machine learning and data analysis.",
            major="DS",
            skills=["python", "pandas", "scikit-learn"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["Data Scientist"],
        ),
        _profile(
            "ds-gpa-ielts",
            "Data science student with GPA 4.5 and IELTS looking for internship in Riyadh.",
            major="DS",
            city="Riyadh",
            qualifications=["GPA 4.5", "IELTS"],
            skills=["sql", "python"],
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "de-pipelines-riyadh",
            "Data engineering student in Riyadh seeking COOP in ETL, data pipelines, and SQL.",
            major="DE",
            city="Riyadh",
            skills=["python", "sql", "spark"],
            interest="Data Engineering",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Data Engineering"],
        ),
        _profile(
            "de-cloud-dammam",
            "Data engineer student in Dammam targeting cloud and big data training with AWS.",
            major="DE",
            city="Dammam",
            skills=["python", "sql"],
            qualifications=["AWS"],
            program_type="Training",
            work_mode="Hybrid",
            preferred_roles=["Cloud Engineer", "Data Engineering"],
        ),
        _profile(
            "de-etl-remote",
            "DE student looking for remote data engineering internship focused on ETL pipelines.",
            major="DE",
            skills=["python", "sql", "kafka"],
            program_type="Internship",
            work_mode="Remote",
            preferred_roles=["Data Engineering"],
        ),
        _profile(
            "cis-business-riyadh",
            "CIS student at PSU seeking business analyst COOP in Riyadh with SQL and Excel.",
            major="CIS",
            university="PSU",
            city="Riyadh",
            skills=["sql", "excel"],
            interest="Information Systems",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Business Analyst"],
        ),
        _profile(
            "cis-systems-jeddah",
            "Computer information systems student in Jeddah looking for systems analyst internship.",
            major="CIS",
            city="Jeddah",
            skills=["sql"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Systems Analyst"],
        ),
        _profile(
            "ce-network-dhahran",
            "Computer engineering student at KFUPM in Dhahran seeking network engineer COOP.",
            major="CE",
            university="KFUPM",
            city="Dhahran",
            skills=["linux", "c++"],
            interest="Computer Engineering",
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Network Engineer"],
        ),
        _profile(
            "ce-embedded-khobar",
            "CE student in Khobar interested in embedded systems and infrastructure engineering internship.",
            major="CE",
            city="Khobar",
            skills=["c++", "linux"],
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Embedded Systems"],
        ),
        _profile(
            "ft-banking-riyadh",
            "Fintech student in Riyadh seeking internship in banking technology and product analytics.",
            major="FT",
            city="Riyadh",
            skills=["sql", "python"],
            interest="FinTech",
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Business Analyst"],
        ),
        _profile(
            "ft-finance-remote",
            "FinTech student looking for remote COOP in finance technology and dashboards.",
            major="FT",
            skills=["sql", "excel"],
            program_type="COOP",
            work_mode="Remote",
            preferred_roles=["FinTech"],
        ),
        _profile(
            "riyadh-only-cs",
            "CS student based in Riyadh seeking any on-site software engineering opportunity.",
            major="CS",
            city="Riyadh",
            skills=["python"],
            program_type="COOP/Internship",
            work_mode="On-site",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "jeddah-ds",
            "Data science student in Jeddah open to internship or COOP in analytics.",
            major="DS",
            city="Jeddah",
            skills=["python", "sql"],
            program_type="COOP/Internship",
            work_mode="Hybrid",
        ),
        _profile(
            "eastern-province-cys",
            "Cybersecurity student in Dammam open to Khobar and Dhahran SOC roles.",
            major="CYS",
            city="Dammam",
            preferred_locations=["Dammam", "Khobar", "Dhahran"],
            skills=["linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["SOC Analyst"],
        ),
        _profile(
            "saudi-arabia-flex",
            "AI student open to opportunities across Saudi Arabia with remote hybrid flexibility.",
            major="AI",
            city="Riyadh",
            preferred_locations=["Saudi Arabia"],
            skills=["python"],
            program_type="Internship",
            work_mode="Hybrid",
        ),
        _profile(
            "remote-only-de",
            "Data engineering student seeking fully remote training anywhere in Saudi Arabia.",
            major="DE",
            city="Remote",
            preferred_locations=["Remote", "Saudi Arabia"],
            skills=["python", "sql"],
            program_type="Training",
            work_mode="Remote",
        ),
        _profile(
            "coop-explicit-cs",
            "Computer science student looking specifically for a COOP program in Riyadh.",
            major="CS",
            city="Riyadh",
            skills=["java"],
            program_type="COOP",
            work_mode="On-site",
        ),
        _profile(
            "internship-explicit-ai",
            "AI student looking specifically for an internship in machine learning.",
            major="AI",
            city="Riyadh",
            skills=["python"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Machine Learning Engineer"],
        ),
        _profile(
            "coop-internship-flex",
            "CS student open to COOP or Internship in software engineering across Riyadh and Jeddah.",
            major="CS",
            city="Riyadh",
            preferred_locations=["Riyadh", "Jeddah"],
            skills=["python", "git"],
            program_type="COOP/Internship",
            work_mode="Hybrid",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "tamheer-cis",
            "CIS student seeking Tamheer program in Riyadh for business and systems analysis.",
            major="CIS",
            city="Riyadh",
            skills=["sql"],
            program_type="Tamheer",
            work_mode="On-site",
            preferred_roles=["Business Analyst", "Systems Analyst"],
        ),
        _profile(
            "training-de",
            "Data engineering student applying for training program with ETL and Python.",
            major="DE",
            city="Riyadh",
            skills=["python", "sql"],
            program_type="Training",
            work_mode="On-site",
            preferred_roles=["Data Engineering"],
        ),
        _profile(
            "in-person-cs",
            "CS student who prefers in person work in Jeddah for software engineering COOP.",
            major="CS",
            city="Jeddah",
            skills=["python"],
            program_type="COOP",
            work_mode="In person",
            preferred_roles=["Software Engineer"],
        ),
        _profile(
            "hybrid-ds-riyadh",
            "Data science student in Riyadh seeking hybrid data analyst COOP.",
            major="DS",
            city="Riyadh",
            skills=["python", "sql"],
            program_type="COOP",
            work_mode="Hybrid",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "no-interview-cs",
            "CS student in Riyadh wants software engineering COOP without interview or direct acceptance.",
            major="CS",
            city="Riyadh",
            skills=["python"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Software Engineer"],
            interview_preference="No interview preferred",
        ),
        _profile(
            "no-interview-ft",
            "Fintech student seeking internship with no interview required in Riyadh.",
            major="FT",
            city="Riyadh",
            skills=["sql"],
            program_type="Internship",
            interview_preference="No interview preferred",
        ),
        _profile(
            "interview-okay-ai",
            "AI student in Jeddah; interview is okay for machine learning internship roles.",
            major="AI",
            city="Jeddah",
            skills=["python"],
            program_type="Internship",
            preferred_roles=["Machine Learning Engineer"],
            interview_preference="Interview okay",
        ),
        _profile(
            "interview-okay-cys",
            "Cybersecurity student in Riyadh; I can do interviews for SOC analyst COOP.",
            major="CYS",
            city="Riyadh",
            skills=["linux"],
            program_type="COOP",
            preferred_roles=["SOC Analyst"],
            interview_preference="Interview okay",
        ),
        _profile(
            "qual-aws-azure",
            "CS student with AWS and Azure certifications seeking cloud engineer internship.",
            major="CS",
            city="Riyadh",
            skills=["python", "linux"],
            qualifications=["AWS", "Azure"],
            program_type="Internship",
            work_mode="Hybrid",
            preferred_roles=["Cloud Engineer"],
        ),
        _profile(
            "qual-security-certs",
            "CYS student with CCNA, Security+, and CEH seeking cybersecurity COOP in Dammam.",
            major="CYS",
            city="Dammam",
            qualifications=["CCNA", "Security+", "CEH"],
            skills=["linux"],
            program_type="COOP",
            work_mode="On-site",
            preferred_roles=["Cybersecurity Analyst"],
        ),
        _profile(
            "qual-powerbi-gpa",
            "Data science student with Power BI and GPA 4.5 seeking analyst internship in Riyadh.",
            major="DS",
            city="Riyadh",
            qualifications=["Power BI", "GPA 4.5"],
            skills=["sql", "python"],
            program_type="Internship",
            preferred_roles=["Data Analyst"],
        ),
        _profile(
            "qual-ielts-intern",
            "Business-oriented CIS student with IELTS 6.5 seeking internship in Jeddah.",
            major="CIS",
            city="Jeddah",
            qualifications=["IELTS"],
            skills=["excel", "sql"],
            program_type="Internship",
            work_mode="On-site",
            preferred_roles=["Business Analyst"],
        ),
        _profile(
            "devops-cs-cloud",
            "CS student targeting DevOps engineer COOP with Docker, Linux, and AWS in Riyadh.",
            major="CS",
            city="Riyadh",
            skills=["docker", "linux", "python"],
            qualifications=["AWS"],
            program_type="COOP",
            work_mode="Hybrid",
            preferred_roles=["DevOps Engineer", "Cloud Engineer"],
        ),
        _profile(
            "open-major-broad",
            "Computing student in Riyadh with Python and SQL open to software or data roles.",
            major="CS",
            city="Riyadh",
            skills=["python", "sql"],
            program_type="COOP/Internship",
            work_mode="Hybrid",
            preferred_roles=["Software Engineer", "Data Analyst"],
        ),
    ]

    if len(profiles) < 40:
        raise ValueError(f"Expected at least 40 synthetic profiles, found {len(profiles)}")

    return profiles


# ---------------------------------------------------------------------------
# Dataset assembly
# ---------------------------------------------------------------------------

def build_regression_rows(
    profiles: Sequence[Tuple[str, str, ParsedProfile]],
    opportunities: Sequence[Opportunity],
) -> List[dict]:
    """Build one CSV row dict per (profile, opportunity) pair."""
    rows: List[dict] = []

    for profile_id, chat_message, profile in profiles:
        for opportunity in opportunities:
            scores = score_profile_opportunity_pair(profile, opportunity)
            role_cluster = infer_role_cluster(opportunity)
            interview_required = infer_interview_required(opportunity)
            verified = infer_verified_opportunity(opportunity)

            rows.append(
                {
                    "profile_id": profile_id,
                    "chat_message": chat_message,
                    "major": profile.major,
                    "university": profile.university,
                    "city": profile.city,
                    "preferred_locations": _join_list(profile.preferred_locations),
                    "skills": _join_list(profile.skills),
                    "qualifications": _join_list(profile.qualifications),
                    "interest": profile.interest,
                    "program_type": profile.program_type,
                    "work_mode": profile.work_mode,
                    "preferred_roles": _join_list(profile.preferred_roles),
                    "interview_preference": profile.interview_preference,
                    "opportunity_id": opportunity.id,
                    "company_name": opportunity.company,
                    "program_name": opportunity.title,
                    "opportunity_city": opportunity.city,
                    "opportunity_program_type": opportunity.program_type,
                    "opportunity_work_mode": opportunity.work_mode,
                    "opportunity_skills": _join_list(opportunity.skills_list),
                    "opportunity_requirements": opportunity.requirements,
                    "opportunity_role_cluster": role_cluster,
                    "interview_required": interview_required,
                    "source_url": opportunity.source_url,
                    "verified_opportunity": verified,
                    **scores,
                }
            )

    return rows


def build_regression_dataset(
    profiles: Optional[Sequence[Tuple[str, str, ParsedProfile]]] = None,
    opportunities: Optional[Sequence[Opportunity]] = None,
) -> pd.DataFrame:
    """Build the full regression dataset dataframe."""
    profile_list = list(profiles or build_synthetic_profiles())
    opportunity_list = list(opportunities or get_candidates())
    rows = build_regression_rows(profile_list, opportunity_list)
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def main() -> None:
    """Generate and save the regression training dataset."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    profiles = build_synthetic_profiles()
    xlsx_loaded = load_opportunities_from_xlsx()
    opportunities = xlsx_loaded if xlsx_loaded else get_candidates()

    if xlsx_loaded:
        print(
            f"[build_regression_dataset] Loaded {len(opportunities)} opportunities "
            f"from {OPPORTUNITIES_XLSX_PATH}"
        )
    else:
        print(
            "[build_regression_dataset] WARNING: Excel file missing or empty — "
            f"using placeholder opportunities ({len(opportunities)} rows). "
            f"Expected path: {OPPORTUNITIES_XLSX_PATH}"
        )

    df = build_regression_dataset(profiles, opportunities)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"[build_regression_dataset] Synthetic profiles: {len(profiles)}")
    print(f"[build_regression_dataset] Opportunities: {len(opportunities)}")
    print(f"[build_regression_dataset] Generated rows: {len(df)}")
    print(f"[build_regression_dataset] Saved to {OUTPUT_FILE}")
    print(
        "[build_regression_dataset] target_score = 100 * ("
        "0.35*major_fit + 0.20*skill_match + 0.15*role_interest + "
        "0.10*city_match + 0.10*program_type + 0.05*work_mode + "
        "0.03*verification + 0.02*interview)"
    )


if __name__ == "__main__":
    main()
