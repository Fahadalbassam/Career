"""
test_regression_dataset.py – Unit tests for regression dataset scoring rubric.

Includes ML-2C tests for:
  - Enriched opportunity dataset builder
  - Train/test split inspection
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from app.build_regression_dataset import (
    CSV_COLUMNS,
    build_regression_dataset,
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


# ---------------------------------------------------------------------------
# ML-2C: Enriched opportunity dataset builder tests
# ---------------------------------------------------------------------------

ENRICHED_REQUIRED_COLUMNS = [
    "inferred_role_cluster",
    "inferred_interests",
    "inferred_skills",
    "required_skills",
    "preferred_skills",
]


def test_enriched_dataset_builder_creates_csv(tmp_path, monkeypatch):
    """enrich_opportunities_dataset.main() creates Opportunities_Enriched.csv."""
    import app.enrich_opportunities_dataset as enrich_mod

    out_file = tmp_path / "Opportunities_Enriched.csv"
    monkeypatch.setattr(enrich_mod, "OUTPUT_FILE", out_file)
    monkeypatch.setattr(enrich_mod, "PROCESSED_DIR", tmp_path)

    # build_enriched_dataframe uses load_opportunities_from_xlsx which reads the
    # real xlsx.  Use placeholder opportunities to keep the test self-contained.
    from app.recommender import PLACEHOLDER_OPPORTUNITIES

    def _fake_load_raw(xlsx_path=None):
        return pd.DataFrame(
            [
                {
                    "id": o.id,
                    "company": o.company,
                    "title": o.title,
                    "city": o.city,
                    "work_mode": o.work_mode,
                    "program_type": o.program_type,
                    "requirements": o.requirements,
                    "skills_list": "; ".join(o.skills_list),
                    "source_url": o.source_url,
                }
                for o in PLACEHOLDER_OPPORTUNITIES
            ]
        )

    def _fake_load_opps(xlsx_path=None):
        return PLACEHOLDER_OPPORTUNITIES

    monkeypatch.setattr(enrich_mod, "_load_raw_dataframe", _fake_load_raw)
    monkeypatch.setattr(enrich_mod, "load_opportunities_from_xlsx", _fake_load_opps)

    enrich_mod.main()

    assert out_file.exists(), "Opportunities_Enriched.csv was not created"


def test_enriched_dataset_has_required_columns(monkeypatch):
    """build_enriched_dataframe returns a DataFrame with all required enriched columns."""
    import app.enrich_opportunities_dataset as enrich_mod
    from app.recommender import PLACEHOLDER_OPPORTUNITIES

    def _fake_load_raw(xlsx_path=None):
        return pd.DataFrame(
            [
                {
                    "id": o.id,
                    "company": o.company,
                    "title": o.title,
                    "city": o.city,
                    "work_mode": o.work_mode,
                    "program_type": o.program_type,
                    "requirements": o.requirements,
                    "skills_list": "; ".join(o.skills_list),
                    "source_url": o.source_url,
                }
                for o in PLACEHOLDER_OPPORTUNITIES
            ]
        )

    def _fake_load_opps(xlsx_path=None):
        return PLACEHOLDER_OPPORTUNITIES

    monkeypatch.setattr(enrich_mod, "_load_raw_dataframe", _fake_load_raw)
    monkeypatch.setattr(enrich_mod, "load_opportunities_from_xlsx", _fake_load_opps)

    df = enrich_mod.build_enriched_dataframe()

    for col in ENRICHED_REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing enriched column: {col}"


# ---------------------------------------------------------------------------
# ML-2C: Regression dataset builder still runs with enriched columns
# ---------------------------------------------------------------------------

def test_regression_dataset_includes_enriched_columns():
    """build_regression_rows includes the five enriched ML-2C columns."""
    enriched_cols = [
        "opportunity_inferred_role_cluster",
        "opportunity_inferred_interests",
        "opportunity_inferred_skills",
        "opportunity_required_skills",
        "opportunity_preferred_skills",
    ]
    for col in enriched_cols:
        assert col in CSV_COLUMNS, f"Missing enriched column in CSV_COLUMNS: {col}"

    profiles = build_synthetic_profiles()[:1]
    opps = [make_opportunity(id=99)]
    rows = build_regression_rows(profiles, opps)
    assert len(rows) == 1
    for col in enriched_cols:
        assert col in rows[0], f"Enriched column missing from row: {col}"


# ---------------------------------------------------------------------------
# ML-2C: Train/test split inspection tests
# ---------------------------------------------------------------------------

def test_split_inspection_creates_output_files(tmp_path, monkeypatch):
    """compute_split() writes all four expected output files."""
    import app.inspect_regression_split as split_mod

    # Build a tiny regression dataset in tmp_path
    df = build_regression_dataset(
        profiles=build_synthetic_profiles()[:5],
        opportunities=[make_opportunity(id=i) for i in range(1, 4)],
    )
    dataset_path = tmp_path / "dataset.csv"
    df.to_csv(dataset_path, index=False)

    train_file = tmp_path / "train.csv"
    test_file = tmp_path / "test.csv"
    profile_ids_file = tmp_path / "profiles.csv"
    summary_file = tmp_path / "summary.json"

    monkeypatch.setattr(split_mod, "TRAIN_FILE", train_file)
    monkeypatch.setattr(split_mod, "TEST_FILE", test_file)
    monkeypatch.setattr(split_mod, "PROFILE_IDS_FILE", profile_ids_file)
    monkeypatch.setattr(split_mod, "SUMMARY_FILE", summary_file)
    monkeypatch.setattr(split_mod, "PROCESSED_DIR", tmp_path)

    summary = split_mod.compute_split(dataset_path=dataset_path)

    assert train_file.exists(), "regression_train_split.csv not created"
    assert test_file.exists(), "regression_test_split.csv not created"
    assert profile_ids_file.exists(), "regression_split_profile_ids.csv not created"
    assert summary_file.exists(), "regression_split_summary.json not created"


def test_split_no_profile_id_overlap(tmp_path, monkeypatch):
    """Profile IDs must not appear in both train and test sets."""
    import app.inspect_regression_split as split_mod

    df = build_regression_dataset(
        profiles=build_synthetic_profiles()[:10],
        opportunities=[make_opportunity(id=i) for i in range(1, 4)],
    )
    dataset_path = tmp_path / "dataset.csv"
    df.to_csv(dataset_path, index=False)

    monkeypatch.setattr(split_mod, "TRAIN_FILE", tmp_path / "train.csv")
    monkeypatch.setattr(split_mod, "TEST_FILE", tmp_path / "test.csv")
    monkeypatch.setattr(split_mod, "PROFILE_IDS_FILE", tmp_path / "profiles.csv")
    monkeypatch.setattr(split_mod, "SUMMARY_FILE", tmp_path / "summary.json")
    monkeypatch.setattr(split_mod, "PROCESSED_DIR", tmp_path)

    summary = split_mod.compute_split(dataset_path=dataset_path)
    assert summary["overlapping_profile_ids"] == [], (
        f"Expected no overlap, got: {summary['overlapping_profile_ids']}"
    )


def test_split_ratio_approximately_80_20(tmp_path, monkeypatch):
    """Train/test split ratio should be approximately 80/20."""
    import app.inspect_regression_split as split_mod

    df = build_regression_dataset(
        profiles=build_synthetic_profiles(),
        opportunities=[make_opportunity(id=i) for i in range(1, 4)],
    )
    dataset_path = tmp_path / "dataset.csv"
    df.to_csv(dataset_path, index=False)

    monkeypatch.setattr(split_mod, "TRAIN_FILE", tmp_path / "train.csv")
    monkeypatch.setattr(split_mod, "TEST_FILE", tmp_path / "test.csv")
    monkeypatch.setattr(split_mod, "PROFILE_IDS_FILE", tmp_path / "profiles.csv")
    monkeypatch.setattr(split_mod, "SUMMARY_FILE", tmp_path / "summary.json")
    monkeypatch.setattr(split_mod, "PROCESSED_DIR", tmp_path)

    summary = split_mod.compute_split(dataset_path=dataset_path)

    # Allow ±10% slack around target 80/20
    assert 0.70 <= summary["train_ratio"] <= 0.90, (
        f"Train ratio {summary['train_ratio']:.2%} is outside expected range 70–90%"
    )
    assert 0.10 <= summary["test_ratio"] <= 0.30, (
        f"Test ratio {summary['test_ratio']:.2%} is outside expected range 10–30%"
    )


def test_split_summary_json_has_expected_keys(tmp_path, monkeypatch):
    """regression_split_summary.json must contain all required keys."""
    import app.inspect_regression_split as split_mod

    df = build_regression_dataset(
        profiles=build_synthetic_profiles()[:5],
        opportunities=[make_opportunity(id=i) for i in range(1, 4)],
    )
    dataset_path = tmp_path / "dataset.csv"
    df.to_csv(dataset_path, index=False)

    summary_file = tmp_path / "summary.json"
    monkeypatch.setattr(split_mod, "TRAIN_FILE", tmp_path / "train.csv")
    monkeypatch.setattr(split_mod, "TEST_FILE", tmp_path / "test.csv")
    monkeypatch.setattr(split_mod, "PROFILE_IDS_FILE", tmp_path / "profiles.csv")
    monkeypatch.setattr(split_mod, "SUMMARY_FILE", summary_file)
    monkeypatch.setattr(split_mod, "PROCESSED_DIR", tmp_path)

    split_mod.compute_split(dataset_path=dataset_path)

    with open(summary_file, encoding="utf-8") as f:
        data = json.load(f)

    required_keys = [
        "total_rows",
        "train_rows",
        "test_rows",
        "train_ratio",
        "test_ratio",
        "total_profiles",
        "train_profiles",
        "test_profiles",
        "overlapping_profile_ids",
        "random_state",
        "test_size",
        "split_method",
    ]
    for key in required_keys:
        assert key in data, f"Missing key in summary JSON: {key}"
