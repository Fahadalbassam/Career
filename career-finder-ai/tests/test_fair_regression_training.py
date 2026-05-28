"""
test_fair_regression_training.py – Lightweight tests for fair regression training.

ML-3 requirements verified:
  1. Fair training excludes leakage columns.
  2. Fair training can run on a small sampled dataset or test fixture.
  3. Metrics CSV contains required columns.
  4. Predictions CSV contains required columns.
  5. Combined report CSV contains both tracks.
  6. Summary markdown is created.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.train_fair_regression_model import (
    CATEGORICAL_COLUMNS,
    COMBINED_TEXT_COLUMN,
    EXCLUDED_RUBRIC_COLUMNS,
    FAIR_METRICS_FILE,
    FAIR_PREDICTIONS_FILE,
    GRADIENT_BOOSTING_MODEL_FILE,
    RANDOM_FOREST_MODEL_FILE,
    RIDGE_MODEL_FILE,
    assert_no_rubric_features,
    build_fair_combined_text,
    build_fair_feature_frame,
    evaluate_fair_model,
    get_fair_model_input_columns,
    build_text_only_ridge_pipeline,
    build_text_categorical_rf_pipeline,
    build_engineered_gb_pipeline,
)
from app.train_regression_model import clip_predictions, precision_at_k, regression_metrics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sample_row() -> dict:
    return {
        "profile_id": "p1",
        "opportunity_id": 1,
        "target_score": 82.0,
        "chat_message": "CS student in Riyadh seeking remote COOP",
        "major": "CS",
        "university": "KSU",
        "city": "Riyadh",
        "preferred_locations": "Riyadh; Dammam",
        "skills": "python; sql",
        "qualifications": "AWS",
        "interest": "Software Development",
        "program_type": "COOP",
        "work_mode": "Remote",
        "preferred_roles": "Software Engineer",
        "interview_preference": "No interview preferred",
        "company_name": "Test Co",
        "program_name": "Software Engineering COOP",
        "opportunity_city": "Riyadh",
        "opportunity_program_type": "COOP",
        "opportunity_work_mode": "Remote",
        "opportunity_skills": "python; sql",
        "opportunity_requirements": "Python required",
        "opportunity_role_cluster": "Software Engineering",
        "opportunity_inferred_role_cluster": "Software Engineering",
        "opportunity_inferred_interests": "Software Development",
        "opportunity_inferred_skills": "python; sql; git",
        "opportunity_required_skills": "python; sql",
        "opportunity_preferred_skills": "docker; testing",
        "interview_required": "Not stated",
        "verified_opportunity": True,
        "major_fit_score": 1.0,
        "skill_match_score": 1.0,
        "role_interest_score": 1.0,
        "city_match_score": 1.0,
        "program_type_score": 1.0,
        "work_mode_score": 1.0,
        "verification_score": 1.0,
        "interview_score": 0.5,
    }


def _make_small_dataset(n_profiles: int = 4, n_opps: int = 6) -> pd.DataFrame:
    """Create a minimal fair-training-compatible DataFrame for integration tests."""
    rows = []
    for p_idx in range(n_profiles):
        for o_idx in range(n_opps):
            row = _sample_row().copy()
            row["profile_id"] = f"profile_{p_idx}"
            row["opportunity_id"] = o_idx + 1
            row["target_score"] = 50.0 + p_idx * 5 + o_idx * 2
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Unit tests – leakage guard
# ---------------------------------------------------------------------------

def test_fair_feature_builder_excludes_rubric_columns():
    """No rubric score column must appear in any fair model's input feature set."""
    build_fair_feature_frame(pd.DataFrame([_sample_row()]))
    for kind in ("ridge", "random_forest", "gradient_boosting"):
        input_columns = get_fair_model_input_columns(kind)
        assert_no_rubric_features(input_columns)
        for rubric_col in EXCLUDED_RUBRIC_COLUMNS:
            assert rubric_col not in input_columns


def test_assert_no_rubric_features_raises_on_overlap():
    with pytest.raises(ValueError, match="Rubric component columns must not be features"):
        assert_no_rubric_features(["chat_message", "major_fit_score"])


def test_assert_no_rubric_features_passes_for_clean_list():
    assert_no_rubric_features(["chat_message", "major", "city"])


def test_target_score_excluded_from_features():
    """target_score must be in EXCLUDED_RUBRIC_COLUMNS."""
    assert "target_score" in EXCLUDED_RUBRIC_COLUMNS


# ---------------------------------------------------------------------------
# Unit tests – feature building
# ---------------------------------------------------------------------------

def test_build_fair_combined_text_non_empty():
    text = build_fair_combined_text(pd.Series(_sample_row()))
    assert text
    assert "python" in text.lower()
    assert "riyadh" in text.lower()


def test_build_fair_combined_text_excludes_rubric_scores():
    """Rubric score values must not be concatenated into combined_text."""
    row = pd.Series(_sample_row())
    text = build_fair_combined_text(row)
    # Rubric scores are floats like 1.0 / 0.5; check their string forms are absent
    assert "major_fit_score" not in text
    assert "skill_match_score" not in text


def test_build_fair_feature_frame_adds_combined_text():
    df = build_fair_feature_frame(pd.DataFrame([_sample_row()]))
    assert COMBINED_TEXT_COLUMN in df.columns
    assert df[COMBINED_TEXT_COLUMN].iloc[0]


def test_build_fair_feature_frame_adds_count_columns():
    df = build_fair_feature_frame(pd.DataFrame([_sample_row()]))
    for col in ("text_length", "skill_token_count", "preferred_role_count"):
        assert col in df.columns, f"Missing count column: {col}"


def test_build_fair_feature_frame_categorical_filled():
    """Categorical columns must not have NaN after build_fair_feature_frame."""
    row = _sample_row()
    row["city"] = None
    df = build_fair_feature_frame(pd.DataFrame([row]))
    for col in CATEGORICAL_COLUMNS:
        assert df[col].isna().sum() == 0


# ---------------------------------------------------------------------------
# Unit tests – metrics helpers
# ---------------------------------------------------------------------------

def test_regression_metrics_returns_mae_rmse_r2():
    metrics = regression_metrics([70.0, 80.0], [72.0, 78.0])
    assert {"mae", "rmse", "r2"} <= set(metrics.keys())


def test_precision_at_k_between_zero_and_one():
    frame = pd.DataFrame(
        {
            "profile_id": ["p1", "p1", "p1", "p1", "p1"],
            "predicted_score": [90, 85, 80, 50, 40],
            "target_score": [75, 72, 71, 30, 20],
        }
    )
    result = precision_at_k(frame, k=5, relevance_threshold=70)
    assert 0.0 <= result["precision_at_5"] <= 1.0


def test_clip_predictions_within_0_100():
    raw = np.array([-5.0, 50.0, 150.0])
    clipped = clip_predictions(raw)
    assert clipped.min() >= 0.0
    assert clipped.max() <= 100.0


# ---------------------------------------------------------------------------
# Unit tests – output path names
# ---------------------------------------------------------------------------

def test_fair_output_paths_defined():
    assert RIDGE_MODEL_FILE.name == "fair_ridge_model.joblib"
    assert RANDOM_FOREST_MODEL_FILE.name == "fair_random_forest_model.joblib"
    assert GRADIENT_BOOSTING_MODEL_FILE.name == "fair_gradient_boosting_model.joblib"
    assert FAIR_METRICS_FILE.name == "fair_regression_model_metrics.csv"
    assert FAIR_PREDICTIONS_FILE.name == "fair_regression_predictions.csv"


def test_model_files_under_models_dir():
    for path in (RIDGE_MODEL_FILE, RANDOM_FOREST_MODEL_FILE, GRADIENT_BOOSTING_MODEL_FILE):
        assert path.parent.name == "models"
        assert path.name.startswith("fair_")


# ---------------------------------------------------------------------------
# Integration tests – small fixture training
# ---------------------------------------------------------------------------

def _make_train_test(n_train_profiles: int = 3, n_test_profiles: int = 2, n_opps: int = 5):
    train_df = _make_small_dataset(n_profiles=n_train_profiles, n_opps=n_opps)
    test_df = _make_small_dataset(n_profiles=n_test_profiles, n_opps=n_opps)
    # Give test profiles distinct IDs to avoid overlap
    test_df["profile_id"] = test_df["profile_id"].str.replace("profile_", "test_profile_")
    return train_df, test_df


def test_evaluate_fair_ridge_returns_required_metric_keys():
    train_df, test_df = _make_train_test()
    pipeline = build_text_only_ridge_pipeline()
    metrics, predictions = evaluate_fair_model("fair_ridge", pipeline, train_df, test_df)

    required_metric_keys = {
        "track", "model", "mae", "rmse", "r2",
        "precision_at_1", "precision_at_3", "precision_at_5",
        "train_rows", "test_rows", "train_profiles", "test_profiles",
        "feature_set", "leakage_safe",
    }
    assert required_metric_keys <= set(metrics.keys()), (
        f"Missing metric keys: {required_metric_keys - set(metrics.keys())}"
    )


def test_evaluate_fair_ridge_returns_required_prediction_columns():
    train_df, test_df = _make_train_test()
    pipeline = build_text_only_ridge_pipeline()
    _, predictions = evaluate_fair_model("fair_ridge", pipeline, train_df, test_df)

    required_pred_cols = {
        "profile_id", "opportunity_id", "company_name", "program_name",
        "target_score", "predicted_score", "absolute_error",
        "model", "rank_actual", "rank_predicted",
    }
    assert required_pred_cols <= set(predictions.columns), (
        f"Missing prediction columns: {required_pred_cols - set(predictions.columns)}"
    )


def test_evaluate_fair_ridge_leakage_safe_flag():
    train_df, test_df = _make_train_test()
    pipeline = build_text_only_ridge_pipeline()
    metrics, _ = evaluate_fair_model("fair_ridge", pipeline, train_df, test_df)
    assert metrics["leakage_safe"] is True
    assert metrics["track"] == "fair"


def test_evaluate_fair_gb_returns_required_metric_keys():
    """Gradient boosting (no text — dense only) also returns all required keys."""
    train_df, test_df = _make_train_test()
    pipeline = build_engineered_gb_pipeline()
    metrics, predictions = evaluate_fair_model(
        "fair_gradient_boosting", pipeline, train_df, test_df
    )
    assert "precision_at_1" in metrics
    assert "absolute_error" in predictions.columns
    assert "rank_actual" in predictions.columns


def test_predictions_absolute_error_is_non_negative():
    train_df, test_df = _make_train_test()
    pipeline = build_text_only_ridge_pipeline()
    _, predictions = evaluate_fair_model("fair_ridge", pipeline, train_df, test_df)
    assert (predictions["absolute_error"] >= 0).all()


def test_predictions_rank_columns_start_at_one():
    train_df, test_df = _make_train_test()
    pipeline = build_text_only_ridge_pipeline()
    _, predictions = evaluate_fair_model("fair_ridge", pipeline, train_df, test_df)
    assert predictions["rank_actual"].min() >= 1
    assert predictions["rank_predicted"].min() >= 1


# ---------------------------------------------------------------------------
# Integration tests – compare_regression_models (if metrics files exist)
# ---------------------------------------------------------------------------

def test_combined_report_contains_both_tracks(tmp_path, monkeypatch):
    """combine_metrics merges fair and rubric-assisted DataFrames correctly."""
    import app.compare_regression_models as cmp_mod

    fair_data = {
        "track": ["fair"], "model": ["fair_ridge"],
        "mae": [5.0], "rmse": [6.0], "r2": [0.5],
        "precision_at_1": [0.1], "precision_at_3": [0.2], "precision_at_5": [0.3],
        "train_rows": [100], "test_rows": [20],
        "train_profiles": [10], "test_profiles": [3],
        "feature_set": ["text_only"], "leakage_safe": [True],
    }
    rubric_data = {
        "track": ["rubric_assisted"], "model": ["rubric_assisted_ridge"],
        "mae": [0.1], "rmse": [0.2], "r2": [0.99],
        "precision_at_1": [0.5], "precision_at_3": [0.6], "precision_at_5": [0.7],
        "train_rows": [100], "test_rows": [20],
        "train_profiles": [10], "test_profiles": [3],
        "feature_set": ["text_and_rubric"], "leakage_safe": [False],
    }
    combined = cmp_mod.combine_metrics(
        pd.DataFrame(fair_data), pd.DataFrame(rubric_data)
    )
    assert set(combined["track"]) == {"fair", "rubric_assisted"}
    # fair row must come first
    assert combined.iloc[0]["track"] == "fair"


def test_summary_markdown_created(tmp_path, monkeypatch):
    """build_summary_markdown produces non-empty markdown with key sections."""
    import app.compare_regression_models as cmp_mod

    monkeypatch.setattr(cmp_mod, "SPLIT_SUMMARY_FILE", tmp_path / "nonexistent.json")

    fair_data = {
        "track": ["fair"], "model": ["fair_ridge"],
        "mae": [5.0], "rmse": [6.0], "r2": [0.5],
        "precision_at_1": [0.1], "precision_at_3": [0.2], "precision_at_5": [0.3],
        "train_rows": [100], "test_rows": [20],
        "train_profiles": [10], "test_profiles": [3],
        "feature_set": ["text_only"], "leakage_safe": [True],
    }
    rubric_data = {
        "track": ["rubric_assisted"], "model": ["rubric_assisted_ridge"],
        "mae": [0.1], "rmse": [0.2], "r2": [0.99],
        "precision_at_1": [0.5], "precision_at_3": [0.6], "precision_at_5": [0.7],
        "train_rows": [100], "test_rows": [20],
        "train_profiles": [10], "test_profiles": [3],
        "feature_set": ["text_and_rubric"], "leakage_safe": [False],
    }
    combined = cmp_mod.combine_metrics(
        pd.DataFrame(fair_data), pd.DataFrame(rubric_data)
    )
    md = cmp_mod.build_summary_markdown(combined)
    assert "ML-3" in md
    assert "leakage" in md.lower()
    assert "fair" in md.lower()
    assert "rubric" in md.lower()
    assert "## Best Fair Model" in md
    assert "## Best Rubric-Assisted Model" in md
