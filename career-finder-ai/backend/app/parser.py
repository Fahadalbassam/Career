"""
parser.py – Rule-based student message parser.

Extracts structured profile fields from free-text input without requiring
an external LLM.  A Bedrock/LLM integration can replace or augment this
module later.
"""

import re
from typing import List, Optional, Tuple

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

UNIVERSITY_KEYWORDS: dict[str, List[str]] = {
    "IAU": [
        "imam abdulrahman bin faisal university",
        "imam abdulrahman university",
        "iau",
    ],
    "KFUPM": [
        "king fahd university of petroleum and minerals",
        "kfupm",
    ],
    "KSU": ["king saud university", "ksu"],
    "KAU": ["king abdulaziz university", "kau"],
    "PSU": ["prince sultan university", "psu"],
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

# (canonical label, keyword phrases) — longer phrases should be listed first per role
ROLE_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("Machine Learning Engineer", ["machine learning engineer"]),
    ("Full Stack Developer", ["full stack developer", "fullstack developer"]),
    ("Software Engineer", ["software engineer", "software engineering"]),
    ("Data Scientist", ["data scientist"]),
    ("Data Analyst", ["data analyst"]),
    ("AI Engineer", ["ai engineer"]),
    ("Cybersecurity Analyst", ["cybersecurity analyst"]),
    ("SOC Analyst", ["soc analyst"]),
    ("Network Engineer", ["network engineer"]),
    ("Cloud Engineer", ["cloud engineer"]),
    ("DevOps Engineer", ["devops engineer", "dev ops engineer"]),
    ("Business Analyst", ["business analyst"]),
    ("Systems Analyst", ["systems analyst"]),
    ("Frontend Developer", ["frontend developer", "front end developer"]),
    ("Backend Developer", ["backend developer", "back end developer"]),
]

QUALIFICATION_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("Google Data Analytics", ["google data analytics"]),
    ("Security+", ["security+", "security plus"]),
    ("Network+", ["network+", "network plus"]),
    ("Power BI", ["power bi certified", "power bi certification"]),
    ("CompTIA", ["comptia"]),
    ("CCNA", ["ccna"]),
    ("CEH", ["ceh"]),
    ("IELTS", ["ielts"]),
    ("AWS", ["aws certified", "aws certification", "aws"]),
    ("Azure", ["azure certified", "azure certification", "azure"]),
]

NO_INTERVIEW_PHRASES: List[str] = [
    "without interview",
    "no interview",
    "accepts right away",
    "direct acceptance",
]

INTERVIEW_OKAY_PHRASES: List[str] = [
    "interview is okay",
    "interview is ok",
    "i can do interviews",
    "interviews are okay",
    "interview okay",
]

# Skills also detected as qualifications — omit from skills when listed as quals
QUALIFICATION_SKILL_OVERLAP: dict[str, str] = {
    "aws": "AWS",
    "azure": "Azure",
    "power bi": "Power BI",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _normalize_text(message: str) -> str:
    """
    Normalize raw student text before extracting profile fields.

    This makes different writing styles easier to detect.
    Example:
        "Cyber Security CO-OP in Riyadh!!!"
        becomes
        "cybersecurity coop in riyadh"
    """
    text = message.lower().strip()

    # Normalize common symbols/dashes
    text = text.replace("–", "-").replace("—", "-")

    # Normalize common phrases
    text = re.sub(r"\bcyber\s+security\b", "cybersecurity", text)
    text = re.sub(r"\bco\s*-\s*op\b", "coop", text)
    text = re.sub(r"\bco\s+op\b", "coop", text)
    text = re.sub(r"\bcooperative\s+training\b", "coop", text)

    # Normalize work mode phrases
    text = re.sub(r"\bon\s*-\s*site\b", "on-site", text)
    text = re.sub(r"\bon\s+site\b", "on-site", text)
    text = re.sub(r"\bin\s+person\b", "on-site", text)
    text = re.sub(r"\bwork\s+from\s+home\b", "remote", text)

    # Normalize common skill names
    text = re.sub(r"\bpowerbi\b", "power bi", text)
    text = re.sub(r"\bscikit\s+learn\b", "scikit-learn", text)

    # Preserve GPA decimals before punctuation is stripped (e.g. GPA 4.5 → gpa 4_5)
    text = re.sub(
        r"\bgpa\s*(?:is\s*)?(\d+)\.(\d+)\b",
        r"gpa \1_\2",
        text,
    )

    # Remove unnecessary punctuation but keep useful symbols for skills
    # Keeps: +, #, and - for skills like C++, C#, scikit-learn, on-site
    # Underscore is kept for preserved GPA decimals (e.g. gpa 4_5)
    text = re.sub(r"[^a-z0-9+#_\-\s]", " ", text)

    # Collapse repeated spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _find_major(text: str) -> Optional[str]:
    """Return the first matching major code from the text."""
    for code, keywords in MAJOR_KEYWORDS.items():
        for kw in sorted(keywords, key=len, reverse=True):
            if kw in text:
                return code
    return None


def _find_university(text: str) -> Optional[str]:
    """Return a university code when a known institution is mentioned."""
    best_code: Optional[str] = None
    best_len = 0

    for code, keywords in UNIVERSITY_KEYWORDS.items():
        for kw in sorted(keywords, key=len, reverse=True):
            if kw in text and len(kw) > best_len:
                best_code = code
                best_len = len(kw)

    return best_code


def _find_cities_in_order(text: str) -> List[str]:
    """Return unique Saudi cities in order of first appearance."""
    matches: List[Tuple[int, str]] = []

    for city in CITY_KEYWORDS:
        pattern = r"\b" + re.escape(city) + r"\b"
        for match in re.finditer(pattern, text):
            matches.append((match.start(), city.capitalize()))

    matches.sort(key=lambda item: item[0])

    ordered: List[str] = []
    for _, city_name in matches:
        if city_name not in ordered:
            ordered.append(city_name)

    return ordered


def _resolve_city_and_preferred_locations(
    text: str,
) -> Tuple[Optional[str], List[str]]:
    """
  Resolve primary city and preferred locations.

  - One city: ``city`` is set, ``preferred_locations`` is empty (backward compatible).
  - Multiple cities: ``city`` is the first mentioned; ``preferred_locations`` lists all.
    """
    cities = _find_cities_in_order(text)

    if not cities:
        return None, []

    if len(cities) == 1:
        return cities[0], []

    return cities[0], cities


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
    """Return recognised skills found in the text."""
    found: List[str] = []
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found.append(skill)
    return found


def _find_qualifications(text: str) -> List[str]:
    """Return certifications, credentials, and GPA tokens."""
    found: List[str] = []

    for label, keywords in QUALIFICATION_KEYWORDS:
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b" if "+" not in kw else re.escape(kw)
            if "+" in kw:
                if kw in text and label not in found:
                    found.append(label)
                    break
            elif re.search(pattern, text):
                if label not in found:
                    found.append(label)
                break

    gpa_match = re.search(r"\bgpa\s*(?:is\s*)?(\d+)_(\d+)\b", text)
    if gpa_match:
        found.append(f"GPA {gpa_match.group(1)}.{gpa_match.group(2)}")
    else:
        gpa_whole = re.search(r"\bgpa\s*(?:is\s*)?(\d+(?:\.\d+)?)\b", text)
        if gpa_whole:
            found.append(f"GPA {gpa_whole.group(1)}")

    return found


def _find_preferred_roles(text: str) -> List[str]:
    """Return role titles inferred from career-intent phrases."""
    found: List[str] = []

    for label, keywords in ROLE_KEYWORDS:
        for kw in sorted(keywords, key=len, reverse=True):
            if kw in text and label not in found:
                found.append(label)
                break

    return found


def _find_interview_preference(text: str) -> Optional[str]:
    """Return interview stance when explicitly mentioned."""
    for phrase in NO_INTERVIEW_PHRASES:
        if phrase in text:
            return "No interview preferred"

    for phrase in INTERVIEW_OKAY_PHRASES:
        if phrase in text:
            return "Interview okay"

    return None


def _filter_skills_overlapping_qualifications(
    skills: List[str],
    qualifications: List[str],
) -> List[str]:
    """Remove skill tokens that were captured as qualifications (e.g. AWS cert)."""
    qual_set = {q.lower() for q in qualifications}

    filtered: List[str] = []
    for skill in skills:
        qual_label = QUALIFICATION_SKILL_OVERLAP.get(skill)
        if qual_label and qual_label.lower() in qual_set:
            continue
        if skill.lower() in qual_set:
            continue
        filtered.append(skill)

    return filtered


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
    normalised = _normalize_text(message)

    major = _find_major(normalised)
    university = _find_university(normalised)
    city, preferred_locations = _resolve_city_and_preferred_locations(normalised)
    work_mode = _find_work_mode(normalised)
    program_type = _find_program_type(normalised)
    qualifications = _find_qualifications(normalised)
    skills = _filter_skills_overlapping_qualifications(
        _find_skills(normalised),
        qualifications,
    )
    preferred_roles = _find_preferred_roles(normalised)
    interview_preference = _find_interview_preference(normalised)

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
        university=university,
        city=city,
        preferred_locations=preferred_locations,
        skills=skills,
        qualifications=qualifications,
        interest=interest,
        program_type=program_type,
        work_mode=work_mode,
        preferred_roles=preferred_roles,
        interview_preference=interview_preference,
    )
