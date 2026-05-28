"""
assistant_reply.py – Context-aware assistant messages for CLI and tests.

Produces focused replies that only ask for profile fields that are still
missing. When the profile is mostly complete and the top match is strong,
suggests concrete skill gaps instead of repeating generic prompts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _is_missing(value: str | None) -> bool:
    if value is None:
        return True
    stripped = str(value).strip()
    return stripped == "" or stripped.lower() == "not stated"


def _profile_gaps(profile: Dict[str, Any]) -> List[str]:
    """Return human labels for optional fields still missing from the profile."""
    gaps: List[str] = []
    roles = profile.get("preferred_roles") or []
    if not roles:
        gaps.append("preferred role")
    if _is_missing(profile.get("work_mode")):
        gaps.append("work mode")
    if _is_missing(profile.get("interview_preference")):
        gaps.append("interview preference")
    return gaps


def _student_skill_tokens(profile: Dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for skill in profile.get("skills") or []:
        if skill and not _is_missing(skill):
            tokens.add(str(skill).strip().lower())
    return tokens


def _missing_skills_from_recommendation(rec: Optional[Dict[str, Any]]) -> List[str]:
    """Return concrete missing skills from the top recommendation when present."""
    if not rec:
        return []
    missing = rec.get("missing_skills") or []
    out: List[str] = []
    for item in missing:
        if item and not _is_missing(str(item)):
            text = str(item).strip()
            if text and text not in out:
                out.append(text)
        if len(out) >= 4:
            break
    return out


def _suggest_skill_gaps(profile: Dict[str, Any]) -> List[str]:
    """Return a short list of skills that could improve ranking for this interest."""
    have = _student_skill_tokens(profile)
    interest = (profile.get("interest") or "").strip().lower()

    if "cyber" in interest or "security" in interest:
        candidates = [
            ("linux", "Linux"),
            ("networking", "networking"),
            ("siem", "SIEM"),
            ("cybersecurity", "security fundamentals"),
        ]
    elif "data" in interest:
        candidates = [
            ("python", "Python"),
            ("sql", "SQL"),
            ("pandas", "pandas"),
            ("machine learning", "machine learning"),
        ]
    elif "cloud" in interest or "devops" in interest:
        candidates = [
            ("linux", "Linux"),
            ("docker", "Docker"),
            ("kubernetes", "Kubernetes"),
            ("aws", "cloud (AWS/Azure)"),
        ]
    else:
        candidates = [
            ("python", "Python"),
            ("sql", "SQL"),
            ("git", "Git"),
            ("linux", "Linux"),
        ]

    suggestions: List[str] = []
    for token, label in candidates:
        if token not in have and label not in suggestions:
            suggestions.append(label)
        if len(suggestions) >= 4:
            break
    return suggestions


def build_assistant_reply_parts(
    profile: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Build structured assistant copy.

    Keys: ``headline``, ``top_match``, ``next_action``, ``improve_score_by``
    (last two may be empty).
    """
    if _is_missing(profile.get("major")):
        return {
            "headline": (
                "I still need your major to rank opportunities correctly. "
                "Are you CS, AI, CYS, CIS, DS, DE, CE, or FinTech?"
            ),
            "top_match": "",
            "next_action": "",
            "improve_score_by": "",
        }

    skills = profile.get("skills") or []
    if not skills:
        return {
            "headline": (
                "Tell me a few technical skills you have used, such as Python, SQL, "
                "Linux, networking, React, Docker, cloud, cybersecurity, or machine learning."
            ),
            "top_match": "",
            "next_action": "",
            "improve_score_by": "",
        }

    preferred = profile.get("preferred_locations") or []
    if _is_missing(profile.get("city")) and not preferred:
        return {
            "headline": (
                "Which city or preferred location should I prioritise? "
                "For example Riyadh, Jeddah, Dammam, Khobar, Dhahran, remote, or multiple."
            ),
            "top_match": "",
            "next_action": "",
            "improve_score_by": "",
        }

    if _is_missing(profile.get("program_type")):
        return {
            "headline": "Are you looking for COOP, internship, Tamheer, or general training?",
            "top_match": "",
            "next_action": "",
            "improve_score_by": "",
        }

    if _is_missing(profile.get("work_mode")):
        return {
            "headline": "Do you prefer remote, hybrid, or on-site opportunities?",
            "top_match": "",
            "next_action": "",
            "improve_score_by": "",
        }

    top_rec = recommendations[0] if recommendations else None
    top_score = int(top_rec.get("match_score", 0)) if top_rec else 0
    company = (top_rec or {}).get("company", "Unknown")
    title = (top_rec or {}).get("title", "role")
    top_match = f"{company} — {title}, {top_score}%" if top_rec else ""

    gaps = _profile_gaps(profile)
    skill_gaps = _missing_skills_from_recommendation(top_rec) or _suggest_skill_gaps(profile)

    def _next_action_for_skill_gaps() -> str:
        if skill_gaps:
            skill_text = ", ".join(skill_gaps[:4])
            return (
                f"Review /details 1 and strengthen skills like {skill_text} "
                "to improve the match."
            )
        return (
            "Use /details 1 to review missing skills and confirm the opportunity requirements."
        )

    if recommendations and top_score >= 80 and not gaps:
        skill_text = ", ".join(skill_gaps[:4]) if skill_gaps else ""
        return {
            "headline": "Strong match found.",
            "top_match": top_match,
            "next_action": _next_action_for_skill_gaps(),
            "improve_score_by": skill_text,
        }

    if recommendations and top_score >= 70:
        if gaps:
            gap_text = ", ".join(gaps)
            return {
                "headline": "Good matches found — a few details would sharpen the ranking.",
                "top_match": top_match,
                "next_action": f"Tell me your {gap_text}.",
                "improve_score_by": gap_text,
            }
        skill_text = ", ".join(skill_gaps[:4]) if skill_gaps else ""
        return {
            "headline": "Strong match found.",
            "top_match": top_match,
            "next_action": _next_action_for_skill_gaps(),
            "improve_score_by": skill_text,
        }

    if recommendations:
        if gaps:
            gap_text = ", ".join(gaps)
            next_action = f"Tell me your {gap_text}."
        else:
            next_action = (
                "Tell me your city, program type, and 2–3 skills so I can rank "
                "opportunities more accurately."
            )
        return {
            "headline": "Early matches found — your profile can be sharper.",
            "top_match": top_match,
            "next_action": next_action,
            "improve_score_by": ", ".join(skill_gaps[:3]) if skill_gaps else "",
        }

    return {
        "headline": (
            "I'm scanning Saudi COOP and internship options. "
            "Share your major, city, skills, or preferred work mode to get a personalised ranking."
        ),
        "top_match": "",
        "next_action": "",
        "improve_score_by": "",
    }


def format_assistant_reply(parts: Dict[str, str]) -> str:
    """Flatten structured parts into a short multi-line message."""
    lines: List[str] = [parts.get("headline", "").strip()]
    top = parts.get("top_match", "").strip()
    if top:
        lines.append(f"Top match: {top}")
    next_action = parts.get("next_action", "").strip()
    if next_action:
        lines.append(f"Next best action: {next_action}")
    improve = parts.get("improve_score_by", "").strip()
    if improve and improve not in next_action:
        lines.append(f"Improve score by adding: {improve}")
    return "\n".join(line for line in lines if line)


def build_assistant_reply(
    profile: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
) -> str:
    """Return the assistant message string for a profile + recommendations."""
    return format_assistant_reply(
        build_assistant_reply_parts(profile, recommendations)
    )
