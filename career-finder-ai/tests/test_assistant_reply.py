"""Tests for context-aware assistant reply generation (FINAL-POLISH-1)."""

from app.assistant_reply import build_assistant_reply, build_assistant_reply_parts
from app.parser import parse_message
from app.recommender import recommend_from_message


def _profile_dict(**kwargs):
    base = {
        "major": "CS",
        "city": "Khobar",
        "interest": "Cybersecurity",
        "program_type": "COOP",
        "work_mode": "On-site",
        "skills": ["sql", "infrastructure"],
        "preferred_roles": ["Security Operations"],
        "interview_preference": "Interview preferred",
        "preferred_locations": [],
        "qualifications": [],
    }
    base.update(kwargs)
    return base


def test_assistant_does_not_ask_work_mode_when_present():
    reply = build_assistant_reply(
        _profile_dict(),
        [{"company": "Acme", "title": "COOP", "match_score": 81}],
    )
    assert "work mode" not in reply.lower()


def test_assistant_does_not_ask_interview_when_present():
    reply = build_assistant_reply(
        _profile_dict(),
        [{"company": "Acme", "title": "COOP", "match_score": 81}],
    )
    assert "interview preference" not in reply.lower()


def test_assistant_does_not_ask_preferred_role_when_present():
    reply = build_assistant_reply(
        _profile_dict(),
        [{"company": "Acme", "title": "COOP", "match_score": 81}],
    )
    assert "preferred role" not in reply.lower()


def test_assistant_suggests_skills_when_profile_complete_and_strong_match():
    reply = build_assistant_reply(
        _profile_dict(),
        [{"company": "Bank Albilad", "title": "Cooperative Training", "match_score": 81}],
    )
    assert "Strong match" in reply
    assert "Linux" in reply or "networking" in reply or "SIEM" in reply


def test_assistant_asks_only_missing_gaps():
    parts = build_assistant_reply_parts(
        _profile_dict(preferred_roles=[], interview_preference=None),
        [{"company": "Acme", "title": "COOP", "match_score": 75}],
    )
    assert "interview preference" in parts["next_action"].lower()
    assert "work mode" not in parts["next_action"].lower()


def test_recommend_from_message_with_preferred_roles_and_interview():
    combined = (
        "CS student in Khobar, SQL and mongodb, COOP, on-site, "
        "interview preferred, security developer operator"
    )
    response = recommend_from_message(combined)
    assert response.profile.interview_preference == "Interview preferred"
    assert response.profile.preferred_roles
    assert response.recommendations
    scores = [r.match_score for r in response.recommendations]
    assert scores == sorted(scores, reverse=True)
    assert all(r.score_source == "rubric" for r in response.recommendations[:3])


def test_assistant_uses_concrete_missing_skills_not_generic_technical():
    from app.recommender import recommend_from_message

    response = recommend_from_message(
        "I am a CS student in Khobar looking for cybersecurity COOP. "
        "I know SQL, MongoDB, Linux, networking, and SIEM. "
        "I prefer on-site and I want an interview. "
        "I want to work in Security Operations."
    )
    recs = [r.model_dump() for r in response.recommendations]
    reply = build_assistant_reply(response.profile.model_dump(), recs)
    assert "more technical skills" not in reply.lower()
    if response.recommendations[0].missing_skills:
        assert "/details 1" in reply or "strengthen skills like" in reply.lower()


def test_assistant_suggests_details_when_no_missing_skills_list():
    reply = build_assistant_reply(
        _profile_dict(),
        [{"company": "Acme", "title": "COOP", "match_score": 81, "missing_skills": []}],
    )
    assert "more technical skills" not in reply.lower()
    assert "/details" in reply or "missing skills" in reply.lower()


def test_hotfix_assistant_no_interview_prompt_when_in_person_pref_set():
    parts = build_assistant_reply_parts(
        _profile_dict(interview_preference="Interview preferred: In person"),
        [{"company": "Acme", "title": "COOP", "match_score": 75}],
    )
    assert "interview preference" not in parts["next_action"].lower()


def test_hotfix_dry_run_profile_rubric_sorted():
    combined = (
        "im a cs student at imam abdulrahman bin faisal university, currently living in khobar, "
        "im looking for coop opportunities in riyadh, im interested in security and devops, "
        "i have a background in prompt engineering and web development, "
        "I want my COop to be onsite or hybrid. "
        "interview preference would be in person. i know API"
    )
    response = recommend_from_message(combined)
    assert response.profile.interview_preference == "Interview preferred: In person"
    assert "apis" in response.profile.skills
    assert response.recommendations
    scores = [r.match_score for r in response.recommendations]
    assert scores == sorted(scores, reverse=True)
    assert all(r.score_source == "rubric" for r in response.recommendations[:3])


def test_hotfix_missing_skills_api_alias_covered_by_apis_skill():
    from app.rubric import compute_missing_skills
    from app.schemas import Opportunity, ParsedProfile

    profile = ParsedProfile(major="CS", skills=["apis"])
    opportunity = Opportunity(
        id=1,
        company="Test",
        title="Backend",
        city="Riyadh",
        work_mode="Remote",
        program_type="COOP",
        major_fit=["CS"],
        skills_list=["python", "api", "apis", "REST API"],
        source_url="https://example.com",
    )
    missing = [m.lower() for m in compute_missing_skills(profile, opportunity)]
    assert "api" not in missing
    assert "apis" not in missing
    assert "rest api" not in missing
