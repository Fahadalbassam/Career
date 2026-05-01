"""
test_recommender.py – Unit tests for the recommendation engine.
"""

import pytest
from app.recommender import (
    recommend,
    recommend_from_message,
    get_candidates,
    filter_candidates,
)
from app.parser import parse_message
from app.schemas import ParsedProfile


# ---------------------------------------------------------------------------
# get_candidates
# ---------------------------------------------------------------------------

def test_get_candidates_returns_list():
    candidates = get_candidates()
    assert isinstance(candidates, list)
    assert len(candidates) > 0


def test_get_candidates_are_opportunities():
    from app.schemas import Opportunity
    candidates = get_candidates()
    for c in candidates:
        assert isinstance(c, Opportunity)

# ---------------------------------------------------------------------------
# filter_candidates
# ---------------------------------------------------------------------------

def test_filter_candidates_prefers_major_matches():
    profile = ParsedProfile(
        major="AI",
        city=None,
        interest=None,
        work_mode=None,
        program_type=None,
        skills=[],
    )

    candidates = get_candidates()
    filtered = filter_candidates(profile, candidates)

    assert len(filtered) > 0
    for opp in filtered:
        assert not opp.major_fit or "AI" in opp.major_fit


def test_filter_candidates_prefers_program_type_matches():
    profile = ParsedProfile(
        major=None,
        city=None,
        interest=None,
        work_mode=None,
        program_type="COOP",
        skills=[],
    )

    candidates = get_candidates()
    filtered = filter_candidates(profile, candidates)

    assert len(filtered) > 0
    for opp in filtered:
        assert opp.program_type == "COOP"        


# ---------------------------------------------------------------------------
# recommend
# ---------------------------------------------------------------------------

def test_recommend_returns_top_n():
    profile = ParsedProfile(
        major="DS",
        city="Riyadh",
        interest="Data Science",
        work_mode="Remote",
        program_type="COOP",
        skills=[],
    )
    results = recommend(profile, top_n=3)
    assert len(results) <= 3


def test_recommend_default_top_5():
    profile = ParsedProfile(
        major="CS",
        city=None,
        interest=None,
        work_mode=None,
        program_type=None,
        skills=[],
    )
    results = recommend(profile)
    assert len(results) <= 5


def test_recommend_results_sorted_descending():
    profile = ParsedProfile(
        major="AI",
        city="Riyadh",
        interest="Artificial Intelligence",
        work_mode="On-site",
        program_type="COOP",
        skills=[],
    )
    results = recommend(profile)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_scores_within_bounds():
    profile = ParsedProfile(
        major="CYS",
        city="Dammam",
        interest="Cybersecurity",
        work_mode="Remote",
        program_type="COOP",
        skills=[],
    )
    results = recommend(profile)
    for opp in results:
        assert 0.0 <= opp.score <= 1.0


def test_recommend_does_not_mutate_candidates():
    """Candidates pool should remain at score 0.0 after recommendation."""
    profile = ParsedProfile(
        major="DS",
        city="Riyadh",
        interest="Data Science",
        work_mode="Remote",
        program_type="COOP",
        skills=[],
    )
    recommend(profile)
    candidates = get_candidates()
    for c in candidates:
        assert c.score == 0.0


# ---------------------------------------------------------------------------
# recommend_from_message
# ---------------------------------------------------------------------------

def test_recommend_from_message_returns_response():
    from app.schemas import RecommendResponse
    response = recommend_from_message("I am a CS student in Riyadh looking for COOP")
    assert isinstance(response, RecommendResponse)


def test_recommend_from_message_parses_profile():
    response = recommend_from_message(
        "I am a cybersecurity student in Dammam looking for remote COOP"
    )
    assert response.profile.major == "CYS"
    assert response.profile.city == "Dammam"
    assert response.profile.work_mode == "Remote"
    assert response.profile.program_type == "COOP"


def test_recommend_from_message_has_recommendations():
    response = recommend_from_message("data science student in Riyadh")
    assert len(response.recommendations) > 0


def test_recommend_from_message_total_candidates_positive():
    response = recommend_from_message("AI student")
    assert response.total_candidates > 0


def test_recommendations_include_explanation_reasons():
    profile = ParsedProfile(
        major="CYS",
        city="Riyadh",
        interest="Cybersecurity",
        work_mode="Hybrid",
        program_type="Internship",
        skills=[],
    )

    results = recommend(profile, top_n=5)

    assert len(results) > 0
    assert isinstance(results[0].why_recommended, list)
    assert len(results[0].why_recommended) > 0