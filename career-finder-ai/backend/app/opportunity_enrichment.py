"""
opportunity_enrichment.py — ML-2B / ML-2B.1 runtime enrichment for opportunities.

When the source dataset (Opportunities_Clean.xlsx) has weak or missing role /
skill metadata, this module infers *weak* secondary signals from the company
name, title, requirements, declared skills list, and role cluster.

Design constraints
==================

- **Runtime only.** This is pure inference. No file writes, no DB. The source
  Excel is not mutated.
- **Secondary signal only.** Anything returned here must be treated by the
  rubric as a partial-weight bump, never as authoritative. Explicit
  ``skills_list`` and ``role_cluster`` on the opportunity still win.
- **Pure functions.** The helpers below take a single ``Opportunity`` and
  return a plain dict. They are safe to call from tests.

Returned shape from :func:`enrich_opportunity_signals`::

    {
        "role_cluster":        Optional[str],
        "inferred_interests":  List[str],   # taxonomy interest labels
        "inferred_skills":     List[str],   # lowercase skill tokens
        "required_skills":     List[str],   # ML-2B.1: from ROLE_SKILL_PROFILES
        "preferred_skills":    List[str],   # ML-2B.1: from ROLE_SKILL_PROFILES
    }

These fields are layered onto the existing opportunity at scoring time in
:mod:`app.rubric`. ``required_skills`` and ``preferred_skills`` are
distinguished so the rubric can give required hits a stronger weight than
preferred hits without disturbing the rubric's overall weights.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from app.schemas import Opportunity


# ---------------------------------------------------------------------------
# Bucket definitions
# ---------------------------------------------------------------------------
#
# Each bucket has:
#   - ``triggers``: lowercase phrases. A bucket fires if any trigger is
#     present in the opportunity's combined text.
#   - ``role_cluster``: a preferred role-cluster label for this bucket.
#     ``enrich_opportunity_signals`` only sets ``role_cluster`` when the
#     opportunity does not already declare one.
#   - ``interests``: canonical taxonomy interest labels these opportunities
#     should weakly match against.
#   - ``skills``: lowercase skill tokens these opportunities should be
#     treated as referencing as a *weak* signal.
#
# The order of buckets is the priority order — telecom/network first,
# then cyber/security, then bank/fintech, AI/data, software/backend.

_TELECOM_TRIGGERS = (
    "stc",
    "mobily",
    "zain",
    "telecom",
    "telecommunication",
    "telecommunications",
    "network operator",
    "isp",
    "5g",
    "lte",
)
_TELECOM_INFRA_TRIGGERS = (
    "network",
    "networking",
    "infrastructure",
    "datacenter",
    "data center",
    "noc",
    "core network",
)

_CYBER_TRIGGERS = (
    "cybersecurity",
    "cyber security",
    "infosec",
    "soc",
    "siem",
    "penetration",
    "pentest",
    "vulnerability",
    "incident response",
    "ethical hacking",
    "security operations",
    "blue team",
    "red team",
    "endpoint security",
    "firewall",
    "ids/ips",
)

_BANK_TRIGGERS = (
    "bank",
    "banking",
    "fintech",
    "financial technology",
    "al rajhi",
    "alrajhi",
    "snb",
    "saudi national bank",
    "riyad bank",
    "samba",
    "anb",
    "alinma",
    "stcpay",
    "tabby",
    "tamara",
    "payments",
)

_AI_DATA_TRIGGERS = (
    "artificial intelligence",
    " ai ",
    "ai/",
    "ai-",
    "ai engineer",
    "machine learning",
    " ml ",
    "deep learning",
    "data scientist",
    "data science",
    "data engineering",
    "data engineer",
    "analytics",
    "wakeb",
    "sdaia",
    "nlp",
    "natural language",
    "computer vision",
    "etl",
    "data pipeline",
    "data warehouse",
)

_SOFTWARE_TRIGGERS = (
    "software engineer",
    "software engineering",
    "software development",
    "backend",
    "back end",
    "back-end",
    "frontend",
    "front end",
    "front-end",
    "full stack",
    "fullstack",
    "web development",
    "api",
    " apis ",
    "developer",
    "mobile development",
)


# Canonical bucket payloads. Keep these lists short and high-signal.
#
# Each bucket can also declare ``skill_profile_keys`` — the keys into
# :data:`ROLE_SKILL_PROFILES` that should fire when this bucket matches.
# Multiple buckets can fire at once; their required / preferred skill lists
# are unioned (case-insensitive, order-preserving).
_BUCKETS: List[Dict[str, object]] = [
    {
        "name": "telecom_network",
        "triggers": _TELECOM_TRIGGERS + _TELECOM_INFRA_TRIGGERS,
        "role_cluster": "Network Security",
        "interests": [
            "Cybersecurity",
            "Cloud / DevOps",
        ],
        "skills": [
            "networking",
            "network security",
            "cybersecurity",
            "linux",
            "cloud",
        ],
        "skill_profile_keys": ["Network Security", "Cybersecurity"],
    },
    {
        "name": "cybersecurity",
        "triggers": _CYBER_TRIGGERS,
        "role_cluster": "Cybersecurity",
        "interests": [
            "Cybersecurity",
        ],
        "skills": [
            "cybersecurity",
            "soc",
            "siem",
            "network security",
            "penetration testing",
            "linux",
            "incident response",
            "vulnerability assessment",
            "networking",
        ],
        "skill_profile_keys": ["Cybersecurity", "Network Security"],
    },
    {
        "name": "bank_fintech",
        "triggers": _BANK_TRIGGERS,
        "role_cluster": "Backend Engineering",
        "interests": [
            "FinTech",
            "Software Development",
            "Data Science",
            "Cybersecurity",
        ],
        "skills": [
            "sql",
            "python",
            "api",
            "cybersecurity",
            "data analysis",
        ],
        "skill_profile_keys": ["Backend Engineering"],
    },
    {
        "name": "ai_data",
        "triggers": _AI_DATA_TRIGGERS,
        "role_cluster": "AI / Machine Learning",
        "interests": [
            "Data Science",
            "Data Engineering",
        ],
        "skills": [
            "python",
            "sql",
            "machine learning",
            "data analysis",
        ],
        "skill_profile_keys": ["AI / Machine Learning", "Data Engineering"],
    },
    {
        "name": "software",
        "triggers": _SOFTWARE_TRIGGERS,
        "role_cluster": "Software Engineering",
        "interests": [
            "Software Development",
        ],
        "skills": [
            "python",
            "api",
            "sql",
            "git",
        ],
        "skill_profile_keys": ["Backend Engineering", "Frontend Engineering"],
    },
]


# ---------------------------------------------------------------------------
# ROLE_SKILL_PROFILES  (ML-2B.1)
# ---------------------------------------------------------------------------
#
# Simple, course-demo role skill profiles. Each profile describes the
# canonical required / preferred technical skills for a role cluster. The
# rubric uses these to:
#
#   * Score "inferred required skill" matches at weight 0.7.
#   * Score "inferred preferred skill" matches at weight 0.4.
#   * Order ``missing_skills`` so required gaps appear before preferred gaps.
#
# Required = a student with this role goal needs these to apply at all.
# Preferred = these are the strong differentiators (nice-to-have).
#
# All entries are kept lowercase for case-insensitive matching against the
# parser's ``SKILL_KEYWORDS`` and the opportunity's declared skills_list.
ROLE_SKILL_PROFILES: Dict[str, Dict[str, List[str]]] = {
    "Cybersecurity": {
        "required": ["linux", "networking", "cybersecurity fundamentals"],
        "preferred": [
            "siem",
            "soc",
            "penetration testing",
            "incident response",
            "vulnerability assessment",
        ],
    },
    "Network Security": {
        "required": ["networking", "linux", "security fundamentals"],
        "preferred": ["firewall", "siem", "incident response", "network monitoring"],
    },
    "Cloud / DevOps": {
        "required": ["linux", "docker", "git"],
        "preferred": ["kubernetes", "ci/cd", "aws", "azure", "terraform", "cloud"],
    },
    "Backend Engineering": {
        "required": ["python", "apis", "sql", "git"],
        "preferred": ["docker", "testing", "cloud", "rest apis"],
    },
    "Frontend Engineering": {
        "required": ["javascript", "html", "css", "react"],
        "preferred": ["typescript", "ui testing", "apis"],
    },
    "Data Engineering": {
        "required": ["sql", "python", "etl"],
        "preferred": ["pipelines", "spark", "data warehouse", "bi"],
    },
    "Data Science": {
        "required": ["python", "sql", "data analysis"],
        "preferred": ["machine learning", "statistics", "pandas", "visualization"],
    },
    "AI / Machine Learning": {
        "required": ["python", "machine learning", "data analysis"],
        "preferred": ["nlp", "llm", "model training", "tensorflow", "pytorch"],
    },
    "QA / Testing": {
        "required": ["testing", "documentation", "problem solving"],
        "preferred": ["test automation", "qa", "selenium", "api testing"],
    },
    "General Computing": {
        "required": ["problem solving", "basic programming"],
        "preferred": ["git", "sql", "communication"],
    },
}


# Substring → profile key. Order matters: more specific phrases first so
# that e.g. ``"network security"`` resolves to ``Network Security`` rather
# than ``Cybersecurity``.
_ROLE_CLUSTER_TO_PROFILE_KEY: List[tuple[str, str]] = [
    ("network security", "Network Security"),
    ("network engineer", "Network Security"),
    ("networking", "Network Security"),
    ("soc analyst", "Cybersecurity"),
    ("soc operations", "Cybersecurity"),
    ("penetration", "Cybersecurity"),
    ("cybersecurity", "Cybersecurity"),
    ("cyber security", "Cybersecurity"),
    ("information security", "Cybersecurity"),
    ("infosec", "Cybersecurity"),
    ("devops", "Cloud / DevOps"),
    ("cloud / devops", "Cloud / DevOps"),
    ("cloud engineering", "Cloud / DevOps"),
    ("cloud engineer", "Cloud / DevOps"),
    ("site reliability", "Cloud / DevOps"),
    ("platform engineering", "Cloud / DevOps"),
    ("frontend", "Frontend Engineering"),
    ("front-end", "Frontend Engineering"),
    ("front end", "Frontend Engineering"),
    ("ui ", "Frontend Engineering"),
    ("backend", "Backend Engineering"),
    ("back-end", "Backend Engineering"),
    ("back end", "Backend Engineering"),
    ("full stack", "Backend Engineering"),
    ("data engineering", "Data Engineering"),
    ("data engineer", "Data Engineering"),
    ("etl", "Data Engineering"),
    ("data pipeline", "Data Engineering"),
    ("data science", "Data Science"),
    ("data scientist", "Data Science"),
    ("data analytics", "Data Science"),
    ("data analyst", "Data Science"),
    ("ai / machine learning", "AI / Machine Learning"),
    ("ai engineering", "AI / Machine Learning"),
    ("ai engineer", "AI / Machine Learning"),
    ("machine learning", "AI / Machine Learning"),
    ("artificial intelligence", "AI / Machine Learning"),
    ("nlp", "AI / Machine Learning"),
    ("qa / testing", "QA / Testing"),
    ("qa engineer", "QA / Testing"),
    ("quality assurance", "QA / Testing"),
    ("test automation", "QA / Testing"),
    ("software engineering", "Backend Engineering"),
    ("software engineer", "Backend Engineering"),
    ("software developer", "Backend Engineering"),
]


def _skill_profile_key_for_label(label: Optional[str]) -> Optional[str]:
    """Map an arbitrary role-cluster label to a :data:`ROLE_SKILL_PROFILES` key.

    Returns ``None`` when no mapping is found. Callers can decide whether to
    fall back to ``"General Computing"`` or to skip enrichment.
    """
    if not label:
        return None
    text = label.lower().strip()
    if not text:
        return None
    for needle, key in _ROLE_CLUSTER_TO_PROFILE_KEY:
        if needle in text:
            return key
    return None


def _skill_profile_keys_from_opportunity(opp: Opportunity) -> List[str]:
    """Return every :data:`ROLE_SKILL_PROFILES` key whose needle appears in
    the opportunity's combined text (company + title + role_cluster +
    requirements + skills_list).

    Used as a broader fallback so that opportunities whose role signal
    only appears in the requirements / skills_list (e.g. a Deloitte
    listing whose skills_list says ``"Networking Fundamentals"``) still
    pick up a role profile. Order = declaration order of
    ``_ROLE_CLUSTER_TO_PROFILE_KEY`` (most specific first).
    """
    blob = _combined_text(opp)
    out: List[str] = []
    for needle, key in _ROLE_CLUSTER_TO_PROFILE_KEY:
        if needle in blob and key not in out:
            out.append(key)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _combined_text(opp: Opportunity) -> str:
    """Build a single lowercase text blob used for trigger detection.

    Pads with spaces on each side so the matcher can still find short tokens
    like ``" ai "`` without false-positives in the middle of other words.
    """
    parts = [
        opp.company or "",
        opp.title or "",
        opp.role_cluster or "",
        opp.requirements or "",
        " ".join(opp.skills_list or []),
    ]
    blob = " ".join(parts).lower()
    return f" {blob} "


def _matches_any(text: str, triggers: Iterable[str]) -> bool:
    for trigger in triggers:
        if trigger in text:
            return True
    return False


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for value in values:
        key = value.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fired_role_skill_profile_keys(opportunity: Opportunity) -> List[str]:
    """Return ordered :data:`ROLE_SKILL_PROFILES` keys activated for an opportunity.

    Combines bucket ``skill_profile_keys`` with needles found in the opportunity
    text (title, requirements, skills_list, etc.). Used by the rubric to layer
    role-cluster skills before company-level bucket fallbacks.
    """
    text = _combined_text(opportunity)
    fired_profile_keys: List[str] = []

    for bucket in _BUCKETS:
        if not _matches_any(text, bucket["triggers"]):  # type: ignore[arg-type]
            continue
        for key in bucket.get("skill_profile_keys", []) or []:  # type: ignore[union-attr]
            if isinstance(key, str) and key not in fired_profile_keys:
                fired_profile_keys.append(key)

    for key in _skill_profile_keys_from_opportunity(opportunity):
        if key not in fired_profile_keys:
            fired_profile_keys.append(key)

    return fired_profile_keys


def enrich_opportunity_signals(opportunity: Opportunity) -> Dict[str, object]:
    """Return weak inferred signals for an opportunity.

    Returns
    -------
    dict
        ``{"role_cluster": Optional[str], "inferred_interests": List[str],
        "inferred_skills": List[str], "required_skills": List[str],
        "preferred_skills": List[str]}``.

        - ``role_cluster`` is only set when the opportunity does not already
          declare one (i.e. ``opportunity.role_cluster`` is empty).
        - ``inferred_interests`` are canonical taxonomy labels
          (e.g. ``"Cybersecurity"``, ``"Cloud / DevOps"``,
          ``"Data Science"``).
        - ``inferred_skills`` are lowercase skill tokens that align with the
          parser's ``SKILL_KEYWORDS`` vocabulary where possible.
        - ``required_skills`` / ``preferred_skills`` (ML-2B.1) come from
          :data:`ROLE_SKILL_PROFILES`. They are *secondary* — explicit
          ``opportunity.skills_list`` always wins. ``preferred_skills``
          never overlaps with ``required_skills`` (required wins on dedupe).

    Notes
    -----
    Returned signals are *weak*. The rubric must treat them as secondary —
    explicit ``skills_list``, ``role_cluster``, and title/requirements
    references on the opportunity always take priority.
    """
    text = _combined_text(opportunity)

    interests: List[str] = []
    skills: List[str] = []
    inferred_role_cluster: Optional[str] = None

    for bucket in _BUCKETS:
        triggers = bucket["triggers"]  # type: ignore[index]
        if not _matches_any(text, triggers):  # type: ignore[arg-type]
            continue

        interests.extend(bucket["interests"])  # type: ignore[arg-type]
        skills.extend(bucket["skills"])        # type: ignore[arg-type]

        if inferred_role_cluster is None:
            inferred_role_cluster = str(bucket["role_cluster"])

    fired_profile_keys = fired_role_skill_profile_keys(opportunity)

    # Aggregate required / preferred from every fired profile.
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    for key in fired_profile_keys:
        profile = ROLE_SKILL_PROFILES.get(key)
        if not profile:
            continue
        required_skills.extend(profile.get("required", []))
        preferred_skills.extend(profile.get("preferred", []))

    required_skills = _dedupe_preserve_order(required_skills)
    required_lower = {s.lower() for s in required_skills}
    # Preferred should not duplicate anything that is already required.
    preferred_skills = [
        s
        for s in _dedupe_preserve_order(preferred_skills)
        if s.lower() not in required_lower
    ]

    final_role_cluster: Optional[str] = None
    if not (opportunity.role_cluster or "").strip() and inferred_role_cluster:
        final_role_cluster = inferred_role_cluster

    return {
        "role_cluster": final_role_cluster,
        "inferred_interests": _dedupe_preserve_order(interests),
        "inferred_skills": _dedupe_preserve_order(skills),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
    }


def enrich_opportunity_skill_pool(opportunity: Opportunity) -> List[str]:
    """Combined explicit + inferred skill pool, lowercase, deduplicated.

    Explicit ``skills_list`` entries appear first so explicit > inferred when
    callers do a first-match scan.
    """
    explicit = [s for s in (opportunity.skills_list or []) if s]
    inferred = enrich_opportunity_signals(opportunity)["inferred_skills"]  # type: ignore[index]
    return _dedupe_preserve_order(list(explicit) + list(inferred))  # type: ignore[arg-type]
