"""
parser.py – Rule-based student message parser.

Extracts structured profile fields from free-text input without requiring
an external LLM. Future extensions could add semantic parsing, but the live
system uses deterministic rules only.
module later.
"""

import re
from typing import List, Optional, Tuple

from app.schemas import ParsedProfile
from app.taxonomy import (
    EASTERN_PROVINCE_CITIES,
    EASTERN_PROVINCE_PHRASES,
    INTEREST_ALIASES,
    SKILL_ALIASES,
    find_city_in_text,
    find_interest_in_text,
    normalise_skill_aliases,
    role_clusters_for_interest,
)


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
    "kubernetes",
    "linux",
    "git",
    "aws",
    "azure",
    "gcp",
    "cloud",
    "tableau",
    "power bi",
    "excel",
    "spark",
    "kafka",
    "devops",
    "networking",
    "cybersecurity",
    "penetration testing",
    "prompt engineering",
    "software testing",
    "qa",
    "soc",
    "siem",
    "mongodb",
    "nosql",
    "infrastructure",
    "network security",
    "incident response",
    "vulnerability assessment",
    "cicd",
    "unity",
    "unreal",
    "airflow",
    "terraform",
    "redis",
    "apis",
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
    ("Security Operations", [
        "security developer operator",
        "security developer",
        "security operations engineer",
        "security operations",
        "security operator",
    ]),
    ("DevSecOps", ["devsecops", "dev sec ops", "devops security"]),
    ("Security Engineering", ["security engineer", "infrastructure security"]),
    ("Network Security", ["network security engineer"]),
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

INTEREST_KEYWORDS: List[Tuple[str, List[str]]] = [
    ("Cybersecurity", [
        "security infrastructure", "penetration testing", "cybersecurity",
        "cyber security", "soc analyst", "siem", "network security",
        "information security", "ethical hacking",
    ]),
    ("Cloud Computing", [
        "cloud computing", "cloud infrastructure", "cloud engineer",
        "devops", "dev ops", "infrastructure", "aws engineer", "azure engineer",
        "kubernetes", "containers",
    ]),
    ("Data Science", [
        "data science", "machine learning", "deep learning",
        "artificial intelligence", "nlp", "natural language processing",
        "computer vision",
    ]),
    ("Data Engineering", [
        "data engineering", "data pipeline", "etl", "data warehouse",
    ]),
    ("Software Development", [
        "software development", "software engineering", "backend development",
        "frontend development", "full stack", "fullstack", "web development",
        "mobile development",
    ]),
    ("QA/Testing", [
        "software testing", "quality assurance", "qa engineer",
        "test automation",
    ]),
    ("FinTech", ["fintech", "financial technology"]),
]

NO_INTERVIEW_PHRASES: List[str] = [
    "without interview",
    "no interview",
    "prefer no interview",
    "do not want an interview",
    "don't want an interview",
    "don't want interview",
    "do not want interview",
    "i don't want interview",
    "i do not want interview",
    "accepts right away",
    "direct acceptance",
]

INTERVIEW_IN_PERSON_PHRASES: List[str] = [
    "interview preference would be in person",
    "interview preference is in person",
    "interview preference in person",
    "my interview to be in person",
    "interview to be in person",
    "would like my interview to be in person",
    "want my interview to be in person",
    "want an interview, in person",
    "want an interview in person",
    "prefer in-person interview",
    "prefer in person interview",
    "in-person interview",
    "in person interview",
    "face to face interview",
    "face-to-face interview",
]

INTERVIEW_REMOTE_PHRASES: List[str] = [
    "online interview",
    "remote interview",
    "virtual interview",
    "video interview",
]

INTERVIEW_PREFERRED_PHRASES: List[str] = [
    "i want an interview",
    "want an interview",
    "with interview",
    "interview preferred",
]

INTERVIEW_OKAY_PHRASES: List[str] = [
    "interview is okay",
    "interview is ok",
    "interview is fine",
    "i can do interview",
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

def _normalize_text(message: str, *, preserve_in_person: bool = False) -> str:
    """
    Normalize raw student text before extracting profile fields.

    This makes different writing styles easier to detect.
    Example:
        "Cyber Security CO-OP in Riyadh!!!"
        becomes
        "cybersecurity coop in riyadh"

    When ``preserve_in_person`` is True, ``in person`` is not rewritten to
    ``on-site`` so interview-mode phrases stay distinct from work-mode parsing.
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
    if not preserve_in_person:
        text = re.sub(r"\bin\s+person\b", "on-site", text)
    text = re.sub(r"\bwork\s+from\s+home\b", "remote", text)

    # Normalize common skill names
    text = re.sub(r"\bpowerbi\b", "power bi", text)
    text = re.sub(r"\bscikit\s+learn\b", "scikit-learn", text)

    # Normalize machine learning spacing (must run before skill-alias pass
    # so the canonical "machine learning" token is present for matching).
    text = re.sub(r"\bmachine[\s-]+learning\b", "machine learning", text)
    text = re.sub(r"\bdevsecops\b", "devsecops", text)
    text = re.sub(r"\bdev\s+sec\s+ops\b", "devsecops", text)

    # Delegate the rest of the skill aliases (dev ops, k8s, pen testing,
    # infosec, cicd, prompt testing, reactjs, ...) to the taxonomy module.
    # This keeps the parser and the taxonomy in sync.
    text = normalise_skill_aliases(text)

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
    _, cities = find_city_in_text(text, include_extended=False)
    return cities


def _mentions_eastern_province(text: str) -> bool:
    return any(phrase in text for phrase in EASTERN_PROVINCE_PHRASES)


def _ordered_unique_cities(cities: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for city in cities:
        if city not in seen:
            seen.add(city)
            out.append(city)
    return out


def _city_in_span(text: str, start: int, end: int) -> Optional[str]:
    """Return the first canonical city mentioned in ``text[start:end]``."""
    window = text[start:end]
    primary, _ = find_city_in_text(window, include_extended=False)
    return primary


def _detect_home_city(text: str) -> Optional[str]:
    """Infer home/base city from common phrasing."""
    home_patterns = (
        r"\bi\s*m\s+in\s+",
        r"\bi\s+live\s+in\s+",
        r"\bbased\s+in\s+",
        r"\bfrom\s+",
    )
    for pattern in home_patterns:
        for match in re.finditer(pattern, text):
            city = _city_in_span(text, match.end(), min(len(text), match.end() + 60))
            if city:
                return city
    return None


def _detect_location_flexibility(text: str) -> Optional[str]:
    # "open to internships/coops in …" is a preferred-location phrase, not flexibility.
    if "open to internships" in text or "open to internship" in text:
        open_to_flexible = False
    elif "open to coop" in text or "open to coops" in text:
        open_to_flexible = False
    else:
        open_to_flexible = "open to" in text

    flexible_markers = (
        "don't mind",
        "dont mind",
        "don t mind",
        "do not mind",
        "idm",
        "i can go to",
        "can go to",
        "i can travel to",
        "can travel to",
        "willing to travel",
        "willing to go",
        "no problem going",
        "no problem with",
    )
    moderate_markers = (
        "is fine",
        "are fine",
        "fine with",
        "okay with",
        "ok with",
        "would consider",
        "can consider",
    )
    strict_markers = (
        "only in",
        "only at",
        "must be in",
        "strictly in",
    )

    if any(marker in text for marker in strict_markers):
        return "strict"
    if open_to_flexible or any(marker in text for marker in flexible_markers):
        return "flexible"
    if any(marker in text for marker in moderate_markers):
        return "moderate"
    return None


def _cities_after_phrases(text: str, phrases: Tuple[str, ...]) -> List[str]:
    found: List[str] = []
    for phrase in sorted(phrases, key=len, reverse=True):
        pattern = r"\b" + re.escape(phrase) + r"\b"
        for match in re.finditer(pattern, text):
            city = _city_in_span(
                text,
                match.end(),
                min(len(text), match.end() + 80),
            )
            if city and city not in found:
                found.append(city)
    return found


def _resolve_location_fields(
    text: str,
) -> Tuple[
    Optional[str],
    Optional[str],
    List[str],
    List[str],
    Optional[str],
]:
    """
    Resolve city, home city, preferred/acceptable locations, and flexibility.

    Backward compatibility:
      - Single city with no flexibility cues -> ``city`` set, lists empty.
      - Multiple cities without flexibility cues -> first city + full list in
        ``preferred_locations`` (legacy behaviour).
    """
    cities = _ordered_unique_cities(_find_cities_in_order(text))
    home_city = _detect_home_city(text)
    flexibility = _detect_location_flexibility(text)

    preferred_phrases = (
        "open to internships in",
        "open to internship in",
        "open to coops in",
        "open to coop in",
        "looking for coops in",
        "looking for coop in",
        "looking for internships in",
        "looking for internship in",
        "looking for an internship in",
        "looking for a coop in",
    )
    travel_phrases = (
        "can travel to",
        "can go to",
        "i can travel to",
        "i can go to",
        "travel to",
    )

    phrase_preferred = _cities_after_phrases(text, preferred_phrases)
    for match in re.finditer(r"\bprefer(?:red)?\b", text):
        end = match.end()
        but_idx = text.find(" but ", end)
        window_end = but_idx if but_idx != -1 else min(len(text), end + 45)
        city = _city_in_span(text, end, window_end)
        if city and city not in phrase_preferred:
            phrase_preferred.append(city)
    travel_cities = _cities_after_phrases(text, travel_phrases)

    eastern_preferred: List[str] = []
    if _mentions_eastern_province(text) and any(
        token in text for token in ("prefer", "preferred", "eastern")
    ):
        eastern_preferred = list(EASTERN_PROVINCE_CITIES)

    if not cities and not eastern_preferred and not phrase_preferred:
        return None, home_city, [], [], flexibility

    preferred: List[str] = list(eastern_preferred)
    for city in phrase_preferred:
        if city not in preferred:
            preferred.append(city)

    acceptable: List[str] = []
    for city in travel_cities:
        if city not in preferred and city not in acceptable:
            acceptable.append(city)

    if flexibility:
        if eastern_preferred and not home_city:
            anchor = eastern_preferred[0]
        else:
            anchor = home_city or (cities[0] if cities else None)
        if anchor is None and preferred:
            anchor = preferred[0]
        if anchor and anchor not in preferred and not eastern_preferred:
            preferred.insert(0, anchor)
        elif anchor and home_city and anchor not in preferred:
            preferred.insert(0, anchor)
        if anchor and not eastern_preferred:
            for city in cities:
                if city == anchor:
                    continue
                if city not in preferred and city not in acceptable:
                    acceptable.append(city)
        for city in travel_cities:
            if city not in preferred and city not in acceptable:
                acceptable.append(city)
        if eastern_preferred:
            primary = eastern_preferred[0]
        else:
            primary = anchor or (preferred[0] if preferred else None)
    elif len(cities) > 1:
        primary = cities[0]
        preferred = list(cities)
        acceptable = []
    elif len(cities) == 1:
        primary = cities[0]
        if phrase_preferred:
            primary = phrase_preferred[0]
            preferred = list(phrase_preferred)
        else:
            preferred = []
        acceptable = []
    else:
        primary = preferred[0] if preferred else None
        acceptable = list(acceptable)

    if home_city:
        primary = home_city

    if (
        preferred
        and primary
        and len(preferred) == 1
        and preferred[0] == primary
        and not acceptable
        and not flexibility
    ):
        preferred = []

    preferred = _ordered_unique_cities(preferred)
    acceptable = _ordered_unique_cities(
        [c for c in acceptable if c not in preferred]
    )

    return primary, home_city, preferred, acceptable, flexibility


def _scrub_interview_scoped_work_mode_tokens(text: str) -> str:
    """Remove on-site/remote tokens that refer to interviews, not COOP work mode."""
    scrubbed = re.sub(
        r"\b(?:interview\w*|interviews)\b.{0,18}\bon-site\b",
        " ",
        text,
    )
    scrubbed = re.sub(
        r"\bon-site\b.{0,12}\b(?:interview\w*|interviews)\b",
        " ",
        scrubbed,
    )
    scrubbed = re.sub(
        r"\b(?:interview\w*|interviews)\b.{0,18}\bremote\b",
        " ",
        scrubbed,
    )
    return scrubbed


def _find_work_mode(text: str) -> Optional[str]:
    """Return the first matching work mode from the text."""
    scrubbed = _scrub_interview_scoped_work_mode_tokens(text)
    for mode, keywords in WORK_MODE_KEYWORDS.items():
        for kw in keywords:
            if kw in scrubbed:
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
    if "apis" not in found and re.search(
        r"\b(?:rest(?:ful)?\s+)?apis?\b|\bapi\s+development\b|\b(?:backend|web)\s+api\b",
        text,
    ):
        found.append("apis")
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


def _find_interest_from_text(text: str) -> Optional[str]:
    """
    Detect explicit interest areas from text phrases.

    Used as an override when the student states a concrete domain interest
    (e.g. "security focused" or "interested in security infrastructure")
    rather than letting the major alone drive the interest field.

    Delegates to :func:`app.taxonomy.find_interest_in_text` which supports the
    full set of ML-2A aliases (security focused, infosec, dev ops, ci cd,
    pen testing, model training, ...).
    """
    return find_interest_in_text(text)


def _mentions_interview_context(text: str) -> bool:
    return "interview" in text


def _find_interview_preference(text: str) -> Optional[str]:
    """Return interview stance when explicitly mentioned (interview context only)."""
    for phrase in ("direct acceptance", "accepts right away"):
        if phrase in text:
            return "No interview preferred"

    if not _mentions_interview_context(text):
        return None

    for phrase in NO_INTERVIEW_PHRASES:
        if phrase in text:
            return "No interview preferred"

    for phrase in INTERVIEW_OKAY_PHRASES:
        if phrase in text:
            return "Interview okay"

    for phrase in INTERVIEW_IN_PERSON_PHRASES:
        if phrase in text:
            return "Interview preferred: In person"

    for phrase in INTERVIEW_REMOTE_PHRASES:
        if phrase in text:
            return "Interview preferred: Remote"

    for phrase in INTERVIEW_PREFERRED_PHRASES:
        if phrase in text:
            return "Interview preferred"

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
    normalised_interview = _normalize_text(message, preserve_in_person=True)
    normalised = _normalize_text(message)

    major = _find_major(normalised)
    university = _find_university(normalised)
    (
        city,
        home_city,
        preferred_locations,
        acceptable_locations,
        location_flexibility,
    ) = _resolve_location_fields(normalised)
    work_mode = _find_work_mode(normalised)
    program_type = _find_program_type(normalised)
    qualifications = _find_qualifications(normalised)
    skills = _filter_skills_overlapping_qualifications(
        _find_skills(normalised),
        qualifications,
    )
    preferred_roles = _find_preferred_roles(normalised)
    interview_preference = _find_interview_preference(normalised_interview)

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
    # Text-based interest overrides major default when an explicit domain is stated.
    text_interest = _find_interest_from_text(normalised)
    major_interest = interest_map.get(major, None) if major else None
    interest = text_interest or major_interest

    # When the user states an interest but no specific job title, seed
    # ``preferred_roles`` with the corresponding cluster (e.g. interest
    # "Cybersecurity" -> ["Cybersecurity", "SOC Analyst", "Network Security",
    # "Penetration Testing"]). Explicitly detected roles take priority and are
    # kept ahead of the cluster fallback.
    if text_interest and not preferred_roles:
        cluster_roles = role_clusters_for_interest(text_interest)
        if cluster_roles:
            preferred_roles = list(cluster_roles)

    return ParsedProfile(
        major=major,
        university=university,
        city=city,
        home_city=home_city,
        preferred_locations=preferred_locations,
        acceptable_locations=acceptable_locations,
        location_flexibility=location_flexibility,
        skills=skills,
        qualifications=qualifications,
        interest=interest,
        program_type=program_type,
        work_mode=work_mode,
        preferred_roles=preferred_roles,
        interview_preference=interview_preference,
    )
