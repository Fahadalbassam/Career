"""
test_model_error_analysis.py – Lightweight tests for ML-4 error analysis and examples.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.analyze_model_errors import (
    build_error_analysis_frame,
    build_error_summary_json,
    get_best_fair_model,
    run_error_analysis,
)
from app.generate_recommendation_examples import (
    run_generate_examples,
    select_example_profiles,
)


def _sample_metrics() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "track": "fair",
                "model": "fair_ridge",
                "mae": 10.0,
                "rmse": 12.0,
                "r2": 0.01,
                "precision_at_1": 0.2,
                "precision_at_3": 0.2,
                "precision_at_5": 0.18,
            },
            {
                "track": "fair",
                "model": "fair_gradient_boosting",
                "mae": 5.0,
                "rmse": 7.0,
                "r2": 0.65,
                "precision_at_1": 0.2,
                "precision_at_3": 0.27,
                "precision_at_5": 0.24,
            },
        ]
    )


def _sample_test_and_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    test_rows = []
    for profile_id in ("p_a", "p_b"):
        for opp_id, target in [(1, 80.0), (2, 60.0), (3, 40.0)]:
            test_rows.append(
                {
                    "profile_id": profile_id,
                    "opportunity_id": opp_id,
                    "chat_message": f"Message for {profile_id}",
                    "major": "CS",
                    "city": "Riyadh",
                    "skills": "python",
                    "interest": "Software Development",
                    "program_type": "COOP",
                    "work_mode": "Hybrid",
                    "company_name": f"Co {opp_id}",
                    "program_name": f"Prog {opp_id}",
                    "opportunity_role_cluster": "Software Engineering",
                    "opportunity_required_skills": "python",
                    "opportunity_preferred_skills": "docker",
                    "target_score": target,
                }
            )
    test_df = pd.DataFrame(test_rows)

    pred_rows = []
    for model in ("fair_ridge", "fair_gradient_boosting"):
        for profile_id in ("p_a", "p_b"):
            for opp_id, target, pred_delta in [(1, 80.0, 1.0), (2, 60.0, 5.0), (3, 40.0, 15.0)]:
                pred = target + pred_delta
                pred_rows.append(
                    {
                        "profile_id": profile_id,
                        "opportunity_id": opp_id,
                        "target_score": target,
                        "predicted_score": pred,
                        "absolute_error": abs(target - pred),
                        "model": model,
                    }
                )
    return test_df, pd.DataFrame(pred_rows)


def test_get_best_fair_model():
    metrics = _sample_metrics()
    assert get_best_fair_model(metrics) == "fair_gradient_boosting"


def test_run_error_analysis_creates_outputs(tmp_path: Path):
    test_df, pred_df = _sample_test_and_predictions()
    metrics = _sample_metrics()

    pred_path = tmp_path / "pred.csv"
    metrics_path = tmp_path / "metrics.csv"
    test_path = tmp_path / "test.csv"
    split_path = tmp_path / "split.json"

    pred_df.to_csv(pred_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    test_df.to_csv(test_path, index=False)
    split_path.write_text(
        json.dumps({"test_rows": len(test_df), "test_profiles": 2}),
        encoding="utf-8",
    )

    error_df, summary = run_error_analysis(
        predictions_path=pred_path,
        metrics_path=metrics_path,
        test_split_path=test_path,
        split_summary_path=split_path,
        output_dir=tmp_path,
    )

    assert (tmp_path / "fair_model_error_analysis.csv").exists()
    assert (tmp_path / "fair_model_worst_predictions.csv").exists()
    assert (tmp_path / "fair_model_best_predictions.csv").exists()
    assert (tmp_path / "fair_model_profile_error_summary.csv").exists()
    assert (tmp_path / "fair_model_error_summary.json").exists()

    required_keys = {
        "best_model",
        "mae",
        "rmse",
        "r2",
        "precision_at_1",
        "precision_at_3",
        "precision_at_5",
        "total_test_rows",
        "worst_error",
        "best_error",
        "mean_error",
        "median_error",
        "profiles_analyzed",
    }
    assert required_keys.issubset(summary.keys())
    assert summary["best_model"] == "fair_gradient_boosting"

    worst = pd.read_csv(tmp_path / "fair_model_worst_predictions.csv")
    best = pd.read_csv(tmp_path / "fair_model_best_predictions.csv")
    assert worst["absolute_error"].is_monotonic_decreasing
    assert best["absolute_error"].is_monotonic_increasing
    assert len(error_df) == 6


def test_generate_examples_outputs(tmp_path: Path):
    test_df, pred_df = _sample_test_and_predictions()
    metrics = _sample_metrics()

    pred_path = tmp_path / "pred.csv"
    metrics_path = tmp_path / "metrics.csv"
    test_path = tmp_path / "test.csv"
    csv_out = tmp_path / "examples.csv"
    md_out = tmp_path / "examples.md"

    pred_df.to_csv(pred_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    test_df.to_csv(test_path, index=False)

    examples_df = run_generate_examples(
        predictions_path=pred_path,
        metrics_path=metrics_path,
        test_split_path=test_path,
        error_analysis_path=None,
        examples_csv_path=csv_out,
        examples_md_path=md_out,
    )

    assert csv_out.exists()
    assert md_out.exists()
    assert examples_df["profile_id"].nunique() >= 1
    assert (examples_df.groupby("example_id").size() <= 5).all()
    md_text = md_out.read_text(encoding="utf-8")
    assert "# Representative Recommendation Examples" in md_text
    assert "Interpretation" in md_text


def test_build_error_analysis_frame_sorting():
    test_df, pred_df = _sample_test_and_predictions()
    frame = build_error_analysis_frame(pred_df, test_df, "fair_gradient_boosting")
    assert frame["absolute_error"].is_monotonic_decreasing


def test_build_error_summary_json_keys():
    test_df, pred_df = _sample_test_and_predictions()
    metrics = _sample_metrics()
    best = get_best_fair_model(metrics)
    frame = build_error_analysis_frame(pred_df, test_df, best)
    row = metrics[metrics["model"] == best].iloc[0]
    summary = build_error_summary_json(best, row, frame, {"test_rows": 6})
    assert summary["profiles_analyzed"] == 2


def test_select_example_profiles_includes_curated_when_present():
    test_df, pred_df = _sample_test_and_predictions()
    selections = select_example_profiles(test_df, None, "fair_gradient_boosting", pred_df)
    assert len(selections) >= 2
