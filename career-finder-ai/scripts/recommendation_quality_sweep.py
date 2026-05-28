#!/usr/bin/env python3
"""
recommendation_quality_sweep.py – FINAL-QA-1 curated recommendation quality report.

Runs fixed scenarios through recommend_from_message and writes:
  docs/reports/final_recommendation_quality_sweep.md

Usage (from career-finder-ai/):
  python scripts/recommendation_quality_sweep.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.parser import parse_message  # noqa: E402
from app.recommender import recommend_from_message  # noqa: E402

REPORT_PATH = _REPO_ROOT / "docs" / "reports" / "final_recommendation_quality_sweep.md"

SCENARIOS = [
    {
        "id": 1,
        "name": "Accidental single character",
        "message": "n",
    },
    {
        "id": 2,
        "name": "Vague internship request",
        "message": "I need internship",
    },
    {
        "id": 3,
        "name": "Missing city",
        "message": "I am a CS student looking for cybersecurity COOP. I know Linux and networking.",
    },
    {
        "id": 4,
        "name": "Missing skills",
        "message": "I am a data science student in Riyadh looking for an internship.",
    },
    {
        "id": 5,
        "name": "Cybersecurity complete profile",
        "message": (
            "I am a CS student in Khobar looking for cybersecurity COOP. "
            "I know Linux, networking, and penetration testing."
        ),
    },
    {
        "id": 6,
        "name": "Data science complete profile",
        "message": (
            "I am a data science student in Riyadh. I know Python, SQL, pandas, "
            "and machine learning. I want an internship."
        ),
    },
    {
        "id": 7,
        "name": "Software/backend complete profile",
        "message": (
            "I am a software engineering student in Jeddah. I know JavaScript, "
            "React, Node.js, and APIs. I want backend or full stack COOP."
        ),
    },
    {
        "id": 8,
        "name": "Cloud/DevOps complete profile",
        "message": (
            "I am a computer engineering student in Dammam. I know cloud, Linux, "
            "Docker, and networking. I want DevOps internship."
        ),
    },
    {
        "id": 9,
        "name": "Contradictory interests",
        "message": (
            "I am in Riyadh but also Khobar maybe, CS, interested in AI and "
            "cybersecurity, I know Python and Linux."
        ),
    },
    {
        "id": 10,
        "name": "No skills yet",
        "message": "I do not know any skills yet but I want a high paying AI internship",
    },
]

RELEVANCE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Cybersecurity complete profile": ("cyber", "security", "soc", "network"),
    "Data science complete profile": ("data", "science", "analytic", "machine", "ai"),
    "Software/backend complete profile": (
        "software",
        "engineer",
        "backend",
        "developer",
        "full stack",
        "web",
    ),
    "Cloud/DevOps complete profile": (
        "devops",
        "cloud",
        "infrastructure",
        "platform",
        "engineer",
    ),
}


def _missing_fields_note(profile) -> str:
    gaps = []
    if not profile.major:
        gaps.append("major")
    if not profile.city and not profile.preferred_locations:
        gaps.append("city")
    if not profile.skills:
        gaps.append("skills")
    if not profile.interest:
        gaps.append("interest")
    if not profile.program_type:
        gaps.append("program_type")
    if not profile.work_mode:
        gaps.append("work_mode")
    if gaps:
        return "Missing: " + ", ".join(gaps) + " (frontend/CLI should ask follow-ups)"
    return "Core fields present"


def _top_three_summary(recommendations) -> tuple[str, int | None]:
    if not recommendations:
        return "(none)", None
    parts = []
    top_score = None
    for opp in recommendations[:3]:
        if top_score is None:
            top_score = opp.match_score
        parts.append(f"{opp.rank}. {opp.company} — {opp.title} ({opp.match_score}%)")
    return "; ".join(parts), top_score


def _verdict(name: str, message: str, profile, recommendations, error: str | None) -> tuple[str, str]:
    if error:
        return "Fail", f"Exception: {error}"

    notes: list[str] = []

    if name == "Accidental single character":
        if profile.major or profile.city or profile.skills:
            notes.append("Parser filled fields from accidental input")
        if recommendations and recommendations[0].match_score > 85:
            notes.append("Suspiciously high top score for accidental input")
        if notes:
            return "Review", "; ".join(notes)
        return "Pass", "Empty profile; no crash; scores not over-confident"

    if name in ("Vague internship request", "No skills yet"):
        if not profile.major or not profile.skills:
            return "Pass", "Incomplete profile as expected"
        return "Review", "More fields parsed than expected for vague input"

    if name == "Missing city":
        if profile.city:
            return "Review", f"City unexpectedly set to {profile.city}"
        if not recommendations:
            return "Fail", "No recommendations returned"
        return "Pass", "Major/skills parsed; city gap remains"

    if name == "Missing skills":
        if profile.skills:
            return "Review", "Skills unexpectedly populated"
        if not profile.major or not profile.city:
            return "Review", "Expected major+city without skills"
        return "Pass", "Location/major present; skills gap honest"

    if name == "Contradictory interests":
        if profile.major != "CS":
            notes.append(f"Unexpected major {profile.major}")
        if not profile.city:
            notes.append("No city resolved from dual-city message")
        if notes:
            return "Review", "; ".join(notes)
        return "Pass", "Parsed safely despite mixed interests/locations"

    # Complete profiles
    keywords = RELEVANCE_KEYWORDS.get(name)
    if keywords and recommendations:
        blob = " ".join(
            [
                recommendations[0].title,
                recommendations[0].role_cluster,
                recommendations[0].company,
            ]
        ).lower()
        if not any(k in blob for k in keywords):
            return "Review", f"Top match may be weak for {name}: {recommendations[0].title}"

    if not profile.major or not profile.city or not profile.skills:
        return "Review", "Expected complete profile but some core fields missing"

    scores = [r.match_score for r in recommendations]
    if scores != sorted(scores, reverse=True):
        return "Fail", "Recommendations not sorted by match_score"

    for opp in recommendations:
        if opp.score_source != "rubric":
            return "Fail", f"Unexpected score_source {opp.score_source}"

    if not recommendations:
        return "Fail", "No recommendations for complete profile"

    return "Pass", "Safe parse, rubric scores, relevant top match"


def run_sweep() -> list[dict]:
    rows: list[dict] = []
    for scenario in SCENARIOS:
        message = scenario["message"]
        error = None
        try:
            profile = parse_message(message)
            response = recommend_from_message(message)
            recommendations = response.recommendations
        except Exception as exc:  # noqa: BLE001
            profile = None
            recommendations = []
            error = str(exc)

        verdict, notes = _verdict(
            scenario["name"],
            message,
            profile,
            recommendations,
            error,
        )
        top_summary, top_score = _top_three_summary(recommendations)

        rows.append(
            {
                "scenario": scenario["name"],
                "message": message.replace("|", "\\|"),
                "major": profile.major if profile else "—",
                "city": profile.city if profile else "—",
                "skills": ", ".join(profile.skills[:6]) if profile and profile.skills else "—",
                "interest": profile.interest if profile else "—",
                "missing": _missing_fields_note(profile) if profile else "—",
                "top3": top_summary.replace("|", "\\|"),
                "top_score": top_score if top_score is not None else "—",
                "verdict": verdict,
                "notes": notes.replace("|", "\\|"),
            }
        )
    return rows


def write_report(rows: list[dict]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Final recommendation quality sweep",
        "",
        f"Generated: {ts}",
        "",
        "Automated run of `scripts/recommendation_quality_sweep.py` against "
        "`recommend_from_message` (live rubric ranking).",
        "",
        "| Scenario | Input message | Parsed major | Parsed city | Parsed skills | "
        "Parsed interest | Missing fields / follow-up | Top 3 recommendations | "
        "Top score | Verdict | Notes |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        msg = row["message"]
        if len(msg) > 80:
            msg = msg[:77] + "..."
        lines.append(
            f"| {row['scenario']} | {msg} | {row['major']} | {row['city']} | "
            f"{row['skills']} | {row['interest']} | {row['missing']} | "
            f"{row['top3']} | {row['top_score']} | **{row['verdict']}** | {row['notes']} |"
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
        ]
    )
    passes = sum(1 for r in rows if r["verdict"] == "Pass")
    reviews = sum(1 for r in rows if r["verdict"] == "Review")
    fails = sum(1 for r in rows if r["verdict"] == "Fail")
    lines.append(f"- **Pass:** {passes}/10")
    lines.append(f"- **Review:** {reviews}/10")
    lines.append(f"- **Fail:** {fails}/10")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


def main() -> int:
    rows = run_sweep()
    write_report(rows)
    fails = sum(1 for r in rows if r["verdict"] == "Fail")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
