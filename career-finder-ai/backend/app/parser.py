"""
parser.py – Rule-based student message parser.

Extracts structured profile fields from free-text input without requiring
an external LLM.  A Bedrock/LLM integration can replace or augment this
module later.
"""

import re
from typing import List, Optional

from app.schemas import ParsedProfile


# ---------------------------------------------------------------------------
# Lookup dictionaries
# ---------------------------------------------------------------------------

MAJOR_KEYWORDS: dict[str, List[str]] = {
    "CS": ["computer science", "cs student", "software engineering", "se student"],
    "AI": ["artificial intelligence", "ai student", "machine learning", "ml student"],
    "CYS": ["cybersecurity", "cyber security", "information security", "cys student"],
    "CIS": ["computer information systems", "cis student", "information systems"],
    "DS": ["data science", "data scientist", "ds student"],
    "DE": ["data engineering", "data engineer", "de student"],
    "CE": ["computer engineering", "computer engineer", "ce student"],
    "FT": ["fintech", "financial technology", "fin-tech", "ft student"],
}

CITY_KEYWORDS: List[str] = [
    "riyadh",
    "jeddah",
    "dammam",
    "mecca",
    "medina",
    "khobar",
    "dhahran",
    "abha",
    "tabuk",
    "hail",
    "najran",
    "jubail",
]

WORK_MODE_KEYWORDS: dict[str, List[str]] = {
    "Remote": ["remote", "work from home", "wfh", "online"],
    "On-site": ["on-site", "onsite", "on site", "in office", "in-office", "office"],
    "Hybrid": ["hybrid"],
}

PROGRAM_TYPE_KEYWORDS: dict[str, List[str]] = {
    "COOP": ["coop", "co-op", "cooperative", "تعاوني"],
    "Internship": ["internship", "intern", "training", "تدريب"],
}

SKILL_KEYWORDS: List[str] = [
    "python",
    "java",
    "javascript",
    "typescript",
    "sql",
    "r",
    "c++",
    "c#",
    "react",
    "node",
    "django",
    "flask",
    "fastapi",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "docker",
    "linux",
    "git",
    "aws",
    "azure",
    "gcp",
    "tableau",
    "power bi",
    "excel",
    "spark",
    "kafka",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _find_major(text: str) -> Optional[str]:
    """Return the first matching major code from the text."""
    for code, keywords in MAJOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return code
    return None


def _find_city(text: str) -> Optional[str]:
    """Return the first matching Saudi city name from the text."""
    for city in CITY_KEYWORDS:
        if city in text:
            return city.capitalize()
    return None


def _find_work_mode(text: str) -> Optional[str]:
    """Return the first matching work mode from the text."""
    for mode, keywords in WORK_MODE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return mode
    return None


def _find_program_type(text: str) -> Optional[str]:
    """Return the first matching program type from the text."""
    for ptype, keywords in PROGRAM_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return ptype
    return None


def _find_skills(text: str) -> List[str]:
    """Return a sorted list of recognised skills found in the text."""
    found: List[str] = []
    for skill in SKILL_KEYWORDS:
        # Use word-boundary matching for short skill names
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found.append(skill)
    return found


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_message(message: str) -> ParsedProfile:
    """
    Parse a free-text student message and return a structured profile.

    Args:
        message: Raw student input describing their background and preferences.

    Returns:
        A :class:`ParsedProfile` with detected fields (``None`` when not found).
    """
    normalised = message.lower().strip()

    major = _find_major(normalised)
    city = _find_city(normalised)
    work_mode = _find_work_mode(normalised)
    program_type = _find_program_type(normalised)
    skills = _find_skills(normalised)

    # Derive interest from major when possible
    interest_map = {
        "CS": "Software Development",
        "AI": "Artificial Intelligence",
        "CYS": "Cybersecurity",
        "CIS": "Information Systems",
        "DS": "Data Science",
        "DE": "Data Engineering",
        "CE": "Computer Engineering",
        "FT": "FinTech",
    }
    interest = interest_map.get(major, None) if major else None

    return ParsedProfile(
        major=major,
        city=city,
        interest=interest,
        work_mode=work_mode,
        program_type=program_type,
        skills=skills,
    )
