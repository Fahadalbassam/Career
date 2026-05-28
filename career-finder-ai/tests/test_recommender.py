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

def _cybersecurity_fixture_opportunities():
    """Two CYS-relevant opportunities used to isolate skills_matched wiring tests.

    Avoids coupling to the real Excel dataset (where verbatim spellings of
    'linux' and 'network security' are rare); the recommender still ranks these
    against the profile so we can assert end-to-end behavior.
    """
    return [
        Opportunity(
            id=901,
            company="Cyber Test Co",
            title="Cybersecurity Internship",
            city="Riyadh",
            work_mode="Hybrid",
            program_type="Internship",
            major_fit=["CYS", "CS", "CE"],
            requirements="Linux and network security required",
            skills_list=["linux", "network security", "soc"],
            source_url="https://example.com/cyber",
        ),
        Opportunity(
            id=902,
            company="Other Cyber Co",
            title="SOC Analyst COOP",
            city="Riyadh",
            work_mode="On-site",
            program_type="COOP",
            major_fit=["CYS"],
            requirements="Network security, incident response",
            skills_list=["network security", "incident response"],
            source_url="https://example.com/soc",
        ),
    ]


def test_recommendations_include_skill_matches(monkeypatch):
    monkeypatch.setattr(
        recommender_module,
        "load_opportunities_from_xlsx",
        _cybersecurity_fixture_opportunities,
    )

    profile = ParsedProfile(
        major="CYS",
        city="Riyadh",
        interest="Cybersecurity",
        work_mode=None,
        program_type=None,
        skills=["linux", "network security"],
    )

    results = recommender_module.recommend(profile, top_n=5)

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


def test_recommendations_explain_skill_matches(monkeypatch):
    monkeypatch.setattr(
        recommender_module,
        "load_opportunities_from_xlsx",
        _cybersecurity_fixture_opportunities,
    )

    profile = ParsedProfile(
        major="CYS",
        city="Riyadh",
        interest="Cybersecurity",
        work_mode=None,
        program_type=None,
        skills=["linux", "network security"],
    )

    results = recommender_module.recommend(profile, top_n=5)

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


# ---------------------------------------------------------------------------
# Extended response contract: match_score, score_breakdown, role_cluster,
# interview_required, missing_skills
# ---------------------------------------------------------------------------

EXPECTED_BREAKDOWN_KEYS = {
    "major_fit_score",
    "skill_match_score",
    "role_interest_score",
    "city_match_score",
    "program_type_score",
    "work_mode_score",
    "verification_score",
    "interview_score",
}

VALID_INTERVIEW_REQUIRED_VALUES = {"Required", "Not required", "Not stated"}


def _sample_recommendations():
    """Return a populated list of recommendations for shape assertions."""
    response = recommend_from_message(
        "I am a CS student in Riyadh looking for a remote COOP with Python and SQL"
    )
    assert len(response.recommendations) > 0, "Need at least one recommendation"
    return response.recommendations


def test_recommendation_has_match_score():
    for opp in _sample_recommendations():
        assert isinstance(opp.match_score, int)
        assert 0 <= opp.match_score <= 100


def test_legacy_score_still_within_zero_one_bounds():
    for opp in _sample_recommendations():
        assert isinstance(opp.score, float)
        assert 0.0 <= opp.score <= 1.0


def test_legacy_score_matches_match_score_divided_by_100():
    for opp in _sample_recommendations():
        expected = round(opp.match_score / 100.0, 4)
        assert opp.score == expected


def test_recommendation_has_score_breakdown_with_expected_keys():
    for opp in _sample_recommendations():
        assert isinstance(opp.score_breakdown, dict)
        assert set(opp.score_breakdown.keys()) == EXPECTED_BREAKDOWN_KEYS


def test_score_breakdown_values_are_within_zero_one():
    for opp in _sample_recommendations():
        for key, value in opp.score_breakdown.items():
            assert isinstance(value, float), f"{key} is not a float"
            assert 0.0 <= value <= 1.0, f"{key}={value} out of bounds"


def test_recommendation_has_non_empty_role_cluster():
    for opp in _sample_recommendations():
        assert isinstance(opp.role_cluster, str)
        assert opp.role_cluster.strip() != ""


def test_recommendation_has_valid_interview_required():
    for opp in _sample_recommendations():
        assert opp.interview_required in VALID_INTERVIEW_REQUIRED_VALUES


def test_recommendation_has_missing_skills_list():
    for opp in _sample_recommendations():
        assert isinstance(opp.missing_skills, list)
        for entry in opp.missing_skills:
            assert isinstance(entry, str)
            assert entry.strip() != ""


def test_missing_skills_excludes_student_skills():
    profile = ParsedProfile(
        major="CS",
        city="Riyadh",
        interest="Software Development",
        program_type="COOP",
        skills=["python", "sql"],
    )

    results = recommend(profile, top_n=5)
    assert len(results) > 0

    student_skills_lower = {s.strip().lower() for s in profile.skills}

    for opp in results:
        for missing in opp.missing_skills:
            assert missing.strip().lower() not in student_skills_lower


def test_missing_skills_filters_noise_tokens():
    from app.rubric import compute_missing_skills

    profile = ParsedProfile(major="CS", skills=["Python"])
    opportunity = Opportunity(
        id=999,
        company="Test Co",
        title="Test Role",
        city="Riyadh",
        work_mode="Remote",
        program_type="COOP",
        major_fit=["CS"],
        skills_list=["python", "Not stated", "", "  ", "React", "nan", "n/a", "Git"],
        source_url="https://example.com",
    )

    missing = compute_missing_skills(profile, opportunity)
    lowered = [m.lower() for m in missing]

    assert "react" in lowered
    assert "git" in lowered
    assert "python" not in lowered
    assert "not stated" not in lowered
    assert "nan" not in lowered
    assert "n/a" not in lowered
    assert "" not in lowered


def test_recommend_response_is_sorted_by_match_score_desc():
    results = _sample_recommendations()
    match_scores = [opp.match_score for opp in results]
    assert match_scores == sorted(match_scores, reverse=True)


# ---------------------------------------------------------------------------
# ML-2A: taxonomy-backed role/interest scoring
# ---------------------------------------------------------------------------

from app.rubric import compute_role_interest_score


def _security_opportunity() -> Opportunity:
    return Opportunity(
        id=701,
        company="STC",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS", "CS", "CE"],
        requirements="Network security, SOC monitoring, vulnerability assessment, Linux",
        skills_list=["network security", "soc", "vulnerability assessment", "linux"],
        source_url="https://example.com/cyber",
    )


def _generic_software_opportunity() -> Opportunity:
    return Opportunity(
        id=702,
        company="GenericSoft",
        title="Software Engineering COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CS", "CIS"],
        requirements="Backend development, APIs, databases, Java, Python",
        skills_list=["backend", "api", "databases", "java", "python"],
        source_url="https://example.com/sw",
    )


def test_cybersecurity_interest_outscores_generic_software_for_security_opp():
    """A cybersecurity-focused student should rank a security opportunity
    higher than a generic software opportunity on role/interest alone."""
    profile = ParsedProfile(
        major="CS",
        city="Riyadh",
        interest="Cybersecurity",
        skills=[],
    )

    security_score = compute_role_interest_score(profile, _security_opportunity())
    software_score = compute_role_interest_score(profile, _generic_software_opportunity())

    assert security_score > software_score
    # Direct cluster match (interest == cluster) -> full 1.0
    assert security_score >= 0.8
    # Generic software for a security student should not be over-boosted.
    assert software_score <= 0.4


def test_cloud_devops_interest_matches_cloud_opportunity_via_cluster_keywords():
    profile = ParsedProfile(
        major="CS",
        interest="Cloud / DevOps",
        preferred_roles=["Cloud / DevOps", "Infrastructure", "Platform Engineering"],
        skills=[],
    )
    cloud_opp = Opportunity(
        id=801,
        company="CloudCo",
        title="Cloud Engineer COOP",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="COOP",
        major_fit=["CS"],
        requirements="Kubernetes, Docker, AWS, CI/CD pipelines",
        skills_list=["kubernetes", "docker", "aws", "ci/cd"],
        source_url="https://example.com/cloud",
    )

    score = compute_role_interest_score(profile, cloud_opp)
    assert score >= 0.8


def test_cybersecurity_interest_partial_match_via_opportunity_skills_only(monkeypatch):
    """Opportunity whose title/cluster do not name security but whose skills
    list contains a cluster keyword should still receive a partial bump."""
    opp = Opportunity(
        id=901,
        company="GenericCo",
        title="Engineering COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CYS", "CS"],
        requirements="General engineering",
        skills_list=["incident response"],
        source_url="https://example.com/eng",
    )
    profile = ParsedProfile(
        major="CYS",
        interest="Cybersecurity",
        skills=[],
    )

    score = compute_role_interest_score(profile, opp)
    # Skills-only hit -> partial match (0.6 in the ML-2A spec).
    assert 0.55 <= score <= 0.75


# ---------------------------------------------------------------------------
# ML-2B: opportunity enrichment + inferred-skill / inferred-interest scoring
# ---------------------------------------------------------------------------

from app.opportunity_enrichment import enrich_opportunity_signals
from app.rubric import compute_skill_match_score, score_profile_opportunity_pair


def _bare_telecom_opportunity() -> Opportunity:
    """STC opportunity with intentionally weak metadata.

    The title and requirements deliberately do not name "cybersecurity",
    "network security" or "cloud" so the enrichment layer is forced to
    do the work of inferring those signals from the company name and the
    generic "network" / "infrastructure" wording.
    """
    return Opportunity(
        id=1101,
        company="STC",
        title="Engineering Trainee Program",
        city="Riyadh",
        work_mode="On-site",
        program_type="Internship",
        major_fit=["CS", "CE", "CYS"],
        requirements="Telecom network infrastructure trainee program",
        skills_list=[],
        source_url="https://stc.com.sa/careers",
    )


def _bare_data_opportunity() -> Opportunity:
    """A plain data opportunity used as a negative control for DevOps profiles."""
    return Opportunity(
        id=1102,
        company="Wakeb",
        title="Data Analytics Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["DS", "AI", "CS"],
        requirements="Data analytics and Python",
        skills_list=["python", "data analysis"],
        source_url="https://wakeb.com/careers",
    )


def _bare_cloud_devops_opportunity() -> Opportunity:
    return Opportunity(
        id=1103,
        company="CloudCo",
        title="Cloud Engineer COOP",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="COOP",
        major_fit=["CS"],
        requirements="Kubernetes, Docker, CI/CD pipelines",
        skills_list=["kubernetes", "docker", "cicd"],
        source_url="https://cloudco.example.com/careers",
    )


def test_enrich_telecom_opportunity_inferred_signals():
    """STC-style telecom opp should pick up network / security / cloud signals."""
    signals = enrich_opportunity_signals(_bare_telecom_opportunity())
    interests = signals["inferred_interests"]
    skills = signals["inferred_skills"]

    assert "Cybersecurity" in interests
    assert "Cloud / DevOps" in interests
    # Inferred skills should include at least one networking/security term.
    expected_skills = {"networking", "network security", "cybersecurity", "linux", "cloud"}
    assert expected_skills & set(skills)


def test_enrich_does_not_override_existing_role_cluster():
    opp = _bare_telecom_opportunity().model_copy(update={"role_cluster": "Data Science"})
    signals = enrich_opportunity_signals(opp)
    # role_cluster is None when the opportunity already declares one.
    assert signals["role_cluster"] is None


def test_security_profile_outscores_generic_software_via_inferred_signals():
    """A cybersecurity-focused student should still rank a security-leaning
    opportunity above a plain software opportunity even when the security
    opportunity only carries *inferred* network/security signals."""
    profile = ParsedProfile(
        major="CS",
        city="Riyadh",
        interest="Cybersecurity",
        skills=["linux", "networking"],
    )

    security_like = _bare_telecom_opportunity()
    software = Opportunity(
        id=1104,
        company="GenericSoft",
        title="Software Engineering COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CS"],
        requirements="Backend APIs and databases",
        skills_list=["java", "sql"],
        source_url="https://example.com/sw",
    )

    sec_skill = compute_skill_match_score(profile, security_like)
    sw_skill = compute_skill_match_score(profile, software)

    # security_like has no explicit linux/networking but should hit them
    # via inferred enrichment (weight 0.5 each).
    assert sec_skill > sw_skill
    assert sec_skill > 0.0


def test_devops_profile_scores_cloud_opp_above_data_opp():
    profile = ParsedProfile(
        major="CS",
        interest="Cloud / DevOps",
        preferred_roles=["Cloud / DevOps"],
        skills=["docker", "kubernetes"],
    )
    cloud = _bare_cloud_devops_opportunity()
    data = _bare_data_opportunity()

    cloud_pair = score_profile_opportunity_pair(profile, cloud)
    data_pair = score_profile_opportunity_pair(profile, data)

    assert cloud_pair["target_score"] > data_pair["target_score"]
    assert cloud_pair["role_interest_score"] >= data_pair["role_interest_score"]


def test_inferred_skills_do_not_overpower_explicit_skills():
    """A profile skill that appears explicitly in opp A should yield a higher
    skill_match_score than the same profile skill appearing only via the
    inferred enrichment in opp B."""
    explicit_opp = Opportunity(
        id=1201,
        company="ExplicitCo",
        title="Network Engineer COOP",
        city="Riyadh",
        work_mode="On-site",
        program_type="COOP",
        major_fit=["CS"],
        requirements="Network security and Linux required",
        skills_list=["network security", "linux"],
        source_url="https://example.com/explicit",
    )
    inferred_only_opp = _bare_telecom_opportunity()

    profile = ParsedProfile(
        major="CS",
        skills=["network security", "linux"],
    )

    explicit_score = compute_skill_match_score(profile, explicit_opp)
    inferred_score = compute_skill_match_score(profile, inferred_only_opp)

    # Explicit > inferred. Per-token weight is 1.0 vs 0.5.
    assert explicit_score == 1.0
    assert inferred_score < explicit_score
    assert inferred_score > 0.0


# ---------------------------------------------------------------------------
# ML-2B.1: required vs preferred role-skill profile enrichment
# ---------------------------------------------------------------------------

from app.opportunity_enrichment import ROLE_SKILL_PROFILES
from app.rubric import (
    compute_missing_preferred_skills,
    compute_missing_required_skills,
    compute_missing_skills,
)


def test_ml2b1_cybersecurity_profile_shape():
    """Cybersecurity profile lists Linux / networking / cybersecurity
    fundamentals as required and SIEM / SOC / penetration testing as
    preferred."""
    cyber = ROLE_SKILL_PROFILES["Cybersecurity"]
    required = {s.lower() for s in cyber["required"]}
    preferred = {s.lower() for s in cyber["preferred"]}

    assert {"linux", "networking", "cybersecurity fundamentals"}.issubset(required)
    assert {"siem", "soc", "penetration testing"}.issubset(preferred)


def test_ml2b1_cloud_devops_profile_shape():
    """Cloud / DevOps profile lists Linux / Docker / Git required and
    Kubernetes / CI-CD / AWS / cloud preferred."""
    cloud = ROLE_SKILL_PROFILES["Cloud / DevOps"]
    required = {s.lower() for s in cloud["required"]}
    preferred = {s.lower() for s in cloud["preferred"]}

    assert {"linux", "docker", "git"}.issubset(required)
    assert {"kubernetes", "ci/cd", "aws", "cloud"}.issubset(preferred)


def test_ml2b1_cybersecurity_opp_enrichment_carries_required_and_preferred():
    """Enrichment returns the Cybersecurity profile's required and
    preferred skills for a cybersecurity-flagged opportunity."""
    opp = Opportunity(
        id=2001,
        company="STC",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="Cybersecurity fundamentals",
        skills_list=["soc"],
        source_url="https://example.com/stc-cyber",
    )

    signals = enrich_opportunity_signals(opp)
    required = {str(s).lower() for s in signals["required_skills"]}
    preferred = {str(s).lower() for s in signals["preferred_skills"]}

    assert "linux" in required
    assert "networking" in required
    assert "cybersecurity fundamentals" in required
    assert "siem" in preferred
    assert "penetration testing" in preferred
    # preferred must never overlap with required
    assert not (preferred & required)


def test_ml2b1_cloud_opp_enrichment_carries_required_and_preferred_via_title():
    """A bare cloud opp whose title says ``Cloud Engineer`` still picks up
    the Cloud / DevOps required / preferred skills."""
    opp = Opportunity(
        id=2002,
        company="CloudCo",
        title="Cloud Engineer COOP",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="COOP",
        major_fit=["CS"],
        requirements="",
        skills_list=[],
        source_url="https://example.com/cloudco",
    )

    signals = enrich_opportunity_signals(opp)
    required = {str(s).lower() for s in signals["required_skills"]}
    preferred = {str(s).lower() for s in signals["preferred_skills"]}

    assert {"linux", "docker", "git"}.issubset(required)
    assert {"kubernetes", "ci/cd", "aws", "cloud"}.issubset(preferred)


def test_ml2b1_required_skill_weighted_higher_than_preferred_only():
    """A profile that knows ONLY a required role skill should outscore a
    profile that knows ONLY a preferred role skill against the same
    opportunity (with no explicit overlap)."""
    cyber_no_explicit_overlap = Opportunity(
        id=2003,
        company="Cyber Holdings",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="Cybersecurity role for graduates",
        skills_list=[],  # nothing explicit; everything goes through enrichment
        source_url="https://example.com/cybh",
    )

    required_only_profile = ParsedProfile(
        major="CYS",
        skills=["linux"],  # required for Cybersecurity profile
    )
    # ``firewall`` is in Network Security's *preferred* list but not in
    # any bucket's bucket-level inferred_skills pool, so it can only be
    # matched via the preferred path (0.4).
    preferred_only_profile = ParsedProfile(
        major="CYS",
        skills=["firewall"],
    )

    req_score = compute_skill_match_score(required_only_profile, cyber_no_explicit_overlap)
    pref_score = compute_skill_match_score(preferred_only_profile, cyber_no_explicit_overlap)

    # Required weight (0.7) > preferred weight (0.4).
    assert req_score > pref_score
    assert abs(req_score - 0.7) < 0.05
    assert abs(pref_score - 0.4) < 0.05


def test_ml2b1_explicit_skill_still_beats_required_inferred():
    """Even after ML-2B.1, an explicit skill list still beats an inferred
    required role skill: 1.0 > 0.7."""
    explicit_opp = Opportunity(
        id=2004,
        company="ExplicitCyber",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="Linux administration required",
        skills_list=["linux"],
        source_url="https://example.com/exp",
    )
    inferred_only_opp = Opportunity(
        id=2005,
        company="Cyber Holdings",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="Cybersecurity role for graduates",
        skills_list=[],
        source_url="https://example.com/inf",
    )

    profile = ParsedProfile(major="CYS", skills=["linux"])
    explicit_score = compute_skill_match_score(profile, explicit_opp)
    inferred_score = compute_skill_match_score(profile, inferred_only_opp)

    assert explicit_score == 1.0
    assert inferred_score < explicit_score
    assert inferred_score >= 0.65  # 0.7 inferred-required, within float tolerance


def test_ml2b1_missing_skills_ordered_required_then_preferred():
    """`missing_skills` puts required gaps before preferred gaps; the
    optional companion fields expose the split for callers that want it."""
    opp = Opportunity(
        id=2006,
        company="Cyber Holdings",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="",
        skills_list=[],
        source_url="https://example.com/cybh2",
    )

    profile = ParsedProfile(major="CYS", skills=[])

    required_missing = compute_missing_required_skills(profile, opp)
    preferred_missing = compute_missing_preferred_skills(profile, opp)
    combined = compute_missing_skills(profile, opp)

    assert required_missing, "expected required gaps for a cyber opp"
    assert preferred_missing, "expected preferred gaps for a cyber opp"

    # No overlap between the two companion lists.
    req_lower = {s.lower() for s in required_missing}
    pref_lower = {s.lower() for s in preferred_missing}
    assert not (req_lower & pref_lower)

    # Combined list capped at 8 and ordered required-first.
    assert len(combined) <= 8
    combined_lower = [s.lower() for s in combined]
    # The first required skill must appear before the first preferred-only
    # skill in the combined list.
    pref_only_lower = pref_lower - req_lower
    first_required_index = next(
        (i for i, s in enumerate(combined_lower) if s in req_lower), None
    )
    first_preferred_index = next(
        (i for i, s in enumerate(combined_lower) if s in pref_only_lower), None
    )
    assert first_required_index is not None
    if first_preferred_index is not None:
        assert first_required_index < first_preferred_index


def test_ml2b1_missing_skills_excludes_student_skills():
    """A student who already has ``linux`` must not see ``linux`` in any
    of the three missing-skills lists."""
    opp = Opportunity(
        id=2007,
        company="Cyber Holdings",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="",
        skills_list=["linux"],
        source_url="https://example.com/cybh3",
    )
    profile = ParsedProfile(major="CYS", skills=["linux"])

    combined = compute_missing_skills(profile, opp)
    required_missing = compute_missing_required_skills(profile, opp)
    preferred_missing = compute_missing_preferred_skills(profile, opp)

    for label, items in (
        ("missing_skills", combined),
        ("missing_required_skills", required_missing),
        ("missing_preferred_skills", preferred_missing),
    ):
        lowered = [s.lower() for s in items]
        assert "linux" not in lowered, f"linux leaked into {label}: {items}"


def test_ml2b1_recommend_populates_companion_missing_fields():
    """End-to-end: ``recommend()`` populates `missing_required_skills` and
    `missing_preferred_skills` on the returned opportunities."""
    cyber_opp = Opportunity(
        id=2008,
        company="Cyber Holdings",
        title="Cybersecurity Internship",
        city="Riyadh",
        work_mode="Hybrid",
        program_type="Internship",
        major_fit=["CYS"],
        requirements="Cybersecurity role for graduates",
        skills_list=[],
        source_url="https://example.com/cybh4",
    )

    recommender_module_local = recommender_module
    recommender_module_local_old = recommender_module_local.load_opportunities_from_xlsx

    def fake_loader():
        return [cyber_opp]

    try:
        recommender_module_local.load_opportunities_from_xlsx = fake_loader  # type: ignore[assignment]
        profile = ParsedProfile(major="CYS", skills=[])
        results = recommender_module_local.recommend(profile, top_n=5)
        assert len(results) == 1
        top = results[0]
        assert "linux" in [s.lower() for s in top.missing_required_skills]
        assert any(s.lower() == "siem" for s in top.missing_preferred_skills)
        # No overlap between required and preferred companion lists.
        req_lower = {s.lower() for s in top.missing_required_skills}
        pref_lower = {s.lower() for s in top.missing_preferred_skills}
        assert not (req_lower & pref_lower)
    finally:
        recommender_module_local.load_opportunities_from_xlsx = recommender_module_local_old  # type: ignore[assignment]


def test_recommend_from_message_alkhobar_normalises_to_khobar(monkeypatch):
    """`alkhobar` in chat text should be normalised to `Khobar` in the
    parsed profile and should match a Khobar opportunity at city_match=1.0."""

    khobar_opp = Opportunity(
        id=1001,
        company="Khobar Cyber Co",
        title="Cybersecurity Internship",
        city="Khobar",
        work_mode="On-site",
        program_type="Internship",
        major_fit=["CYS", "CS", "CE"],
        requirements="Network security, Linux",
        skills_list=["network security", "linux"],
        source_url="https://example.com/khobar-cyber",
    )

    monkeypatch.setattr(
        recommender_module,
        "load_opportunities_from_xlsx",
        lambda: [khobar_opp],
    )

    response = recommend_from_message(
        "I am a CS student in alkhobar looking for security focused opportunities"
    )

    assert response.profile.city == "Khobar"
    assert response.profile.interest == "Cybersecurity"
    assert len(response.recommendations) >= 1
    top = response.recommendations[0]
    assert top.city == "Khobar"
    assert top.score_breakdown["city_match_score"] == 1.0