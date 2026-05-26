"""
test_regression_training.py – Lightweight tests for regression training helpers.
"""

import pandas as pd
import pytest

from app.train_regression_model import (
    COMBINED_TEXT_COLUMN,
    GRADIENT_BOOSTING_MODEL_FILE,
    METRICS_FILE,
    PREDICTIONS_FILE,
    RANDOM_FOREST_MODEL_FILE,
    RIDGE_MODEL_FILE,
    VECTORIZER_FILE,
    build_combined_text,
    build_feature_frame,
    precision_at_k,
    regression_metrics,
    validate_required_columns,
)


def _sample_row() -> dict:
    return {
        "chat_message": "CS student in Riyadh seeking remote COOP",
        "major": "CS",
        "university": "KSU",
        "city": "Riyadh",
        "preferred_locations": "Riyadh",
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
        "opportunity_requirements": "Python and SQL required",
        "opportunity_role_cluster": "Software Engineering",
        "interview_required": "Not stated",
        "profile_id": "p1",
        "opportunity_id": 1,
        "target_score": 85.0,
        "major_fit_score": 1.0,
        "skill_match_score": 1.0,
        "role_interest_score": 1.0,
        "city_match_score": 1.0,
        "program_type_score": 1.0,
        "work_mode_score": 1.0,
        "verification_score": 1.0,
        "interview_score": 0.5,
    }


def test_validate_required_columns_raises_on_missing():
    df = pd.DataFrame({"profile_id": ["a"], "target_score": [50.0]})
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_required_columns(df)


def test_validate_required_columns_passes_for_sample():
    df = pd.DataFrame([_sample_row()])
    validate_required_columns(df)


def test_build_combined_text_non_empty():
    text = build_combined_text(pd.Series(_sample_row()))
    assert text
    assert "python" in text.lower()
    assert "riyadh" in text.lower()


def test_build_feature_frame_adds_combined_text():
    df = build_feature_frame(pd.DataFrame([_sample_row()]))
    assert COMBINED_TEXT_COLUMN in df.columns
    assert df[COMBINED_TEXT_COLUMN].iloc[0]


def test_regression_metrics_returns_expected_keys():
    metrics = regression_metrics([70.0, 80.0, 90.0], [72.0, 78.0, 88.0])
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["mae"] >= 0.0
    assert metrics["rmse"] >= 0.0


def test_precision_at_k_between_zero_and_one():
    frame = pd.DataFrame(
        [
            {
                "profile_id": "p1",
                "predicted_score": 95,
                "target_score": 80,
            },
            {
                "profile_id": "p1",
                "predicted_score": 90,
                "target_score": 75,
            },
            {
                "profile_id": "p1",
                "predicted_score": 50,
                "target_score": 40,
            },
            {
                "profile_id": "p1",
                "predicted_score": 40,
                "target_score": 30,
            },
            {
                "profile_id": "p1",
                "predicted_score": 30,
                "target_score": 20,
            },
            {
                "profile_id": "p2",
                "predicted_score": 60,
                "target_score": 50,
            },
        ]
    )
    result = precision_at_k(frame, k=5, relevance_threshold=70)
    assert 0.0 <= result["precision_at_5"] <= 1.0


def test_model_output_paths_are_under_repo_models():
    for path in (
        RIDGE_MODEL_FILE,
        RANDOM_FOREST_MODEL_FILE,
        GRADIENT_BOOSTING_MODEL_FILE,
        VECTORIZER_FILE,
    ):
        assert path.name.startswith("regression_")
        assert path.parent.name == "models"

    assert METRICS_FILE.parent.name == "processed"
    assert PREDICTIONS_FILE.name == "regression_predictions.csv"
