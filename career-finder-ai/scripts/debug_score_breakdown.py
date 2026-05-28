#!/usr/bin/env python3
"""SCORE-AUDIT-1: Print rubric breakdown for a fixed cybersecurity COOP profile."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.opportunity_enrichment import enrich_opportunity_signals  # noqa: E402
from app.parser import parse_message  # noqa: E402
from app.recommender import recommend  # noqa: E402
from app.rubric import score_profile_opportunity_pair  # noqa: E402

AUDIT_MESSAGE = (
    "I am a CS student in Khobar looking for cybersecurity COOP. "
    "I know SQL, MongoDB, Linux, networking, and SIEM. "
    "I prefer on-site and I want an interview. "
    "I want to work in Security Operations."
)

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


def main() -> None:
    profile = parse_message(AUDIT_MESSAGE)
    print("=== Parsed profile ===")
    print(json.dumps(profile.model_dump(), indent=2))

    recs = recommend(profile, top_n=5)
    print("\n=== Top 5 recommendations ===")
    for rec in recs:
        rubric = score_profile_opportunity_pair(profile, rec)
        target = rubric.pop("target_score")
        signals = enrich_opportunity_signals(rec)
        print(f"\n--- Rank {rec.rank}: {rec.company} — {rec.title} ({rec.match_score}%) ---")
        print(f"City: {rec.city} | Work mode: {rec.work_mode} | Program: {rec.program_type}")
        print(f"Role cluster: {rec.role_cluster} | Interview: {rec.interview_required}")
        print(f"Target score (rubric): {target}")
        for key, weight in WEIGHTS.items():
            component = rubric[key]
            print(
                f"  {key}: {component:.4f} (weight {weight:.0%}) "
                f"-> {component * weight * 100:.2f} pts"
            )
        print(f"score_breakdown: {rec.score_breakdown}")
        print(f"matched_skills: {rec.skills_matched}")
        print(f"missing_skills: {rec.missing_skills}")
        print(f"required_skills: {signals.get('required_skills')}")
        print(f"preferred_skills: {signals.get('preferred_skills')}")
        print(f"inferred_skills: {signals.get('inferred_skills')}")
        print(f"why_recommended: {rec.why_recommended}")


if __name__ == "__main__":
    main()
