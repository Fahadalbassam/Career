"""
test_scoring.py – Unit tests for the opportunity scoring functions.
"""

import pytest
from app.schemas import Opportunity, ParsedProfile
from app.scoring import (
    city_match_score,
    compute_score,
    interest_match_score,
    major_fit_score,
    program_type_match_score,
    skills_match_score,
    verified_source_bonus,
    work_mode_match_score,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_opportunity(**kwargs) -> Opportunity:
    """Helper to create an Opportunity with sensible defaults."""
    defaults = {
        "id": 1,
        "company": "Test Co",
        "title": "Data Science COOP",
        "city": "Riyadh",
        "work_mode": "Remote",
        "program_type": "COOP",
        "major_fit": ["DS", "CS"],
        "source_url": "https://example.com",
        "score": 0.0,
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


def make_profile(**kwargs) -> ParsedProfile:
    """Helper to create a ParsedProfile with sensible defaults."""
    defaults = {
        "major": "DS",
        "city": "Riyadh",
        "interest": "Data Science",
        "work_mode": "Remote",
        "program_type": "COOP",
        "skills": [],
    }
    defaults.update(kwargs)
    return ParsedProfile(**defaults)


# ---------------------------------------------------------------------------
# major_fit_score
# ---------------------------------------------------------------------------

def test_major_fit_score_exact_match():
    profile = make_profile(major="DS")
    opp = make_opportunity(major_fit=["DS", "CS"])
    assert major_fit_score(profile, opp) == 1.0


def test_major_fit_score_no_match():
    profile = make_profile(major="CYS")
    opp = make_opportunity(major_fit=["DS", "CS"])
    assert major_fit_score(profile, opp) == 0.0


def test_major_fit_score_empty_list_returns_half():
    profile = make_profile(major="CE")
    opp = make_opportunity(major_fit=[])
    assert major_fit_score(profile, opp) == 0.5


def test_major_fit_score_no_major_in_profile():
    profile = make_profile(major=None)
    opp = make_opportunity(major_fit=["DS"])
    assert major_fit_score(profile, opp) == 0.0


# ---------------------------------------------------------------------------
# city_match_score
# ---------------------------------------------------------------------------

def test_city_match_score_exact():
    profile = make_profile(city="Riyadh")
    opp = make_opportunity(city="Riyadh", work_mode="On-site")
    assert city_match_score(profile, opp) == 1.0


def test_city_match_score_no_match():
    profile = make_profile(city="Jeddah")
    opp = make_opportunity(city="Riyadh", work_mode="On-site")
    assert city_match_score(profile, opp) == 0.0


def test_city_match_score_remote_opportunity():
    profile = make_profile(city="Jeddah")
    opp = make_opportunity(city="Riyadh", work_mode="Remote")
    assert city_match_score(profile, opp) == 0.5


def test_city_match_score_no_preference():
    profile = make_profile(city=None)
    opp = make_opportunity(city="Riyadh", work_mode="On-site")
    assert city_match_score(profile, opp) == 0.5


# ---------------------------------------------------------------------------
# work_mode_match_score
# ---------------------------------------------------------------------------

def test_work_mode_match_exact():
    profile = make_profile(work_mode="Remote")
    opp = make_opportunity(work_mode="Remote")
    assert work_mode_match_score(profile, opp) == 1.0


def test_work_mode_match_no_match():
    profile = make_profile(work_mode="On-site")
    opp = make_opportunity(work_mode="Remote")
    assert work_mode_match_score(profile, opp) == 0.0


def test_work_mode_match_no_preference():
    profile = make_profile(work_mode=None)
    opp = make_opportunity(work_mode="Remote")
    assert work_mode_match_score(profile, opp) == 0.5


# ---------------------------------------------------------------------------
# interest_match_score
# ---------------------------------------------------------------------------

def test_interest_match_score_found_in_title():
    profile = make_profile(interest="Data Science")
    opp = make_opportunity(title="Data Science COOP Program")
    assert interest_match_score(profile, opp) == 1.0


def test_interest_match_score_not_found():
    profile = make_profile(interest="Cybersecurity")
    opp = make_opportunity(title="Data Science COOP Program")
    assert interest_match_score(profile, opp) == 0.0


def test_interest_match_score_no_interest():
    profile = make_profile(interest=None)
    opp = make_opportunity(title="Data Science COOP Program")
    assert interest_match_score(profile, opp) == 0.5


# ---------------------------------------------------------------------------
# verified_source_bonus
# ---------------------------------------------------------------------------

def test_verified_source_bonus_with_url():
    opp = make_opportunity(source_url="https://example.com")
    assert verified_source_bonus(opp) == 0.1


def test_verified_source_bonus_without_url():
    opp = make_opportunity(source_url="")
    assert verified_source_bonus(opp) == 0.0


# ---------------------------------------------------------------------------
# compute_score
# ---------------------------------------------------------------------------

def test_compute_score_perfect_match():
    profile = make_profile(
        major="DS",
        city="Riyadh",
        work_mode="Remote",
        interest="Data Science",
        program_type="COOP",
        skills=["python", "sql"],
    )

    opp = make_opportunity(
        major_fit=["DS"],
        city="Riyadh",
        work_mode="Remote",
        program_type="COOP",
        title="Data Science COOP",
        requirements="Python and SQL are required",
        skills_list=["python", "sql", "data analysis"],
        source_url="https://example.com",
    )


    score = compute_score(profile, opp)

    assert score > 0.8

def test_compute_score_poor_match():
    profile = make_profile(
        major="DS",
        city="Riyadh",
        work_mode="Remote",
        interest="Data Science",
        program_type="COOP",
        skills=["python", "sql"],
    )

    opp = make_opportunity(
        major_fit=["CYS"],
        city="Jeddah",
        work_mode="On-site",
        program_type="Internship",
        title="Cybersecurity Internship",
        requirements="Networking and security knowledge required",
        skills_list=["networking", "security"],
        source_url="",
    )

    score = compute_score(profile, opp)

    assert score < 0.5


def test_compute_score_within_bounds():
    profile = make_profile()
    opp = make_opportunity()
    score = compute_score(profile, opp)
    assert 0.0 <= score <= 1.0

# ---------------------------------------------------------------------------
# program_type_match_score
# ---------------------------------------------------------------------------

def test_program_type_match_exact():
    profile = make_profile(program_type="COOP")
    opp = make_opportunity(program_type="COOP")
    assert program_type_match_score(profile, opp) == 1.0


def test_program_type_match_no_match():
    profile = make_profile(program_type="COOP")
    opp = make_opportunity(program_type="Internship")
    assert program_type_match_score(profile, opp) == 0.0


def test_program_type_match_no_preference():
    profile = make_profile(program_type=None)
    opp = make_opportunity(program_type="Internship")
    assert program_type_match_score(profile, opp) == 0.5


    # ---------------------------------------------------------------------------
# skills_match_score
# ---------------------------------------------------------------------------

def test_skills_match_score_all_skills_match():
    profile = make_profile(skills=["python", "sql"])
    opp = make_opportunity(
        title="Data Science COOP",
        requirements="Python and SQL are required",
        skills_list=["python", "sql", "data analysis"],
    )

    assert skills_match_score(profile, opp) == 1.0


def test_skills_match_score_partial_match():
    profile = make_profile(skills=["python", "sql"])
    opp = make_opportunity(
        title="Data Science COOP",
        requirements="Python is required",
        skills_list=["python"],
    )

    assert skills_match_score(profile, opp) == 0.5


def test_skills_match_score_no_match():
    profile = make_profile(skills=["python", "sql"])
    opp = make_opportunity(
        title="Cybersecurity Internship",
        requirements="Networking knowledge is required",
        skills_list=["networking"],
    )

    assert skills_match_score(profile, opp) == 0.0


def test_skills_match_score_no_student_skills():
    profile = make_profile(skills=[])
    opp = make_opportunity(
        title="Data Science COOP",
        requirements="Python and SQL are required",
        skills_list=["python", "sql"],
    )

    assert skills_match_score(profile, opp) == 0.5

def test_program_type_match_coop_with_mixed_type():
    profile = make_profile(program_type="COOP")
    opp = make_opportunity(program_type="COOP/Internship")

    assert program_type_match_score(profile, opp) == 1.0


def test_program_type_match_internship_with_mixed_type():
    profile = make_profile(program_type="Internship")
    opp = make_opportunity(program_type="COOP/Internship")

    assert program_type_match_score(profile, opp) == 1.0


def test_program_type_match_training_partial_match_for_coop():
    profile = make_profile(program_type="COOP")
    opp = make_opportunity(program_type="Training")

    assert program_type_match_score(profile, opp) == 0.5


def test_program_type_match_graduate_program_no_match_for_coop():
    profile = make_profile(program_type="COOP")
    opp = make_opportunity(program_type="Graduate Program")

    assert program_type_match_score(profile, opp) == 0.0

def test_work_mode_on_site_matches_in_person():
    profile = make_profile(work_mode="On-site")
    opp = make_opportunity(work_mode="In person")

    assert work_mode_match_score(profile, opp) == 1.0


def test_work_mode_on_site_matches_onsite():
    profile = make_profile(work_mode="On-site")
    opp = make_opportunity(work_mode="Onsite")

    assert work_mode_match_score(profile, opp) == 1.0


def test_work_mode_remote_matches_hybrid_partially():
    profile = make_profile(work_mode="Remote")
    opp = make_opportunity(work_mode="Hybrid")

    assert work_mode_match_score(profile, opp) == 0.7


def test_work_mode_hybrid_matches_remote_partially():
    profile = make_profile(work_mode="Hybrid")
    opp = make_opportunity(work_mode="Remote")

    assert work_mode_match_score(profile, opp) == 0.7


def test_work_mode_not_stated_gets_small_score():
    profile = make_profile(work_mode="Remote")
    opp = make_opportunity(work_mode="Not stated")

    assert work_mode_match_score(profile, opp) == 0.3

def test_city_match_same_eastern_province_cluster():
    profile = make_profile(city="Dammam")
    opp = make_opportunity(city="Dhahran")

    assert city_match_score(profile, opp) == 0.7


def test_city_match_flexible_saudi_arabia():
    profile = make_profile(city="Jeddah")
    opp = make_opportunity(city="Saudi Arabia")

    assert city_match_score(profile, opp) == 0.5


def test_city_match_flexible_multiple():
    profile = make_profile(city="Riyadh")
    opp = make_opportunity(city="Multiple")

    assert city_match_score(profile, opp) == 0.5


def test_city_match_not_stated_small_score():
    profile = make_profile(city="Riyadh")
    opp = make_opportunity(city="Not stated")

    assert city_match_score(profile, opp) == 0.3


def test_city_match_preferred_beats_acceptable():
    profile = make_profile(
        city="Khobar",
        home_city="Khobar",
        preferred_locations=["Khobar"],
        acceptable_locations=["Riyadh"],
    )
    preferred_opp = make_opportunity(city="Khobar", work_mode="On-site")
    acceptable_opp = make_opportunity(city="Riyadh", work_mode="On-site")
    assert city_match_score(profile, preferred_opp) > city_match_score(
        profile, acceptable_opp
    )
    assert city_match_score(profile, preferred_opp) == 1.0
    assert city_match_score(profile, acceptable_opp) == 0.85


def test_city_match_acceptable_above_no_match():
    profile = make_profile(
        city="Khobar",
        acceptable_locations=["Riyadh"],
    )
    acceptable_opp = make_opportunity(city="Riyadh", work_mode="On-site")
    no_match_opp = make_opportunity(city="Abha", work_mode="On-site")
    assert city_match_score(profile, acceptable_opp) > city_match_score(
        profile, no_match_opp
    )
    assert city_match_score(profile, no_match_opp) == 0.0


def test_city_match_eastern_cluster_partial():
    profile = make_profile(city="Dammam", home_city="Dammam")
    opp = make_opportunity(city="Dhahran", work_mode="On-site")
    assert city_match_score(profile, opp) == 0.7


def test_recommendations_sorted_by_match_score_rubric():
    from app.recommender import recommend

    profile = ParsedProfile(
        major="CS",
        city="Khobar",
        home_city="Khobar",
        preferred_locations=["Khobar"],
        acceptable_locations=["Riyadh", "Jeddah"],
        location_flexibility="flexible",
        interest="Software Development",
        program_type="COOP",
    )
    results = recommend(profile, top_n=5)
    assert len(results) > 0
    scores = [r.match_score for r in results]
    assert scores == sorted(scores, reverse=True)
    for opp in results:
        assert 0 <= opp.match_score <= 100
        assert opp.score_source == "rubric"