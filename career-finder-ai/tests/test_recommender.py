"""
test_recommender.py – Unit tests for the recommendation engine.
"""

import pytest
import pandas as pd
import app.recommender as recommender_module

from app.recommender import (
    recommend,
    recommend_from_message,
    get_candidates,
    filter_candidates,
    load_opportunities_from_xlsx
)
from app.parser import parse_message
from app.schemas import Opportunity, ParsedProfile


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

def test_recommendations_include_skill_matches():
    profile = ParsedProfile(
        major="CYS",
        city="Riyadh",
        interest="Cybersecurity",
        work_mode=None,
        program_type=None,
        skills=["linux", "network security"],
    )

    results = recommend(profile, top_n=5)

    assert len(results) > 0

    results_with_skill_matches = [
        opp for opp in results
        if len(opp.skills_matched) > 0
    ]

    assert len(results_with_skill_matches) > 0

    all_matched_skills = []
    for opp in results_with_skill_matches:
        all_matched_skills.extend(opp.skills_matched)

    assert "linux" in all_matched_skills or "network security" in all_matched_skills

def test_recommendations_explain_skill_matches():
    profile = ParsedProfile(
        major="CYS",
        city="Riyadh",
        interest="Cybersecurity",
        work_mode=None,
        program_type=None,
        skills=["linux", "network security"],
    )

    results = recommend(profile, top_n=5)

    assert len(results) > 0

    all_reasons = []
    for opp in results:
        all_reasons.extend(opp.why_recommended)

    assert any("Matches your skills" in reason for reason in all_reasons)

def test_load_opportunities_from_xlsx(tmp_path):
    xlsx_file = tmp_path / "opportunities_clean.xlsx"

    data = {
        "id": [1],
        "company": ["STC"],
        "title": ["Cybersecurity Internship"],
        "city": ["Riyadh"],
        "work_mode": ["Hybrid"],
        "program_type": ["Internship"],
        "major_fit": ["CYS,CS"],
        "requirements": ["Linux and network security"],
        "skills_list": ["linux,network security"],
        "source_url": ["https://example.com"],
    }

    df = pd.DataFrame(data)
    df.to_excel(xlsx_file, sheet_name="Opportunities", index=False)

    opportunities = load_opportunities_from_xlsx(xlsx_file)

    assert len(opportunities) == 1
    assert opportunities[0].company == "STC"
    assert opportunities[0].title == "Cybersecurity Internship"
    assert opportunities[0].city == "Riyadh"
    assert opportunities[0].work_mode == "Hybrid"
    assert opportunities[0].program_type == "Internship"
    assert opportunities[0].major_fit == ["CYS", "CS"]
    assert opportunities[0].skills_list == ["linux", "network security"]

def test_recommend_uses_xlsx_loaded_opportunities(monkeypatch):
    fake_excel_opportunities = [
        Opportunity(
            id=101,
            company="Test Data Company",
            title="Data Science COOP",
            city="Riyadh",
            work_mode="Remote",
            program_type="COOP",
            major_fit=["DS", "AI", "CS"],
            requirements="Python, SQL, data analysis",
            skills_list=["python", "sql", "data analysis"],
            source_url="https://example.com/data-coop",
        ),
        Opportunity(
            id=102,
            company="Test Cyber Company",
            title="Cybersecurity Internship",
            city="Jeddah",
            work_mode="On-site",
            program_type="Internship",
            major_fit=["CYS"],
            requirements="Network security and Linux",
            skills_list=["network security", "linux"],
            source_url="https://example.com/cyber-internship",
        ),
    ]

    def fake_loader():
        return fake_excel_opportunities

    monkeypatch.setattr(
        recommender_module,
        "load_opportunities_from_xlsx",
        fake_loader,
    )

    profile = ParsedProfile(
        major="DS",
        city="Riyadh",
        interest="Data Science",
        work_mode="Remote",
        program_type="COOP",
        skills=["python", "sql"],
    )

    results = recommender_module.recommend(profile, top_n=5)

    assert len(results) > 0
    assert results[0].company == "Test Data Company"
    assert results[0].title == "Data Science COOP"
    assert results[0].score > 0.8
    assert "python" in results[0].skills_matched
    assert "sql" in results[0].skills_matched


def test_recommendations_include_rank_numbers():
    profile = ParsedProfile(
        major="CYS",
        city="Riyadh",
        interest="Cybersecurity",
        work_mode="Hybrid",
        program_type="Internship",
        skills=["linux", "network security"],
    )

    results = recommend(profile, top_n=5)

    assert len(results) > 0

    for index, opp in enumerate(results, start=1):
        assert opp.rank == index