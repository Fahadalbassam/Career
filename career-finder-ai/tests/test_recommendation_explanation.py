"""Tests for Sprint-3 recommendation explanation and missing-skill cleanup."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from app.parser import parse_message
from app.recommendation_explanation import (
    build_next_best_action,
    build_why_this_score_lines,
    describe_location_fit,
    format_details_lines,
)
from app.recommender import recommend, recommend_from_message
from app.rubric import compute_missing_skills, _student_covers_skill, _student_skill_set
from app.schemas import Opportunity, ParsedProfile

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_PATH = _REPO_ROOT / "scripts" / "careerfinder_cli.py"

SPRINT3_CYBER_MESSAGE = (
    "I am a CS student in Khobar looking for cybersecurity COOP. "
    "I know SQL, MongoDB, Linux, networking, and SIEM. "
    "I prefer on-site and I want an interview. "
    "I want to work in Security Operations."
)


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("careerfinder_cli", _CLI_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["careerfinder_cli"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cli():
    return _load_cli_module()


def _sprint3_profile_and_rec():
    response = recommend_from_message(SPRINT3_CYBER_MESSAGE)
    profile = response.profile.model_dump()
    rec = response.recommendations[0].model_dump()
    return profile, rec


def test_details_includes_core_fields(capsys, cli):
    profile, rec = _sprint3_profile_and_rec()
    cli.print_recommendation_details(rec, profile)
    out = capsys.readouterr().out
    assert "Score source:      rubric" in out
    assert "Match score:" in out
    assert rec["company"] in out
    assert rec["title"] in out
    assert "Location:" in out
    assert "Program type:" in out
    assert "Work mode:" in out


def test_details_shows_matched_and_missing_skills(capsys, cli):
    profile, rec = _sprint3_profile_and_rec()
    cli.print_recommendation_details(rec, profile)
    out = capsys.readouterr().out
    if rec.get("skills_matched"):
        assert "Matched skills:" in out
    if rec.get("missing_skills"):
        assert "Missing / recommended skills:" in out


def test_details_does_not_list_exact_user_skills_as_missing():
    profile, rec = _sprint3_profile_and_rec()
    student = {s.lower() for s in profile["skills"]}
    for missing in rec.get("missing_skills") or []:
        assert missing.lower() not in student


def test_next_best_action_uses_concrete_missing_skills():
    profile, rec = _sprint3_profile_and_rec()
    action = build_next_best_action(rec, profile)
    assert "more technical skills" not in action.lower()
    if rec.get("missing_skills"):
        assert "Strengthen" in action
        assert rec["missing_skills"][0].lower() in action.lower()


def test_broad_location_described_honestly():
    profile, rec = _sprint3_profile_and_rec()
    breakdown = rec.get("score_breakdown") or {}
    loc_score = float(breakdown.get("city_match_score", 0))
    label = describe_location_fit(loc_score, profile, rec)
    if loc_score <= 0.7 and profile.get("city", "").lower() != (rec.get("city") or "").lower():
        assert label in {"regional", "broad", "partial", "acceptable"}
    lines = format_details_lines(rec, profile)
    text = "\n".join(lines)
    if label in {"regional", "broad"}:
        assert "not an exact city match" in text.lower() or "broad location" in text.lower()


def test_details_explains_score_with_positive_and_limiting_factors(capsys, cli):
    profile, rec = _sprint3_profile_and_rec()
    cli.print_recommendation_details(rec, profile)
    out = capsys.readouterr().out
    assert "Why this score:" in out
    assert "Positive factors:" in out
    assert "Limiting factors:" in out
    assert 80 <= float(rec["match_score"]) <= 90
    assert "not an exact city match" in out.lower() or "broad" in out.lower()
    assert "does not state interview" in out.lower()


def test_why_this_score_mentions_interview_not_stated_not_a_match():
    profile, rec = _sprint3_profile_and_rec()
    if (rec.get("interview_required") or "Not stated") != "Not stated":
        pytest.skip("top listing states interview requirement")
    lines = build_why_this_score_lines(rec, profile)
    text = "\n".join(lines).lower()
    assert "not stated" in text
    assert "not scored as an interview match" in text or "neutral" in text


def test_interview_not_stated_described_honestly():
    rec = {
        "interview_required": "Not stated",
        "score_breakdown": {"interview_score": 0.5},
        "missing_skills": [],
        "city": "Riyadh",
        "program_type": "COOP",
        "work_mode": "On-site",
    }
    profile = {"interview_preference": "Interview preferred"}
    lines = format_details_lines(rec, profile)
    text = "\n".join(lines)
    assert "Interview status:  Not stated" in text
    assert "does not state interview" in text.lower() or "not stated" in text.lower()


def test_role_family_evidence_when_available():
    profile, rec = _sprint3_profile_and_rec()
    why = rec.get("why_recommended") or []
    has_rf = any(r.startswith("Role-family match:") for r in why)
    lines = format_details_lines(rec, profile)
    text = "\n".join(lines)
    if has_rf:
        assert "Role-family evidence:" in text


def test_recommendations_sorted_by_match_score():
    response = recommend_from_message(SPRINT3_CYBER_MESSAGE)
    scores = [r.match_score for r in response.recommendations]
    assert scores == sorted(scores, reverse=True)


def test_match_score_in_range_and_score_source_rubric():
    response = recommend_from_message(SPRINT3_CYBER_MESSAGE)
    for rec in response.recommendations:
        assert 0 <= rec.match_score <= 100
        assert rec.score_source == "rubric"


@pytest.mark.parametrize(
    ("student_skill", "opp_skill"),
    [
        ("cybersecurity", "cybersecurity"),
        ("SIEM", "siem"),
        ("Power BI", "powerbi"),
        ("Node.js", "nodejs"),
    ],
)
def test_missing_skills_alias_cleanup(student_skill, opp_skill):
    profile = ParsedProfile(major="CS", skills=[student_skill])
    student = _student_skill_set(profile)
    assert _student_covers_skill(student, opp_skill)

    opportunity = Opportunity(
        id=9001,
        company="Test",
        title="Test Role",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CS"],
        skills_list=[opp_skill],
        source_url="https://example.com",
    )
    missing = compute_missing_skills(profile, opportunity)
    assert opp_skill.lower() not in {m.lower() for m in missing}


def test_cybersecurity_not_missing_when_student_has_cybersecurity():
    profile = ParsedProfile(major="CS", skills=["cybersecurity"])
    opportunity = Opportunity(
        id=9002,
        company="Test",
        title="Security Role",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CS"],
        skills_list=["cybersecurity", "security fundamentals"],
        source_url="https://example.com",
    )
    missing = compute_missing_skills(profile, opportunity)
    lowered = {m.lower() for m in missing}
    assert "cybersecurity" not in lowered
    assert "security fundamentals" not in lowered
