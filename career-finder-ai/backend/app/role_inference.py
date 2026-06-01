"""
role_inference.py – Role-family inference for CareerFinder.ai (Sprint-2).

Infers which of the 14 role families (see role_families.py) best match a
student's parsed profile, and generates guided questions when the profile is
ambiguous or the user has declared they are unsure.

Public API
----------
    infer_role_families(profile, message="") -> RoleFamilyInferenceResult
    detect_discovery_mode(message, profile) -> bool
    format_role_directions(result) -> str   (display helper)

No I/O, no ML, no external dependencies beyond the app package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from app.role_families import (
    DISCOVERY_QUESTION,
    FOUNDATIONAL_WEIGHT,
    DIFFERENTIATING_WEIGHT,
    MAX_FAMILIES_RETURNED,
    MIN_CONFIDENCE,
    ROLE_FAMILIES,
    SIGNATURE_WEIGHT,
    get_transition_paths,
    is_discovery_phrase,
)
from app.schemas import ParsedProfile


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RoleFamilyMatch:
    """Confidence result for a single role family."""

    role_family: str
    confidence: float          # 0.0–1.0
    evidence: List[str]        # signals found (skills, interest, major)
    missing_signals: List[str] # key skills not present
    explanation: str


@dataclass
class RoleFamilyInferenceResult:
    """Full inference result for a student profile."""

    matches: List[RoleFamilyMatch]
    guided_question: Optional[str]
    is_ambiguous: bool
    current_strength_family: Optional[str]   # top family from skills alone
    target_interest_family: Optional[str]    # top family from interest alone
    transition_paths: List[str]
    discovery_mode: bool                     # user said "idk" / "not sure"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _skill_set(profile: ParsedProfile) -> Set[str]:
    """Normalised set of student skill tokens."""
    return {s.strip().lower() for s in (profile.skills or []) if s.strip()}


def _qual_set(profile: ParsedProfile) -> Set[str]:
    """Normalised qualification tokens (certs, GPA excluded)."""
    tokens: Set[str] = set()
    for q in profile.qualifications or []:
        q = q.strip().lower()
        if q and not q.startswith("gpa"):
            tokens.add(q)
    return tokens


def _all_tokens(profile: ParsedProfile) -> Set[str]:
    """Combined skill + qualification tokens."""
    return _skill_set(profile) | _qual_set(profile)


def _score_skills_for_family(
    tokens: Set[str],
    family_def,
) -> tuple[float, List[str]]:
    """Return (skill_raw_score, evidence_list) for one role family.

    Uses weight constants: signature > differentiating > foundational.
    Avoids double-counting — each token can only trigger one weight level.
    """
    evidence: List[str] = []
    raw = 0.0
    counted: Set[str] = set()

    for skill in family_def.signature_skills:
        if skill in tokens and skill not in counted:
            raw += SIGNATURE_WEIGHT
            evidence.append(skill)
            counted.add(skill)

    for skill in family_def.differentiating_skills:
        if skill in tokens and skill not in counted:
            raw += DIFFERENTIATING_WEIGHT
            evidence.append(skill)
            counted.add(skill)

    for skill in family_def.foundational_skills:
        if skill in tokens and skill not in counted:
            raw += FOUNDATIONAL_WEIGHT
            evidence.append(skill)
            counted.add(skill)

    return raw, evidence


def _interest_match(profile: ParsedProfile, family_name: str) -> tuple[float, List[str]]:
    """Return (bonus, evidence) for interest alignment."""
    family_def = ROLE_FAMILIES[family_name]
    interest = (profile.interest or "").strip()
    if not interest:
        return 0.0, []

    if interest in family_def.related_interests:
        return 0.5, [f"{interest} interest"]

    # Partial / alternative interest label overlap (e.g. "Artificial Intelligence"
    # not listed but "Data Science" is for DS/ML family)
    interest_lower = interest.lower()
    for rel in family_def.related_interests:
        if interest_lower in rel.lower() or rel.lower() in interest_lower:
            return 0.3, [f"{interest} interest (partial)"]

    return 0.0, []


def _preferred_role_match(profile: ParsedProfile, family_name: str) -> tuple[float, List[str]]:
    """Return (bonus, evidence) for preferred_roles overlap."""
    family_def = ROLE_FAMILIES[family_name]
    if not profile.preferred_roles:
        return 0.0, []

    role_titles_lower = [r.lower() for r in family_def.role_titles]
    keywords_lower = [k.lower() for k in family_def.keywords]

    for role in profile.preferred_roles:
        role_lower = role.strip().lower()
        if role_lower in role_titles_lower:
            return 0.3, [f"{role} role preference"]
        for kw in keywords_lower:
            if kw in role_lower or role_lower in kw:
                return 0.2, [f"{role} role preference"]

    return 0.0, []


def _major_match(profile: ParsedProfile, family_name: str) -> tuple[float, List[str]]:
    """Return (bonus, evidence) for major alignment."""
    family_def = ROLE_FAMILIES[family_name]
    if not profile.major:
        return 0.0, []
    if profile.major in family_def.related_majors:
        return 0.12, [f"{profile.major} major"]
    return 0.0, []


def _top_skill_family(
    tokens: Set[str],
    skill_scores: Dict[str, float],
) -> Optional[str]:
    """Return the name of the family with the highest pure-skill score."""
    if not skill_scores:
        return None
    return max(skill_scores, key=lambda k: skill_scores[k])


def _top_interest_family(profile: ParsedProfile) -> Optional[str]:
    """Return the family most aligned with the student's stated interest."""
    if not profile.interest:
        return None
    best_family: Optional[str] = None
    best_score = 0.0
    for family_name in ROLE_FAMILIES:
        bonus, _ = _interest_match(profile, family_name)
        if bonus > best_score:
            best_score = bonus
            best_family = family_name
    return best_family if best_score > 0.0 else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_discovery_mode(message: str, profile: ParsedProfile) -> bool:
    """Return True when the user is in guided-discovery mode.

    Triggers when:
    - The raw message contains a known "I don't know" phrase, OR
    - The profile has no skills AND no interest AND no preferred roles
      (completely empty signal set).
    """
    if is_discovery_phrase(message):
        return True
    has_signals = (
        bool(profile.skills)
        or bool(profile.interest)
        or bool(profile.preferred_roles)
        or bool(profile.major)
    )
    return not has_signals


def infer_role_families(
    profile: ParsedProfile,
    message: str = "",
) -> RoleFamilyInferenceResult:
    """Infer the most likely role families for a student profile.

    Parameters
    ----------
    profile : ParsedProfile
        Parsed student profile from the parser.
    message : str, optional
        Original normalised student message (used for discovery-mode detection).

    Returns
    -------
    RoleFamilyInferenceResult
        Contains sorted matches (highest confidence first), guided question
        when ambiguous, transition info when skill/interest directions diverge.
    """
    tokens = _all_tokens(profile)
    discovery = detect_discovery_mode(message, profile)

    scores: Dict[str, float] = {}
    evidence_map: Dict[str, List[str]] = {}
    skill_only_scores: Dict[str, float] = {}

    for family_name, family_def in ROLE_FAMILIES.items():
        skill_raw, skill_evidence = _score_skills_for_family(tokens, family_def)
        interest_bonus, interest_evidence = _interest_match(profile, family_name)
        preferred_bonus, preferred_evidence = _preferred_role_match(profile, family_name)
        major_bonus, major_evidence = _major_match(profile, family_name)

        confidence = min(
            skill_raw + interest_bonus + preferred_bonus + major_bonus,
            1.0,
        )
        evidence = skill_evidence + interest_evidence + preferred_evidence + major_evidence

        skill_only_scores[family_name] = skill_raw
        if confidence >= MIN_CONFIDENCE:
            scores[family_name] = confidence
            evidence_map[family_name] = evidence

    # Sort descending by confidence, take top N
    sorted_items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    sorted_items = sorted_items[:MAX_FAMILIES_RETURNED]

    matches: List[RoleFamilyMatch] = []
    for family_name, confidence in sorted_items:
        family_def = ROLE_FAMILIES[family_name]
        # Missing signals = signature skills the student does NOT have
        missing = [
            s for s in family_def.signature_skills
            if s not in tokens
        ][:3]
        matches.append(
            RoleFamilyMatch(
                role_family=family_name,
                confidence=round(confidence, 2),
                evidence=evidence_map.get(family_name, []),
                missing_signals=missing,
                explanation=family_def.explanation,
            )
        )

    # Ambiguity: no clear leader (top < 0.3) or no matches at all
    is_ambiguous = (
        not matches
        or matches[0].confidence < 0.3
        or (len(matches) >= 2 and abs(matches[0].confidence - matches[1].confidence) < 0.1
            and matches[0].confidence < 0.5)
    )

    # Transition detection: top skill family ≠ top interest family
    top_skill = _top_skill_family(tokens, skill_only_scores)
    top_interest = _top_interest_family(profile)

    transition_paths: List[str] = []
    if (
        top_skill
        and top_interest
        and top_skill != top_interest
        # Only flag a transition when skills give a meaningful signal
        and skill_only_scores.get(top_skill, 0.0) >= DIFFERENTIATING_WEIGHT
    ):
        transition_paths = get_transition_paths(top_skill, top_interest)
    else:
        # Reset to None if no real divergence
        top_skill = None
        top_interest = None

    # Guided question
    guided_question: Optional[str] = None
    if discovery:
        guided_question = DISCOVERY_QUESTION
    elif is_ambiguous and matches:
        # Ask the first suggested question for the top candidate family
        top_def = ROLE_FAMILIES.get(matches[0].role_family)
        if top_def and top_def.suggested_questions:
            guided_question = top_def.suggested_questions[0]
    elif is_ambiguous:
        guided_question = DISCOVERY_QUESTION
    elif top_skill and top_interest and top_skill != top_interest:
        # Conflict guidance
        guided_question = (
            f"Your current skills point toward {top_skill}, but your interest "
            f"points toward {top_interest}. "
            "Do you want recommendations based on your current strengths, "
            "or your target direction?"
        )

    return RoleFamilyInferenceResult(
        matches=matches,
        guided_question=guided_question,
        is_ambiguous=is_ambiguous,
        current_strength_family=top_skill,
        target_interest_family=top_interest,
        transition_paths=transition_paths,
        discovery_mode=discovery,
    )


# ---------------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------------

def format_role_directions(result: RoleFamilyInferenceResult) -> str:
    """Return a compact display string for role directions.

    Suitable for the terminal CLI and assistant reply.
    """
    if result.discovery_mode:
        lines = ["Role direction: not yet determined."]
        if result.guided_question:
            lines.append("")
            lines.append(result.guided_question)
        return "\n".join(lines)

    lines: List[str] = []

    if result.matches:
        lines.append("Possible role directions:")
        for i, m in enumerate(result.matches, start=1):
            pct = int(round(m.confidence * 100))
            evidence_str = (
                ", ".join(m.evidence[:4]) if m.evidence else "general profile fit"
            )
            lines.append(f"  {i}. {m.role_family} — {pct}%")
            lines.append(f"     Evidence: {evidence_str}")

    if result.current_strength_family and result.target_interest_family:
        lines.append("")
        lines.append(
            f"Note: Your current skills are strongest in "
            f"{result.current_strength_family}, "
            f"but your stated interest is {result.target_interest_family}."
        )
        if result.transition_paths:
            lines.append("Possible transition paths:")
            for path in result.transition_paths[:3]:
                lines.append(f"  • {path}")

    if result.guided_question:
        lines.append("")
        lines.append(result.guided_question)

    return "\n".join(lines) if lines else ""
