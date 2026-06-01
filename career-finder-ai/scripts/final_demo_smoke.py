#!/usr/bin/env python3
"""
SPRINT-4 — Final demo smoke checks (backend-level, no manual CLI input).

Run from career-finder-ai/:
    python scripts/final_demo_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.assistant_reply import build_assistant_reply_parts  # noqa: E402
from app.parser import parse_message  # noqa: E402
from app.recommendation_explanation import format_details_lines  # noqa: E402
from app.recommender import recommend_from_message  # noqa: E402
from app.role_inference import infer_role_families  # noqa: E402

MSG_DISCOVERY = "I don't know what role I want"
MSG_SQL = "I know SQL"
MSG_LOCATION = (
    "I'm in Khobar but I don't mind going to Riyadh or Jeddah for COOP"
)
MSG_FULL = (
    "I am a CS student in Khobar looking for cybersecurity COOP. "
    "I know SQL, MongoDB, Linux, networking, and SIEM. "
    "I prefer on-site and I want an interview. "
    "I want to work in Security Operations."
)

USER_SKILLS_LOWER = frozenset(
    {"linux", "networking", "siem", "mongodb", "sql", "cybersecurity"}
)

Check = Tuple[str, Callable[[], None]]


def _fail(msg: str) -> None:
    raise AssertionError(msg)


def _check_discovery() -> None:
    profile = parse_message(MSG_DISCOVERY)
    result = infer_role_families(profile, message=MSG_DISCOVERY)
    if not result.discovery_mode:
        _fail("discovery_mode should be True for role-unknown message")
    if not result.guided_question:
        _fail("guided_question should be set in discovery mode")
    q = result.guided_question.lower()
    if not any(k in q for k in ("analyst", "engineer", "security", "1.", "2.")):
        _fail("discovery guided question should list role-direction choices")
    parts = build_assistant_reply_parts(
        profile.model_dump(), [], message=MSG_DISCOVERY
    )
    headline = (parts.get("headline") or "").lower()
    if not any(k in headline for k in ("analyst", "engineer", "security", "1.")):
        _fail("assistant headline should show role-direction choices")


def _check_sql_ambiguity() -> None:
    profile = parse_message(MSG_SQL)
    result = infer_role_families(profile, message=MSG_SQL)
    if not result.is_ambiguous:
        _fail("SQL-only profile should be ambiguous (no forced single role)")
    if not result.guided_question:
        _fail("SQL-only profile should include a clarifying guided question")
    top = result.matches[0] if result.matches else None
    if top is not None and top.confidence >= 0.35:
        _fail(
            f"SQL alone should not force one role at high confidence; got {top.role_family} "
            f"({top.confidence})"
        )


def _check_location_flexibility() -> None:
    profile = parse_message(MSG_LOCATION)
    if profile.city != "Khobar" and profile.home_city != "Khobar":
        _fail(f"Khobar/home city expected; got city={profile.city!r} home={profile.home_city!r}")
    acceptable = {c.lower() for c in (profile.acceptable_locations or [])}
    preferred = {c.lower() for c in (profile.preferred_locations or [])}
    if "riyadh" not in acceptable and "riyadh" not in preferred:
        _fail("Riyadh should be accepted or preferred")
    if "jeddah" not in acceptable and "jeddah" not in preferred:
        _fail("Jeddah should be accepted or preferred")
    if profile.location_flexibility not in ("flexible", "moderate"):
        _fail(f"location_flexibility should be flexible/moderate; got {profile.location_flexibility!r}")


def _check_full_recommendation() -> None:
    response = recommend_from_message(MSG_FULL, top_n=5)
    recs = response.recommendations
    if not recs:
        _fail("full cybersecurity demo should return at least one recommendation")
    scores = [r.match_score for r in recs]
    for score in scores:
        if not (0 <= score <= 100):
            _fail(f"match_score out of range: {score}")
    for rec in recs:
        if rec.score_source != "rubric":
            _fail(f"score_source must be rubric; got {rec.score_source!r}")
    if scores != sorted(scores, reverse=True):
        _fail("recommendations must be sorted by match_score descending")

    top = recs[0]
    profile_dict = response.profile.model_dump()
    lines = format_details_lines(top.model_dump(), profile_dict)
    text = "\n".join(lines)
    if not text.strip():
        _fail("format_details_lines produced empty output for top recommendation")

    student = {s.lower() for s in (profile_dict.get("skills") or [])}
    for missing in top.missing_skills or []:
        ml = missing.lower()
        if ml in student or ml in USER_SKILLS_LOWER:
            _fail(f"missing_skills should not list user skill: {missing!r}")

    print("\n--- Top recommendation (full demo) ---")
    print(f"  {top.company} — {top.title}")
    print(f"  match_score={top.match_score}%  score_source={top.score_source}")
    if "bank albilad" in top.company.lower():
        print("  (canonical demo anchor: Bank Albilad #1)")


def _run_checks() -> Tuple[int, int, List[str]]:
    checks: List[Check] = [
        ("guided discovery for role-unknown input", _check_discovery),
        ("SQL ambiguity (no forced single role)", _check_sql_ambiguity),
        ("Khobar + Riyadh/Jeddah location flexibility", _check_location_flexibility),
        ("full demo recommendations + details + missing-skill sanity", _check_full_recommendation),
    ]
    passed = 0
    failures: List[str] = []
    for name, fn in checks:
        try:
            fn()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failures.append(f"{name}: {exc}")
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # pragma: no cover - unexpected
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    return passed, len(checks), failures


def main() -> int:
    print("CareerFinder.ai — SPRINT-4 final demo smoke\n")
    passed, total, failures = _run_checks()
    print()
    if failures:
        print(f"SUMMARY: FAIL ({passed}/{total} checks passed)")
        for item in failures:
            print(f"  - {item}")
        return 1
    print(f"SUMMARY: PASS ({passed}/{total} checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
