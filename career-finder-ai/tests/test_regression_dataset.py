"""
test_regression_dataset.py – Unit tests for regression dataset scoring rubric.
"""

import pytest

from app.build_regression_dataset import (
    CSV_COLUMNS,
    build_regression_rows,
    build_synthetic_profiles,
    compute_city_match_score,
    compute_interview_score,
    compute_major_fit_score,
    compute_program_type_score,
    compute_target_score,
    infer_interview_required,
    score_profile_opportunity_pair,
)
from app.schemas import Opportunity, ParsedProfile


def make_opportunity(**kwargs) -> Opportunity:
    defaults = {
        "id": 1,
        "company": "Test Co",
        "title": "Data Science COOP",
        "city": "Riyadh",
        "work_mode": "Remote",
        "program_type": "COOP",
        "major_fit": ["DS", "CS"],
        "requirements": "Python and SQL required",
        "skills_list": ["python", "sql"],
        "source_url": "https://example.com/job",
    }
    defaults.update(kwargs)
    return Opportunity(**defaults)


def make_profile(**kwargs) -> ParsedProfile:
    defaults = {
        "major": "DS",
        "city": "Riyadh",
        "interest": "Data Science",
        "work_mode": "Remote",
        "program_type": "COOP",
        "skills": ["python", "sql"],
        "preferred_roles": ["Data Scientist"],
    }
    defaults.update(kwargs)
    return ParsedProfile(**defaults)


def test_target_score_between_0_and_100():
    scores = score_profile_opportunity_pair(make_profile(), make_opportunity())
    assert 0.0 <= scores["target_score"] <= 100.0


def test_strong_match_scores_higher_than_weak_mismatch():
    profile = make_profile(
        major="DS",
        city="Riyadh",
        work_mode="Remote",
        program_type="COOP",
        skills=["python", "sql"],
        preferred_roles=["Data Scientist"],
        interest="Data Science",
    )
    strong_opp = make_opportunity(
        title="Data Science COOP",
        city="Riyadh",
        work_mode="Remote",
        program_type="COOP",
        major_fit=["DS"],
        requirements="Python, SQL, statistics",
        skills_list=["python", "sql", "statistics"],
    )
    weak_opp = make_opportunity(
        title="Cybersecurity Internship",
        city="Jeddah",
        work_mode="On-site",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="Network security and Linux",
        skills_list=["network security", "linux"],
    )

    strong = score_profile_opportunity_pair(profile, strong_opp)["target_score"]
    weak = score_profile_opportunity_pair(profile, weak_opp)["target_score"]
    assert strong > weak


def test_program_type_coop_internship_matches_both():
    profile = make_profile(program_type="COOP")
    opp = make_opportunity(program_type="COOP/Internship")
    assert compute_program_type_score(profile, opp) == 0.9

    profile_intern = make_profile(program_type="Internship")
    assert compute_program_type_score(profile_intern, opp) == 0.9


def test_eastern_province_partial_city_match():
    profile = make_profile(city="Dammam", preferred_locations=[])
    opp = make_opportunity(city="Dhahran", work_mode="On-site")
    assert compute_city_match_score(profile, opp) == 0.7


def test_interview_preference_affects_interview_score():
    profile = make_profile(interview_preference="No interview preferred")
    opp = make_opportunity(
        requirements="Direct acceptance, no interview required",
    )
    assert infer_interview_required(opp) == "Not required"
    assert compute_interview_score(profile, opp) == 1.0

    required_opp = make_opportunity(requirements="Interview required for all applicants")
    assert compute_interview_score(profile, required_opp) == 0.2


def test_synthetic_profile_count_at_least_40():
    profiles = build_synthetic_profiles()
    assert len(profiles) >= 40


def test_build_regression_rows_has_expected_columns():
    profiles = build_synthetic_profiles()[:1]
    opportunities = [make_opportunity(id=99)]
    rows = build_regression_rows(profiles, opportunities)
    assert len(rows) == 1
    for column in CSV_COLUMNS:
        assert column in rows[0]


def test_compute_target_score_formula_weights():
    target = compute_target_score(
        major_fit_score=1.0,
        skill_match_score=1.0,
        role_interest_score=1.0,
        city_match_score=1.0,
        program_type_score=1.0,
        work_mode_score=1.0,
        verification_score=1.0,
        interview_score=1.0,
    )
    assert target == 100.0


def test_major_fit_related_major_partial_score():
    profile = make_profile(major="AI")
    opp = make_opportunity(major_fit=["DS", "CS"])
    assert compute_major_fit_score(profile, opp) == 0.6
