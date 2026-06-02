#!/usr/bin/env python3
"""SCORE-AUDIT-2: Compare rubric breakdown before/after adding git and apis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.opportunity_enrichment import enrich_opportunity_signals  # noqa: E402
from app.recommender import recommend  # noqa: E402
from app.rubric import (  # noqa: E402
    compute_profile_skills_matched,
    score_profile_opportunity_pair,
)
from app.schemas import ParsedProfile  # noqa: E402

WEIGHTS = {
    "major_fit_score": 0.35,
    "skill_match_score": 0.20,
    "role_interest_score": 0.15,
    "city_match_score": 0.10,
    "program_type_score": 0.10,
    "work_mode_score": 0.05,
    "verification_score": 0.03,
    "interview_score": 0.02,
}

AUDIT_BASE = {
    "major": "CS",
    "university": "IAU",
    "city": "Khobar",
    "interest": "Cybersecurity",
    "program_type": "COOP",
    "work_mode": "On-site",
    "preferred_roles": ["Security Operations"],
    "interview_preference": "Interview preferred: In person",
}

PROFILE_A_SKILLS = ["sql", "linux", "networking", "cybersecurity"]
PROFILE_B_SKILLS = PROFILE_A_SKILLS + ["git", "apis"]


def _profile(skills: list[str]) -> ParsedProfile:
    return ParsedProfile(**AUDIT_BASE, skills=skills)


def _print_top(profile: ParsedProfile, label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"Profile {label}: skills = {profile.skills}")
    print("=" * 72)

    recs = recommend(profile, top_n=5)
    for rec in recs:
        rubric = score_profile_opportunity_pair(profile, rec)
        target = rubric.pop("target_score")
        signals = enrich_opportunity_signals(rec)
        matched = compute_profile_skills_matched(profile, rec)

        print(f"\n--- Rank {rec.rank}: {rec.company} — {rec.title} ({rec.match_score}%) ---")
        print(f"role_cluster: {rec.role_cluster}")
        print(f"match_score: {rec.match_score}")
        print(f"target_score (rubric): {target}")
        print(f"score_breakdown: {rec.score_breakdown}")
        print(f"matched_skills: {matched}")
        print(f"missing_skills: {rec.missing_skills}")
        print(
            "components: "
            f"role/interest={rubric['role_interest_score']:.4f}, "
            f"skill={rubric['skill_match_score']:.4f}, "
            f"city={rubric['city_match_score']:.4f}, "
            f"program={rubric['program_type_score']:.4f}, "
            f"work_mode={rubric['work_mode_score']:.4f}, "
            f"interview={rubric['interview_score']:.4f}"
        )
        for key, weight in WEIGHTS.items():
            component = rubric[key]
            print(
                f"  {key}: {component:.4f} (weight {weight:.0%}) "
                f"-> {component * weight * 100:.2f} pts"
            )
        print(f"required_skills (enrichment): {signals.get('required_skills')}")
        print(f"preferred_skills (enrichment): {signals.get('preferred_skills')}")
        print(f"explicit skills_list: {rec.skills_list}")


def main() -> None:
    profile_a = _profile(PROFILE_A_SKILLS)
    profile_b = _profile(PROFILE_B_SKILLS)

    print("=== SCORE-AUDIT-2 shared profile fields ===")
    print(json.dumps(AUDIT_BASE, indent=2))

    _print_top(profile_a, "A (before git/apis)")
    _print_top(profile_b, "B (after git/apis)")


if __name__ == "__main__":
    main()
