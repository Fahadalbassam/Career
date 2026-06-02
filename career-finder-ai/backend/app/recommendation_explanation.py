"""
recommendation_explanation.py – Human-readable recommendation explanations.

Sprint-3: compact /details sections, honest fit language, and concrete
next-best-action copy. Does not alter rubric scores or ranking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.rubric import FLEXIBLE_CITIES, TARGET_WEIGHTS, normalize_text

FIT_STRONG = 0.85
FIT_PARTIAL = 0.55
FIT_WEAK = 0.35
FIT_LIMITING = 0.70

def _fit_strength(score: float) -> str:
    if score >= FIT_STRONG:
        return "strong"
    if score >= FIT_PARTIAL:
        return "partial"
    if score >= FIT_WEAK:
        return "weak"
    return "weak"


def describe_location_fit(
    score: float,
    profile: Optional[Dict[str, Any]],
    rec: Dict[str, Any],
) -> str:
    opp_city = normalize_text(rec.get("city"))
    if not opp_city or opp_city == "not stated":
        return "not stated"
    if score >= 0.95:
        return "exact"
    if score >= 0.8:
        return "acceptable"
    if score >= 0.65:
        return "regional"
    if score >= 0.45 or opp_city in FLEXIBLE_CITIES:
        return "broad"
    if score <= 0.05:
        return "no match"
    return "partial" if score >= FIT_PARTIAL else "broad"


def describe_program_type_fit(
    score: float,
    profile: Optional[Dict[str, Any]],
    rec: Dict[str, Any],
) -> str:
    opp_type = normalize_text(rec.get("program_type"))
    if not opp_type or opp_type == "not stated":
        return "not stated"
    if score >= 0.95:
        return "exact"
    if score >= 0.85:
        return "compatible"
    if score >= FIT_PARTIAL:
        return "partial"
    return "no match"


def describe_work_mode_fit(
    score: float,
    profile: Optional[Dict[str, Any]],
    rec: Dict[str, Any],
) -> str:
    opp_mode = normalize_text(rec.get("work_mode"))
    if not opp_mode or opp_mode == "not stated":
        return "not stated"
    if score >= 0.95:
        return "exact"
    if score >= 0.65:
        return "compatible"
    if score >= FIT_PARTIAL:
        return "partial"
    return "no match"


def describe_interview_fit(
    score: float,
    profile: Optional[Dict[str, Any]],
    rec: Dict[str, Any],
) -> str:
    requirement = rec.get("interview_required") or "Not stated"
    if requirement == "Not stated":
        return "not stated"
    pref = (profile or {}).get("interview_preference")
    if requirement == "Required":
        if pref and score >= 0.75:
            return "matches preference"
        return "required (per source)"
    if requirement == "Not required":
        if pref and score >= 0.75:
            return "matches preference"
        return "not required (per source)"
    if pref and score <= 0.3:
        return "mismatch"
    return "not stated"


def build_why_matched_lines(
    rec: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[str]:
    lines: List[str] = []
    breakdown = rec.get("score_breakdown") or {}
    profile = profile or {}

    major_score = breakdown.get("major_fit_score")
    major = profile.get("major")
    if major_score is not None and major:
        strength = _fit_strength(float(major_score))
        if float(major_score) >= 0.95:
            lines.append(f"This appears to fit your major ({major}): {strength} match.")
        elif float(major_score) >= 0.55:
            lines.append(f"Your major ({major}) is a related fit: {strength} match.")
        elif float(major_score) >= 0.25:
            lines.append(f"Major fit is {strength}; the listing may accept broader majors.")
        else:
            lines.append(f"Major fit is weak for {major} on this listing.")

    role_score = breakdown.get("role_interest_score")
    interest = profile.get("interest")
    preferred_roles = profile.get("preferred_roles") or []
    if role_score is not None:
        strength = _fit_strength(float(role_score))
        if interest and float(role_score) >= FIT_PARTIAL:
            lines.append(f"Interest/role direction ({interest}) shows a {strength} fit.")
        elif preferred_roles and float(role_score) >= FIT_PARTIAL:
            lines.append(f"Preferred role ({preferred_roles[0]}) shows a {strength} fit.")
        elif float(role_score) < FIT_PARTIAL and (interest or preferred_roles):
            lines.append("Role/interest alignment is limited on this listing.")

    for reason in rec.get("why_recommended") or []:
        if reason.startswith("Role-family match:"):
            lines.append(reason.replace("Role-family match:", "Role-family evidence:"))
            break

    matched = rec.get("skills_matched") or []
    if matched:
        shown = ", ".join(matched[:8])
        extra = len(matched) - 8
        if extra > 0:
            shown += f" (+{extra} more)"
        lines.append(f"Skill overlap: {shown}.")
    elif float(breakdown.get("skill_match_score", 0)) >= FIT_PARTIAL:
        lines.append("Some skill overlap appears in the listing text.")

    loc_label = describe_location_fit(
        float(breakdown.get("city_match_score", 0)),
        profile,
        rec,
    )
    student_city = profile.get("city") or ""
    opp_city = rec.get("city") or "Not stated"
    if loc_label == "exact":
        lines.append(f"Location: exact city match ({opp_city}).")
    elif loc_label == "regional":
        lines.append(
            f"Location: regional match ({opp_city} vs your {student_city or 'area'}) — "
            "not an exact city match."
        )
    elif loc_label == "broad":
        lines.append(
            f"This is a broad location match ({opp_city}), not an exact city match."
        )
    elif loc_label == "not stated":
        lines.append("The source does not state a specific city for this listing.")
    elif loc_label == "acceptable":
        lines.append(f"Location: acceptable alternate city ({opp_city}).")
    elif loc_label == "partial":
        lines.append(f"The opportunity partially matches your location preference ({opp_city}).")

    prog_label = describe_program_type_fit(
        float(breakdown.get("program_type_score", 0)),
        profile,
        rec,
    )
    stu_prog = profile.get("program_type") or ""
    opp_prog = rec.get("program_type") or "Not stated"
    if prog_label == "exact":
        lines.append(f"Program type matches ({opp_prog}).")
    elif prog_label == "compatible":
        lines.append(f"Program type is compatible ({opp_prog} vs {stu_prog or 'your preference'}).")
    elif prog_label == "partial":
        lines.append(f"Program type is only a partial match ({opp_prog}).")
    elif prog_label == "not stated":
        lines.append("The source does not state the program type clearly.")

    wm_label = describe_work_mode_fit(
        float(breakdown.get("work_mode_score", 0)),
        profile,
        rec,
    )
    opp_mode = rec.get("work_mode") or "Not stated"
    if wm_label == "exact":
        lines.append(f"Work mode matches your preference ({opp_mode}).")
    elif wm_label == "compatible":
        lines.append(f"Work mode is compatible ({opp_mode}).")
    elif wm_label == "partial":
        lines.append(f"Work mode is a partial match ({opp_mode}).")
    elif wm_label == "not stated":
        lines.append("The source does not state work mode.")

    ver_score = breakdown.get("verification_score")
    if ver_score is not None:
        if float(ver_score) >= 0.95:
            lines.append("Source link is available for verification.")
        elif float(ver_score) >= 0.6:
            lines.append("A source link is listed; confirm details before applying.")

    interview_label = describe_interview_fit(
        float(breakdown.get("interview_score", 0.5)),
        profile,
        rec,
    )
    if interview_label == "not stated":
        lines.append("The source does not state interview requirements.")
    elif interview_label == "matches preference":
        lines.append("Interview requirement appears to match your preference.")
    elif interview_label == "mismatch":
        lines.append("Interview requirement may conflict with your preference.")

    if not lines:
        lines.append("Recommended based on overall profile similarity.")

    return lines


def build_score_breakdown_lines(
    rec: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[str]:
    breakdown = rec.get("score_breakdown") or {}
    profile = profile or {}
    if not breakdown:
        return ["  (not available)"]

    lines: List[str] = []

    major = breakdown.get("major_fit_score")
    if major is not None:
        lines.append(f"  Major fit: {_fit_strength(float(major))}")

    role = breakdown.get("role_interest_score")
    if role is not None:
        lines.append(f"  Role/interest fit: {_fit_strength(float(role))}")

    skill = breakdown.get("skill_match_score")
    matched = rec.get("skills_matched") or []
    missing = rec.get("missing_skills") or []
    if skill is not None:
        lines.append(
            f"  Skills fit: {_fit_strength(float(skill))} "
            f"({len(matched)} matched, {len(missing)} missing)"
        )

    city = breakdown.get("city_match_score")
    if city is not None:
        lines.append(
            f"  Location fit: {describe_location_fit(float(city), profile, rec)}"
        )

    prog = breakdown.get("program_type_score")
    if prog is not None:
        lines.append(
            f"  Program type fit: {describe_program_type_fit(float(prog), profile, rec)}"
        )

    wm = breakdown.get("work_mode_score")
    if wm is not None:
        lines.append(
            f"  Work mode fit: {describe_work_mode_fit(float(wm), profile, rec)}"
        )

    interview = breakdown.get("interview_score")
    if interview is not None:
        lines.append(
            f"  Interview fit: {describe_interview_fit(float(interview), profile, rec)}"
        )

    ver = breakdown.get("verification_score")
    if ver is not None and float(ver) >= 0.5:
        lines.append(f"  Source confidence: {_fit_strength(float(ver))}")

    return lines


def _weighted_points(component_key: str, score: float) -> float:
    return TARGET_WEIGHTS[component_key] * score * 100.0


def build_why_this_score_lines(
    rec: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Explain the headline match % with honest positive and limiting factors."""
    profile = profile or {}
    breakdown = rec.get("score_breakdown") or {}
    match_score = float(rec.get("match_score", 0))
    lines: List[str] = [
        f"The {match_score:.0f}% score is the weighted rubric total (see breakdown below).",
    ]

    positives: List[str] = []
    limits: List[str] = []

    major = float(breakdown.get("major_fit_score", 0))
    if major >= FIT_STRONG:
        positives.append(
            f"Strong major fit ({profile.get('major') or 'your major'} aligns with the listing)."
        )

    role = float(breakdown.get("role_interest_score", 0))
    if role >= FIT_STRONG:
        interest = profile.get("interest") or ""
        roles = profile.get("preferred_roles") or []
        role_hint = roles[0] if roles else interest
        positives.append(
            f"Strong role/interest alignment ({role_hint or 'your direction'})."
        )

    prog = float(breakdown.get("program_type_score", 0))
    if prog >= FIT_STRONG:
        positives.append(
            f"Program type matches ({rec.get('program_type') or profile.get('program_type')})."
        )

    wm = float(breakdown.get("work_mode_score", 0))
    if wm >= FIT_STRONG:
        positives.append(
            f"Work mode matches your preference ({rec.get('work_mode') or profile.get('work_mode')})."
        )

    ver = float(breakdown.get("verification_score", 0))
    if ver >= FIT_STRONG and (rec.get("source_url") or "").strip():
        positives.append("Verified source link is available.")

    skill = float(breakdown.get("skill_match_score", 0))
    missing = rec.get("missing_skills") or []
    matched = rec.get("skills_matched") or []
    if skill < FIT_LIMITING:
        gap_note = ""
        if missing:
            gap_note = f" — gaps include {', '.join(missing[:3])}"
        limits.append(
            f"Skill overlap is only partial ({len(matched)} matched, {len(missing)} missing"
            f"{gap_note}); skills rubric contributes ~{_weighted_points('skill_match_score', skill):.0f} of 100."
        )

    city = float(breakdown.get("city_match_score", 0))
    loc_label = describe_location_fit(city, profile, rec)
    student_city = profile.get("city") or ""
    opp_city = rec.get("city") or ""
    if loc_label in {"broad", "regional", "partial", "no match"}:
        limits.append(
            f"Location is {loc_label} ({opp_city or 'listing'} vs your {student_city or 'area'}) — "
            f"not an exact city match; location rubric contributes "
            f"~{_weighted_points('city_match_score', city):.0f} of 100."
        )
    elif city < FIT_LIMITING and opp_city:
        limits.append(
            f"Location fit is limited ({opp_city}); location rubric contributes "
            f"~{_weighted_points('city_match_score', city):.0f} of 100."
        )

    interview_req = rec.get("interview_required") or "Not stated"
    interview_score = float(breakdown.get("interview_score", 0.5))
    interview_pref = profile.get("interview_preference")
    if interview_req == "Not stated" and interview_pref:
        limits.append(
            "Interview requirements are not stated on the source — this is not scored as an "
            "interview match; your preference is neutral until the posting is confirmed."
        )
    elif interview_score < FIT_LIMITING and interview_pref:
        limits.append(
            "Interview fit is partial or mismatched relative to your preference."
        )

    if positives:
        lines.append("Positive factors:")
        for item in positives:
            lines.append(f"  • {item}")
    if limits:
        lines.append("Limiting factors:")
        for item in limits:
            lines.append(f"  • {item}")
    elif match_score < 95:
        lines.append(
            "Limiting factors: no single rubric dimension is far below threshold; "
            "the score reflects several moderate components rather than a perfect fit."
        )

    return lines


def build_next_best_action(
    rec: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> str:
    profile = profile or {}
    missing = [
        s.strip()
        for s in (rec.get("missing_skills") or [])
        if s and str(s).strip()
    ][:4]

    breakdown = rec.get("score_breakdown") or {}
    loc_score = float(breakdown.get("city_match_score", 0))
    loc_label = describe_location_fit(loc_score, profile, rec)
    interview_req = rec.get("interview_required") or "Not stated"
    interview_pref = profile.get("interview_preference")

    if missing:
        skill_text = ", ".join(missing[:3])
        return f"Strengthen {skill_text} for this role direction."

    if loc_label in {"broad", "regional", "partial"} and profile.get("city"):
        return (
            "Confirm whether this opportunity is available in your preferred city "
            f"({profile.get('city')})."
        )

    if interview_req == "Not stated" and interview_pref:
        return "Check the source link or /details 1 to confirm interview requirements."

    gaps: List[str] = []
    if not profile.get("preferred_roles") and not profile.get("interest"):
        gaps.append("preferred role")
    if not profile.get("city") and not profile.get("preferred_locations"):
        gaps.append("city")
    if not profile.get("work_mode"):
        gaps.append("work mode")
    if gaps:
        return f"Add your {', '.join(gaps)} to improve ranking."

    source = (rec.get("source_url") or "").strip()
    if source:
        return "Review the source link and confirm application requirements."

    return "Use /details 1 to compare exact requirements before applying."


def format_details_lines(
    rec: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Build structured /details output lines (no outer section header)."""
    lines: List[str] = []
    rank = rec.get("rank", "?")

    lines.append(f"Rank:              #{rank}")
    lines.append(f"Company:           {rec.get('company', '?')}")
    lines.append(f"Program:           {rec.get('title', '?')}")
    lines.append(f"Match score:       {rec.get('match_score', 0)}%")
    lines.append(f"Score source:      {rec.get('score_source', 'rubric')}")

    lines.append("")
    lines.append("Why this score:")
    for item in build_why_this_score_lines(rec, profile):
        if item.startswith("  •") or item.endswith(":"):
            lines.append(item if item.startswith("  ") else f"  {item}")
        else:
            lines.append(f"  • {item}")

    ml_score = rec.get("ml_score")
    if ml_score is not None:
        ml_src = rec.get("ml_score_source") or ""
        suffix = f" ({ml_src})" if ml_src else ""
        lines.append(f"ML score:          {ml_score}%{suffix}")
    else:
        lines.append("ML score:          not available")

    lines.append(f"Location:          {rec.get('city', '')}")
    lines.append(f"Work mode:         {rec.get('work_mode', '')}")
    lines.append(f"Program type:      {rec.get('program_type', '')}")
    lines.append(f"Interview status:  {rec.get('interview_required', 'Not stated')}")
    source = (rec.get("source_url") or "").strip()
    lines.append(f"Source link:       {source if source else '(none)'}")
    role_cluster = rec.get("role_cluster")
    if role_cluster:
        lines.append(f"Role cluster:      {role_cluster}")

    lines.append("")
    lines.append("Why this matched:")
    for item in build_why_matched_lines(rec, profile):
        lines.append(f"  • {item}")

    lines.append("")
    lines.append("Score breakdown:")
    lines.extend(build_score_breakdown_lines(rec, profile))

    matched = rec.get("skills_matched") or []
    lines.append("")
    if matched:
        shown = matched[:8]
        text = ", ".join(shown)
        if len(matched) > 8:
            text += f" (+{len(matched) - 8} more)"
        lines.append(f"Matched skills:    {text}")
    else:
        lines.append("Matched skills:    (none listed)")

    missing = rec.get("missing_skills") or []
    lines.append("")
    if missing:
        lines.append(f"Missing / recommended skills: {', '.join(missing[:8])}")
    else:
        lines.append("Missing / recommended skills: (none identified from listing)")

    lines.append("")
    lines.append(f"Next best action: {build_next_best_action(rec, profile)}")

    return lines
