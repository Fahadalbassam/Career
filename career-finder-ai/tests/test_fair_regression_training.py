"""
test_fair_regression_training.py – Lightweight tests for fair regression training.
"""

import numpy as np
import pandas as pd
import pytest

from app.train_fair_regression_model import (
    EXCLUDED_RUBRIC_COLUMNS,
    FAIR_METRICS_FILE,
    FAIR_PREDICTIONS_FILE,
    GRADIENT_BOOSTING_MODEL_FILE,
    RANDOM_FOREST_MODEL_FILE,
    RIDGE_MODEL_FILE,
    build_fair_combined_text,
    build_fair_feature_frame,
    get_fair_model_input_columns,
    assert_no_rubric_features,
)
from app.train_regression_model import clip_predictions, precision_at_k, regression_metrics


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
        "interview_required": "Not stated",
        "source_url": "https://example.com/job",
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


def test_fair_feature_builder_excludes_rubric_columns():
    build_fair_feature_frame(pd.DataFrame([_sample_row()]))
    for kind in ("ridge", "random_forest", "gradient_boosting"):
        input_columns = get_fair_model_input_columns(kind)
        assert_no_rubric_features(input_columns)
        for rubric_column in EXCLUDED_RUBRIC_COLUMNS:
            assert rubric_column not in input_columns


def test_build_fair_combined_text_non_empty():
    text = build_fair_combined_text(pd.Series(_sample_row()))
    assert text
    assert "python" in text.lower()
    assert "riyadh" in text.lower()


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


def test_fair_output_paths_defined():
    assert RIDGE_MODEL_FILE.name == "regression_text_only_ridge.joblib"
    assert RANDOM_FOREST_MODEL_FILE.name == "regression_text_only_random_forest.joblib"
    assert GRADIENT_BOOSTING_MODEL_FILE.name == "regression_text_only_gradient_boosting.joblib"
    assert FAIR_METRICS_FILE.name == "fair_regression_model_metrics.csv"
    assert FAIR_PREDICTIONS_FILE.name == "fair_regression_predictions.csv"


def test_clip_predictions_within_0_100():
    raw = np.array([-5.0, 50.0, 150.0])
    clipped = clip_predictions(raw)
    assert clipped.min() >= 0.0
    assert clipped.max() <= 100.0
