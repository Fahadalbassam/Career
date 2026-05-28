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
    assert "/details 1" in reply or "missing skills" in reply.lower()
