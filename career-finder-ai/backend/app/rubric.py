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

from app.opportunity_enrichment import (
    ROLE_SKILL_PROFILES,
    enrich_opportunity_signals,
    fired_role_skill_profile_keys,
)
from app.schemas import Opportunity, ParsedProfile
from app.taxonomy import (
    INTEREST_OPPORTUNITY_KEYWORDS,
    SKILL_ALIASES,
    opportunity_keywords_for_interest,
)


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
    ("Security Operations", ["security operations", "security operator"]),
    ("DevSecOps", ["devsecops", "dev sec ops"]),
    ("Security Engineering", ["security engineer"]),
    ("Network Security", ["network security engineer", "network security"]),
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

# Opportunity skills a student token satisfies for *missing-skills display* only.
# Does not change rubric weights or match_score.
_STUDENT_SKILL_SATISFIES: dict[str, frozenset[str]] = {
    "cybersecurity": frozenset(
        {
            "cybersecurity fundamentals",
            "security fundamentals",
            "cyber security",
            "infosec",
            "information security",
        }
    ),
    "siem": frozenset({"siem"}),
    "networking": frozenset({"networking", "network security", "network fundamentals"}),
    "linux": frozenset({"linux"}),
    "kubernetes": frozenset({"kubernetes", "k8s"}),
    "k8s": frozenset({"kubernetes", "k8s"}),
    "power bi": frozenset({"power bi", "powerbi"}),
    "powerbi": frozenset({"power bi", "powerbi"}),
    "node.js": frozenset({"node.js", "nodejs", "node js"}),
    "nodejs": frozenset({"node.js", "nodejs", "node js"}),
    "git": frozenset({"git"}),
    "apis": frozenset(
        {
            "apis",
            "api",
            "rest api",
            "rest apis",
            "api development",
        }
    ),
    "api": frozenset(
        {
            "apis",
            "api",
            "rest api",
            "rest apis",
            "api development",
        }
    ),
}

# Student interest / preferred role -> ROLE_SKILL_PROFILES keys (SCORE-AUDIT-2).
_INTEREST_PROFILE_KEYS: dict[str, frozenset[str]] = {
    "cybersecurity": frozenset({"Cybersecurity", "Network Security"}),
    "cloud / devops": frozenset({"Cloud / DevOps"}),
    "software development": frozenset({"Backend Engineering", "Frontend Engineering"}),
    "data science": frozenset({"Data Science"}),
    "data engineering": frozenset({"Data Engineering"}),
    "ai / machine learning": frozenset({"AI / Machine Learning"}),
    "fintech": frozenset({"Backend Engineering"}),
}

_PREFERRED_ROLE_PROFILE_KEYS: List[Tuple[str, str]] = [
    ("security operations", "Cybersecurity"),
    ("soc analyst", "Cybersecurity"),
    ("soc operations", "Cybersecurity"),
    ("soc monitoring", "Cybersecurity"),
    ("network security", "Network Security"),
    ("network engineer", "Network Security"),
    ("backend developer", "Backend Engineering"),
    ("backend development", "Backend Engineering"),
    ("frontend developer", "Frontend Engineering"),
    ("full stack", "Backend Engineering"),
    ("cloud / devops", "Cloud / DevOps"),
    ("devops", "Cloud / DevOps"),
    ("data scientist", "Data Science"),
    ("data analyst", "Data Science"),
    ("machine learning", "AI / Machine Learning"),
]

_SKILL_TIER_WEIGHTS: dict[str, float] = {
    "explicit": 1.0,
    "required": 0.7,
    "preferred": 0.4,
    "inferred": 0.5,
}

_EXTRA_SKILL_COMPARE: dict[str, str] = {
    "power bi": "powerbi",
    "node js": "nodejs",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "powerbi": "powerbi",
    "api": "apis",
    "apis": "apis",
    "rest api": "apis",
    "rest apis": "apis",
    "api development": "apis",
}


def _compact_skill_token(value: str) -> str:
    return re.sub(r"[\s.\-_/+]+", "", normalize_text(value))


def _skill_compare_forms(token: str) -> set[str]:
    norm = normalize_text(token)
    forms = {norm, _compact_skill_token(norm)}
    if norm in SKILL_ALIASES:
        canonical = SKILL_ALIASES[norm]
        forms.add(canonical)
        forms.add(_compact_skill_token(canonical))
    for alias, canonical in SKILL_ALIASES.items():
        if alias == norm or canonical == norm:
            forms.add(_compact_skill_token(alias))
            forms.add(_compact_skill_token(canonical))
    if norm in _EXTRA_SKILL_COMPARE:
        canonical = _EXTRA_SKILL_COMPARE[norm]
        forms.add(canonical)
        forms.add(_compact_skill_token(canonical))
    return forms


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


def _clean_explicit_opportunity_skills(opportunity: Opportunity) -> List[str]:
    """Declared ``skills_list`` entries, preserving display spelling."""
    out: List[str] = []
    seen: set[str] = set()
    for raw in opportunity.skills_list or []:
        cleaned = str(raw).strip()
        normalized = cleaned.lower()
        if not normalized or normalized in SKILL_NOISE_TOKENS:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        out.append(cleaned)
    return out


def _student_aligned_profile_keys(profile: ParsedProfile) -> set[str]:
    """Role-profile keys implied by the student's interest and preferred roles."""
    keys: set[str] = set()
    interest = normalize_text(profile.interest)
    if interest:
        for label, profile_keys in _INTEREST_PROFILE_KEYS.items():
            if label in interest or interest in label:
                keys.update(profile_keys)
    for role in normalize_list(profile.preferred_roles):
        for needle, profile_key in _PREFERRED_ROLE_PROFILE_KEYS:
            if needle in role:
                keys.add(profile_key)
    return keys


def _filtered_role_profile_keys(
    opportunity: Opportunity,
    profile: Optional[ParsedProfile],
) -> List[str]:
    """Fired role profiles, narrowed to the student's interest when possible."""
    fired = fired_role_skill_profile_keys(opportunity)
    if profile is None:
        return fired
    aligned = _student_aligned_profile_keys(profile)
    if not aligned:
        return fired
    filtered = [key for key in fired if key in aligned]
    return filtered if filtered else fired


def _dedupe_skill_tier_entries(
    entries: Iterable[Tuple[str, str]],
) -> List[Tuple[str, str]]:
    """Drop duplicate opportunity skills; keep the strongest tier per skill."""
    tier_rank = {"explicit": 4, "required": 3, "preferred": 2, "inferred": 1}
    best: dict[str, Tuple[str, str]] = {}
    order: List[str] = []
    for skill, tier in entries:
        norm = str(skill).strip().lower()
        if not norm or norm in SKILL_NOISE_TOKENS:
            continue
        if norm not in best:
            order.append(norm)
            best[norm] = (skill, tier)
            continue
        prev_tier = best[norm][1]
        if tier_rank.get(tier, 0) > tier_rank.get(prev_tier, 0):
            best[norm] = (skill, tier)
    return [best[norm] for norm in order]


def _role_profile_skill_entries(profile_keys: Sequence[str]) -> List[Tuple[str, str]]:
    entries: List[Tuple[str, str]] = []
    seen_required: set[str] = set()
    for key in profile_keys:
        profile = ROLE_SKILL_PROFILES.get(key)
        if not profile:
            continue
        for skill in profile.get("required", []):
            norm = str(skill).lower()
            if norm in seen_required:
                continue
            seen_required.add(norm)
            entries.append((skill, "required"))
        for skill in profile.get("preferred", []):
            if str(skill).lower() in seen_required:
                continue
            entries.append((skill, "preferred"))
    return entries


def _opportunity_relevant_skill_entries(
    opportunity: Opportunity,
    profile: Optional[ParsedProfile] = None,
) -> List[Tuple[str, str]]:
    """Layered opportunity skills for scoring (SCORE-AUDIT-2).

  1. Explicit ``skills_list`` when present.
    2. Role-cluster required / preferred from interest-filtered profiles.
    3. Company-level bucket ``inferred_skills`` only when (1) and (2) are empty.
    """
    explicit = _clean_explicit_opportunity_skills(opportunity)
    if explicit:
        return [(skill, "explicit") for skill in explicit]

    role_keys = _filtered_role_profile_keys(opportunity, profile)
    role_entries = _role_profile_skill_entries(role_keys)
    if role_entries:
        return _dedupe_skill_tier_entries(role_entries)

    inferred = enrich_opportunity_signals(opportunity).get("inferred_skills", []) or []
    return [(str(skill), "inferred") for skill in inferred]  # type: ignore[arg-type]


def _role_profile_skill_lists(
    opportunity: Opportunity,
    profile: Optional[ParsedProfile],
) -> Tuple[List[str], List[str]]:
    """Required and preferred lists from interest-filtered role profiles."""
    keys = _filtered_role_profile_keys(opportunity, profile)
    required: List[str] = []
    preferred: List[str] = []
    seen_required: set[str] = set()
    for key in keys:
        role_profile = ROLE_SKILL_PROFILES.get(key)
        if not role_profile:
            continue
        for skill in role_profile.get("required", []):
            norm = str(skill).lower()
            if norm in seen_required:
                continue
            seen_required.add(norm)
            required.append(skill)
        for skill in role_profile.get("preferred", []):
            if str(skill).lower() in seen_required:
                continue
            preferred.append(skill)
    return required, preferred


def compute_profile_skills_matched(
    profile: ParsedProfile,
    opportunity: Opportunity,
) -> List[str]:
    """Profile skill labels that satisfy an opportunity-relevant skill."""
    searchable = _opportunity_search_text(opportunity)
    entries = _opportunity_relevant_skill_entries(opportunity, profile)
    matched: List[str] = []
    seen: set[str] = set()

    for skill in profile.skills or []:
        norm = normalize_text(skill)
        if not norm or norm in seen:
            continue
        if norm in searchable:
            seen.add(norm)
            matched.append(skill)
            continue
        token_set = {norm}
        if any(_student_covers_skill(token_set, opp_skill) for opp_skill, _ in entries):
            seen.add(norm)
            matched.append(skill)
            continue
        if any(_skill_compare_forms(norm) & _skill_compare_forms(opp_skill) for opp_skill, _ in entries):
            seen.add(norm)
            matched.append(skill)

    return matched


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
    """Skill match score in [0, 1].

    SCORE-AUDIT-2: opportunity-centric coverage. Extra student skills that are
    not relevant to the opportunity do **not** dilute the score.

    ``skill_score = sum(tier_weight for covered opp skills) / sum(tier_weight
    for all opportunity-relevant skills)``

    Opportunity-relevant skills follow the same layering as
    :func:`_opportunity_relevant_skill_entries` (explicit list, then
    interest-filtered role-cluster profiles, then bucket inferred fallback).

    Tier weights: explicit ``1.0``, required ``0.7``, preferred ``0.4``,
    inferred ``0.5``.
    """
    if not profile.skills and not profile.qualifications:
        return 0.4

    entries = _opportunity_relevant_skill_entries(opportunity, profile)
    if not entries:
        return 0.4

    student = _student_skill_set(profile)
    matched_weight = 0.0
    total_weight = 0.0
    for opp_skill, tier in entries:
        weight = _SKILL_TIER_WEIGHTS.get(tier, 0.5)
        total_weight += weight
        if _student_covers_skill(student, opp_skill):
            matched_weight += weight

    if total_weight <= 0.0:
        return 0.4
    return matched_weight / total_weight


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
    """Score how well an opportunity matches the student's role/interest signals.

    Strategy (ordered, first match wins):

    1. Direct token match — the student's interest or preferred role text
       appears verbatim in the opportunity text / role cluster.
    2. ROLE_EXACT_KEYWORDS overlap — both sides reference the same canonical
       role family (e.g. "soc analyst").
    3. Interest cluster match — the student's interest is in the ML-2A
       taxonomy and the opportunity contains one of its cluster keywords
       (e.g. ``interest="Cybersecurity"`` -> matches "soc", "network security",
       "incident response", ...). Returns ``0.8`` for cluster hits via the
       opportunity title/role cluster, ``0.6`` when the hit is only in the
       skills_list (partial match).
    4. Role family overlap — looser family-level match. Returns ``0.6``.
    5. Generic technical fallback — opportunity mentions any generic
       technical term. Returns ``0.3`` so a cybersecurity-focused student
       does not get over-boosted on a plain software listing.
    6. Zero otherwise.
    """
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

    # ML-2A: interest cluster match via taxonomy.
    interest_keywords = opportunity_keywords_for_interest(profile.interest)
    if interest_keywords:
        title_and_cluster = normalize_text(
            " ".join([opportunity.title, role_cluster])
        )
        if contains_any(title_and_cluster, interest_keywords):
            return 0.8
        if contains_any(role_text, interest_keywords):
            # Hit was further down (requirements / skills_list); treat as a
            # partial match per the ML-2A spec.
            return 0.6

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

    # ML-2B: weak inferred-interest match. When the opportunity has no
    # explicit role/cluster keywords for the user's interest, fall back to
    # the runtime enrichment layer. A hit here is treated as a weak signal
    # (0.5) so it can lift a near-miss but never overrule an explicit
    # cluster match (0.8) or a direct token match (1.0).
    if profile.interest:
        inferred = enrich_opportunity_signals(opportunity)["inferred_interests"]
        if profile.interest in inferred:  # type: ignore[operator]
            return 0.5

    if any(term in role_text for term in GENERIC_TECHNICAL_TERMS):
        return 0.3

    return 0.0


def compute_city_match_score(profile: ParsedProfile, opportunity: Opportunity) -> float:
    opp_city = normalize_text(opportunity.city)
    if not opp_city or opp_city == "not stated":
        return 0.3

    preferred = {normalize_text(c) for c in profile.preferred_locations}
    preferred.discard("")
    acceptable = {normalize_text(c) for c in profile.acceptable_locations}
    acceptable.discard("")
    student_city = normalize_text(profile.city)
    home_city = normalize_text(profile.home_city) or student_city

    if preferred and opp_city in preferred:
        return 1.0

    if student_city and student_city == opp_city:
        return 1.0

    if home_city and home_city == opp_city:
        return 1.0

    if acceptable and opp_city in acceptable:
        return 0.85

    anchor = home_city or student_city
    if anchor in EASTERN_PROVINCE and opp_city in EASTERN_PROVINCE:
        return 0.7

    if opp_city in FLEXIBLE_CITIES:
        return 0.5

    if _normalize_work_mode(opportunity.work_mode) == "remote":
        return 0.5

    if not student_city and not home_city and not preferred and not acceptable:
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

    if preference == "Interview preferred" or (
        preference and preference.startswith("Interview preferred:")
    ):
        if requirement == "Required":
            return 1.0
        if requirement == "Not required":
            return 0.75
        return 0.55

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


MISSING_SKILLS_MAX = 8


def _student_skill_set(profile: ParsedProfile) -> set[str]:
    return {
        skill.strip().lower()
        for skill in (profile.skills or [])
        if skill and skill.strip().lower() not in SKILL_NOISE_TOKENS
    }


def _student_covers_skill(student: set[str], opportunity_skill: str) -> bool:
    """Return True when the student already has this opportunity skill.

    Used for missing-skills lists only. Exact matches, taxonomy-style aliases,
    and clear prefix overlap (e.g. ``cybersecurity`` -> ``cybersecurity fundamentals``)
    are treated as covered. Does not alter rubric scoring.
    """
    norm = str(opportunity_skill).strip().lower()
    if not norm or norm in SKILL_NOISE_TOKENS:
        return True
    if norm in student:
        return True

    opp_forms = _skill_compare_forms(norm)
    for token in student:
        if opp_forms & _skill_compare_forms(token):
            return True
        if norm in _STUDENT_SKILL_SATISFIES.get(token, frozenset()):
            return True
        if len(token) >= 5 and token in norm:
            return True
    return False


def _append_missing(
    candidates: Iterable[str],
    student: set[str],
    seen: set[str],
    out: List[str],
    max_count: int,
) -> bool:
    """Append non-redundant missing skills to ``out``.

    Returns ``True`` when ``out`` reached ``max_count`` and the caller can
    stop.
    """
    for raw in candidates:
        if len(out) >= max_count:
            return True
        if not raw:
            continue
        cleaned = str(raw).strip()
        normalized = cleaned.lower()
        if not normalized or normalized in SKILL_NOISE_TOKENS:
            continue
        if normalized in seen or _student_covers_skill(student, cleaned):
            continue
        seen.add(normalized)
        out.append(cleaned)
    return len(out) >= max_count


def compute_missing_required_skills(
    profile: ParsedProfile,
    opportunity: Opportunity,
    *,
    max_count: int = MISSING_SKILLS_MAX,
) -> List[str]:
    """ML-2B.1: missing skills the role's profile lists as **required**.

    Only role-profile required skills are considered; explicit
    ``skills_list`` entries are handled by :func:`compute_missing_skills`.
    """
    student = _student_skill_set(profile)
    signals = enrich_opportunity_signals(opportunity)
    seen: set[str] = set()
    out: List[str] = []
    _append_missing(signals.get("required_skills", []) or [], student, seen, out, max_count)  # type: ignore[arg-type]
    return out


def compute_missing_preferred_skills(
    profile: ParsedProfile,
    opportunity: Opportunity,
    *,
    max_count: int = MISSING_SKILLS_MAX,
) -> List[str]:
    """ML-2B.1: missing skills the role's profile lists as **preferred**.

    Preferred skills that are already in the required list (or that the
    student already has) are filtered out.
    """
    student = _student_skill_set(profile)
    signals = enrich_opportunity_signals(opportunity)
    required_lower = {str(s).lower() for s in (signals.get("required_skills") or [])}  # type: ignore[arg-type]
    seen: set[str] = set(required_lower)
    out: List[str] = []
    _append_missing(signals.get("preferred_skills", []) or [], student, seen, out, max_count)  # type: ignore[arg-type]
    return out


def compute_missing_skills(
    profile: ParsedProfile,
    opportunity: Opportunity,
    *,
    max_count: int = MISSING_SKILLS_MAX,
) -> List[str]:
    """Return opportunity skills the student does not appear to have.

    SCORE-AUDIT-2 ordering:

    1. **Explicit** ``skills_list`` gaps on the opportunity.
    2. **Missing required** skills from interest-filtered role profiles.
    3. **Missing preferred** skills from those role profiles.
    4. **Bucket inferred** skills only when explicit and role lists are empty.

    Backend / software role-profile skills are omitted for cybersecurity-focused
    students so generic ``python`` / ``apis`` / ``git`` do not displace SOC gaps.
    """
    student = _student_skill_set(profile)
    explicit = _clean_explicit_opportunity_skills(opportunity)
    required, preferred = _role_profile_skill_lists(opportunity, profile)

    seen: set[str] = set()
    out: List[str] = []

    if _append_missing(explicit, student, seen, out, max_count):
        return out
    if _append_missing(required, student, seen, out, max_count):
        return out
    if _append_missing(preferred, student, seen, out, max_count):
        return out

    if not explicit and not required and not preferred:
        inferred = enrich_opportunity_signals(opportunity).get("inferred_skills", []) or []
        _append_missing(inferred, student, seen, out, max_count)  # type: ignore[arg-type]
    return out
