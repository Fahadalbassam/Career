"""
taxonomy.py – Canonical role clusters, interest aliases, city aliases, and skill aliases.

ML-2A introduces a shared taxonomy module so the parser and the rubric can
agree on:

- Role clusters used to label opportunities and group recommendations.
- Interest aliases that map free-text phrases ("security focused",
  "dev ops", "etl pipelines") to canonical interest labels.
- City aliases that normalise Saudi city spellings ("alkhobar", "al khobar",
  "al-khobar" -> "Khobar").
- Skill aliases that fold common spellings into canonical skill tokens
  ("k8s" -> "kubernetes", "infosec" -> "cybersecurity", "ci cd" -> "cicd").

This module is pure data + small pure helpers. It has no I/O and no dependency
on the rest of the application. It is safe to import from both ``app.parser``
and ``app.rubric``.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Role clusters
# ---------------------------------------------------------------------------

# Canonical role clusters used by recommendations and reporting.
ROLE_CLUSTERS: Tuple[str, ...] = (
    "Cybersecurity",
    "SOC Analyst",
    "Network Security",
    "Penetration Testing",
    "Software Engineering",
    "Backend Engineering",
    "Frontend Engineering",
    "Full Stack Engineering",
    "Data Engineering",
    "Data Science",
    "AI / Machine Learning",
    "Cloud / DevOps",
    "QA / Testing",
    "General Computing",
)


# ---------------------------------------------------------------------------
# Interest aliases
# ---------------------------------------------------------------------------

# Canonical interest label -> list of free-text phrases.
#
# We keep backward-compatible labels for tests / persisted profiles:
#     "Cybersecurity", "Software Development", "Data Science", "Data Engineering",
#     "QA/Testing", "FinTech".
# "Cloud / DevOps" is a new canonical introduced in ML-2A (replacing the
# previous "Cloud Computing"). The new label flows into the recommender as a
# free-text interest only; it does not affect persisted schemas.
INTEREST_ALIASES: Dict[str, List[str]] = {
    "Cybersecurity": [
        "security focused",
        "security infrastructure",
        "network security",
        "information security",
        "cyber security",
        "cybersecurity",
        "infosec",
        "soc analyst",
        "soc",
        "siem",
        "blue team",
        "red team",
        "penetration testing",
        "pentesting",
        "pen testing",
        "vulnerability assessment",
        "incident response",
        "ethical hacking",
        "cyber",
        "security",
    ],
    "Cloud / DevOps": [
        "cloud infrastructure",
        "cloud computing",
        "cloud engineer",
        "infrastructure",
        "platform engineering",
        "devops",
        "dev ops",
        "kubernetes",
        "k8s",
        "docker",
        "containers",
        "ci cd",
        "cicd",
        "aws engineer",
        "azure engineer",
        "cloud",
    ],
    "Software Development": [
        "software development",
        "software engineering",
        "backend development",
        "frontend development",
        "full stack",
        "fullstack",
        "web development",
        "mobile development",
        "apis",
        "api development",
        "backend",
        "frontend",
        "software",
    ],
    "Data Engineering": [
        "data engineering",
        "data pipeline",
        "data pipelines",
        "etl",
        "sql pipelines",
        "data warehouse",
    ],
    "Data Science": [
        "data science",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "nlp",
        "natural language processing",
        "computer vision",
        "model training",
        "analytics",
        "ai",
        "ml",
    ],
    "QA/Testing": [
        "quality assurance",
        "software testing",
        "test automation",
        "qa engineer",
        "qa",
        "testing",
    ],
    "FinTech": [
        "fintech",
        "financial technology",
        "fin-tech",
        "banking technology",
    ],
}


# Canonical interest -> default preferred role clusters used by the parser
# when the user states an interest but no specific job title.
INTEREST_TO_ROLE_CLUSTERS: Dict[str, List[str]] = {
    "Cybersecurity": [
        "Cybersecurity",
        "SOC Analyst",
        "Network Security",
        "Penetration Testing",
    ],
    "Cloud / DevOps": [
        "Cloud / DevOps",
        "Infrastructure",
        "Platform Engineering",
    ],
    "Software Development": [
        "Software Engineering",
        "Backend Engineering",
        "Frontend Engineering",
        "Full Stack Engineering",
    ],
    "Data Engineering": [
        "Data Engineering",
        "ETL",
        "Data Pipelines",
    ],
    "Data Science": [
        "Data Science",
        "AI / Machine Learning",
        "Machine Learning",
    ],
    "QA/Testing": [
        "QA / Testing",
        "Test Automation",
    ],
    "FinTech": [
        "FinTech",
        "Financial Technology",
    ],
}


# Canonical interest -> opportunity keywords that should be treated as a strong
# match for the rubric's ``role_interest_score``. These keywords are matched
# against opportunity title / requirements / skills_list / inferred role cluster.
INTEREST_OPPORTUNITY_KEYWORDS: Dict[str, List[str]] = {
    "Cybersecurity": [
        "cybersecurity",
        "cyber security",
        "information security",
        "infosec",
        "soc",
        "soc analyst",
        "security operations",
        "network security",
        "penetration testing",
        "pentesting",
        "vulnerability",
        "incident response",
        "siem",
        "blue team",
        "red team",
    ],
    "Cloud / DevOps": [
        "cloud",
        "devops",
        "dev ops",
        "infrastructure",
        "platform engineering",
        "kubernetes",
        "k8s",
        "docker",
        "ci/cd",
        "cicd",
        "ci cd",
        "site reliability",
        "sre",
    ],
    "Software Development": [
        "software engineer",
        "software engineering",
        "backend",
        "frontend",
        "full stack",
        "fullstack",
        "developer",
        "web development",
        "api",
        "apis",
    ],
    "Data Engineering": [
        "data engineer",
        "data engineering",
        "etl",
        "data pipeline",
        "data pipelines",
        "data warehouse",
        "spark",
        "kafka",
    ],
    "Data Science": [
        "data science",
        "data scientist",
        "machine learning",
        "deep learning",
        "ai engineer",
        "artificial intelligence",
        "nlp",
        "computer vision",
        "analytics",
    ],
    "QA/Testing": [
        "quality assurance",
        "qa",
        "software testing",
        "test automation",
        "qa engineer",
    ],
    "FinTech": [
        "fintech",
        "financial technology",
        "banking",
    ],
}

# Legacy interest labels that the major-derived defaults still emit
# ("Artificial Intelligence", "Information Systems", "Computer Engineering")
# are mapped onto the closest canonical cluster so they continue to receive
# strong role/interest matching from the recommender.
INTEREST_OPPORTUNITY_KEYWORDS["Artificial Intelligence"] = list(
    INTEREST_OPPORTUNITY_KEYWORDS["Data Science"]
)
INTEREST_OPPORTUNITY_KEYWORDS["Information Systems"] = [
    "business analyst",
    "systems analyst",
    "business analysis",
    "information systems",
    "erp",
    "crm",
]
INTEREST_OPPORTUNITY_KEYWORDS["Computer Engineering"] = [
    "embedded",
    "firmware",
    "iot",
    "hardware",
    "network engineer",
    "networking",
]


# ---------------------------------------------------------------------------
# City aliases
# ---------------------------------------------------------------------------

# Lower-case alias -> canonical city name. Aliases include common Saudi city
# spellings (alkhobar, al khobar, al-khobar -> Khobar) plus broader location
# tokens (Remote, Saudi Arabia). The broader tokens are only used when no
# specific Saudi city is mentioned, so they do not stomp on work_mode detection.
CITY_ALIASES: Dict[str, str] = {
    # Khobar
    "alkhobar": "Khobar",
    "al khobar": "Khobar",
    "al-khobar": "Khobar",
    "khobar": "Khobar",
    # Dhahran
    "dhahran": "Dhahran",
    "al dhahran": "Dhahran",
    "al-dhahran": "Dhahran",
    # Dammam
    "dammam": "Dammam",
    "ad dammam": "Dammam",
    "ad-dammam": "Dammam",
    # Riyadh
    "riyadh": "Riyadh",
    "ar riyadh": "Riyadh",
    "ar-riyadh": "Riyadh",
    # Jeddah
    "jeddah": "Jeddah",
    "jedda": "Jeddah",
    # Other recognised Saudi cities (kept for backward compatibility)
    "mecca": "Mecca",
    "medina": "Medina",
    "abha": "Abha",
    "tabuk": "Tabuk",
    "hail": "Hail",
    "najran": "Najran",
    "jubail": "Jubail",
}


# Broader location tokens that should normalise to a canonical "city" only
# when there is no specific Saudi city in the message. These are kept separate
# from ``CITY_ALIASES`` so we do not accidentally treat a remote/COOP message
# as having "Remote" as the city when a real Saudi city is also present.
EXTENDED_LOCATION_ALIASES: Dict[str, str] = {
    "ksa": "Saudi Arabia",
    "saudi": "Saudi Arabia",
    "saudi arabia": "Saudi Arabia",
}


# ---------------------------------------------------------------------------
# Skill aliases
# ---------------------------------------------------------------------------

# Lower-case alias -> canonical skill token. Canonical tokens are kept in
# lower case so they align with the existing ``SKILL_KEYWORDS`` list in
# ``app.parser``.
SKILL_ALIASES: Dict[str, str] = {
    "dev ops": "devops",
    "k8s": "kubernetes",
    "pen testing": "penetration testing",
    "pentesting": "penetration testing",
    "cyber security": "cybersecurity",
    "infosec": "cybersecurity",
    "prompt testing": "prompt engineering",
    "ci cd": "cicd",
    "cicd": "cicd",
    "reactjs": "react",
    "mongo db": "mongodb",
    "mongo": "mongodb",
    "nosql": "nosql",
}


# Tokens that look technical but should never be classified as soft skills.
# Kept separate so the parser can be defensive when expanding skill detection.
SOFT_SKILL_BLOCKLIST: Tuple[str, ...] = (
    "communication",
    "teamwork",
    "leadership",
    "problem solving",
    "time management",
    "critical thinking",
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _word_pattern(phrase: str) -> str:
    """Build a word-bounded regex pattern for a phrase.

    ``re.escape`` keeps slashes and dashes literal. Phrases with ``+`` or ``#``
    fall back to plain substring containment in the caller.
    """
    return r"\b" + re.escape(phrase) + r"\b"


def normalise_skill_aliases(text: str) -> str:
    """
    Replace skill aliases in normalised text with their canonical token.

    Designed to run *after* the parser's standard normalisation step
    (lower-case, dash/whitespace cleanup), so the input here is already
    lower-case and trimmed.

    Examples::

        "i know k8s"     -> "i know kubernetes"
        "experience in pen testing" -> "experience in penetration testing"
        "infosec student" -> "cybersecurity student"
        "ci cd pipelines" -> "cicd pipelines"
    """
    out = text
    # Sort aliases longest-first so multi-word aliases (e.g. "pen testing")
    # take precedence over partial matches.
    for alias in sorted(SKILL_ALIASES.keys(), key=len, reverse=True):
        canonical = SKILL_ALIASES[alias]
        out = re.sub(_word_pattern(alias), canonical, out)
    return out


def find_city_in_text(
    text: str,
    *,
    include_extended: bool = True,
) -> Tuple[Optional[str], List[str]]:
    """
    Find Saudi cities (and optionally broader location tokens) in normalised text.

    Returns a tuple of:
      - the primary city (first match in order of appearance), or ``None``.
      - the list of distinct cities in order of appearance.

    Longest-match-wins: ``"al khobar"`` is preferred over ``"khobar"`` when both
    would match the same span.
    """
    primary_aliases = CITY_ALIASES
    extended_aliases = EXTENDED_LOCATION_ALIASES if include_extended else {}

    primary_matches = _find_alias_matches(text, primary_aliases)

    if primary_matches:
        ordered = _ordered_unique([city for _, city in primary_matches])
        return ordered[0], ordered

    # Only fall back to broader tokens (KSA / Saudi Arabia) when no Saudi
    # city was mentioned. This keeps "I live in Riyadh, KSA" working without
    # also detecting "Saudi Arabia" as a separate preferred location.
    if extended_aliases:
        extended_matches = _find_alias_matches(text, extended_aliases)
        if extended_matches:
            ordered = _ordered_unique([city for _, city in extended_matches])
            return ordered[0], ordered

    return None, []


def find_interest_in_text(text: str) -> Optional[str]:
    """
    Return the canonical interest label whose alias appears in the text.

    Strategy:

    1. If the text contains an explicit ``"interested in <X>"`` phrase, search
       the inner phrase first; this avoids picking up unrelated keywords later
       in the message.
    2. Otherwise (or if the inner phrase yielded nothing), scan the full text.
    3. Within each scan, prefer the earliest alias match. On ties (same
       position), prefer the longest alias so ``"security focused"`` wins over
       the standalone ``"security"`` keyword.
    """
    intent_match = re.search(r"interested\s+in\s+(.{3,80}?)(?:[,.]|$)", text)
    if intent_match:
        canonical = _find_interest_in(intent_match.group(1))
        if canonical:
            return canonical

    return _find_interest_in(text)


def opportunity_keywords_for_interest(interest: Optional[str]) -> List[str]:
    """Return opportunity-side keywords associated with a canonical interest."""
    if not interest:
        return []
    return list(INTEREST_OPPORTUNITY_KEYWORDS.get(interest, []))


def role_clusters_for_interest(interest: Optional[str]) -> List[str]:
    """Return default preferred role clusters for a canonical interest."""
    if not interest:
        return []
    return list(INTEREST_TO_ROLE_CLUSTERS.get(interest, []))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_alias_matches(
    text: str,
    aliases: Dict[str, str],
) -> List[Tuple[int, str]]:
    """Return (position, canonical) for non-overlapping alias matches.

    Longest aliases are matched first so that multi-word spellings claim the
    span before shorter aliases (e.g. ``"al khobar"`` wins over ``"khobar"``).
    """
    matches: List[Tuple[int, int, str]] = []
    used_ranges: List[Tuple[int, int]] = []

    sorted_aliases = sorted(aliases.items(), key=lambda kv: -len(kv[0]))
    for alias, canonical in sorted_aliases:
        for m in re.finditer(_word_pattern(alias), text):
            start, end = m.span()
            if _overlaps(start, end, used_ranges):
                continue
            used_ranges.append((start, end))
            matches.append((start, end, canonical))

    matches.sort(key=lambda item: item[0])
    return [(start, canonical) for start, _, canonical in matches]


def _overlaps(start: int, end: int, ranges: Iterable[Tuple[int, int]]) -> bool:
    for r_start, r_end in ranges:
        if start < r_end and end > r_start:
            return True
    return False


def _ordered_unique(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _find_interest_in(window: str) -> Optional[str]:
    """Scan ``window`` for the best interest alias match.

    "Best" = earliest position. On ties, the longest alias wins so multi-word
    phrases such as ``"security focused"`` outrank the standalone
    ``"security"`` keyword starting at the same offset.
    """
    best_label: Optional[str] = None
    best_position: int = -1
    best_length: int = 0

    for label, phrases in INTEREST_ALIASES.items():
        for phrase in phrases:
            match = re.search(_word_pattern(phrase), window)
            if match is None:
                continue
            position = match.start()
            length = len(phrase)
            if (
                best_position == -1
                or position < best_position
                or (position == best_position and length > best_length)
            ):
                best_label = label
                best_position = position
                best_length = length

    return best_label
