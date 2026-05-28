"""
test_rubric_vs_ml_comparison.py – Lightweight tests for ML-5 rubric vs ML comparison.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.compare_rubric_vs_ml import (
    COMPARISON_COLUMNS,
    build_comparison_frame,
    build_profile_overlap_frame,
    run_rubric_vs_ml_comparison,
)


def _sample_metrics() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "track": "fair",
                "model": "fair_ridge",
                "mae": 10.0,
            },
            {
                "track": "fair",
                "model": "fair_gradient_boosting",
                "mae": 5.0,
            },
        ]
    )


def _sample_test_and_predictions() -> tuple[pd.DataFrame, pd.DataFrame]:
    test_rows = []
    for profile_id in ("p_a", "p_b"):
        for opp_id, target in [(1, 90.0), (2, 70.0), (3, 50.0), (4, 30.0), (5, 10.0), (6, 5.0)]:
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
                    "target_score": target,
                }
            )
    test_df = pd.DataFrame(test_rows)

    pred_rows = []
    for model in ("fair_ridge", "fair_gradient_boosting"):
        for profile_id in ("p_a", "p_b"):
            for opp_id, target in [(1, 90.0), (2, 70.0), (3, 50.0), (4, 30.0), (5, 10.0), (6, 5.0)]:
                # Invert ranking for ML on opp 1 vs rubric to create overlap < 5
                pred = target if opp_id != 1 else (100.0 - target)
                pred_rows.append(
                    {
                        "profile_id": profile_id,
                        "opportunity_id": opp_id,
                        "company_name": f"Co {opp_id}",
                        "program_name": f"Prog {opp_id}",
                        "target_score": target,
                        "predicted_score": pred,
                        "absolute_error": abs(target - pred),
                        "model": model,
                    }
                )
    return test_df, pd.DataFrame(pred_rows)


def test_run_comparison_creates_outputs(tmp_path: Path):
    test_df, pred_df = _sample_test_and_predictions()
    metrics = _sample_metrics()

    pred_path = tmp_path / "pred.csv"
    metrics_path = tmp_path / "metrics.csv"
    test_path = tmp_path / "test.csv"
    split_path = tmp_path / "split.json"
    report_path = tmp_path / "report.md"

    pred_df.to_csv(pred_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    test_df.to_csv(test_path, index=False)
    split_path.write_text(
        json.dumps(
            {
                "split_method": "GroupShuffleSplit",
                "train_rows": 10,
                "test_rows": len(test_df),
                "overlapping_profile_ids": [],
            }
        ),
        encoding="utf-8",
    )

    _, summary = run_rubric_vs_ml_comparison(
        predictions_path=pred_path,
        metrics_path=metrics_path,
        test_split_path=test_path,
        split_summary_path=split_path,
        output_dir=tmp_path,
        report_path=report_path,
    )

    assert (tmp_path / "rubric_vs_ml_comparison.csv").exists()
    assert (tmp_path / "rubric_vs_ml_largest_disagreements.csv").exists()
    assert (tmp_path / "rubric_vs_ml_profile_overlap.csv").exists()
    assert (tmp_path / "rubric_vs_ml_summary.json").exists()
    assert report_path.exists()

    required_keys = {
        "best_model",
        "rows_compared",
        "profiles_compared",
        "mean_absolute_difference",
        "median_absolute_difference",
        "max_absolute_difference",
        "pearson_correlation",
        "spearman_correlation",
        "average_overlap_at_5",
        "split_method",
        "train_rows",
        "test_rows",
        "no_profile_overlap",
    }
    assert required_keys.issubset(summary.keys())
    assert summary["best_model"] == "fair_gradient_boosting"

    comparison = pd.read_csv(tmp_path / "rubric_vs_ml_comparison.csv")
    for col in COMPARISON_COLUMNS:
        assert col in comparison.columns

    largest = pd.read_csv(tmp_path / "rubric_vs_ml_largest_disagreements.csv")
    assert largest["absolute_difference"].is_monotonic_decreasing

    overlap = pd.read_csv(tmp_path / "rubric_vs_ml_profile_overlap.csv")
    assert (overlap["overlap_ratio_at_5"] >= 0).all()
    assert (overlap["overlap_ratio_at_5"] <= 1).all()

    md = report_path.read_text(encoding="utf-8")
    assert "# Rubric vs ML Score Comparison" in md
    assert "shadow" in md.lower()


def test_build_comparison_frame_has_difference_columns():
    test_df, pred_df = _sample_test_and_predictions()
    frame = build_comparison_frame(pred_df, test_df, "fair_gradient_boosting")
    assert "score_difference" in frame.columns
    assert "absolute_difference" in frame.columns
    assert (frame["absolute_difference"] >= 0).all()


def test_profile_overlap_counts():
    test_df, pred_df = _sample_test_and_predictions()
    frame = build_comparison_frame(pred_df, test_df, "fair_gradient_boosting")
    overlap = build_profile_overlap_frame(frame)
    assert overlap["overlap_count_at_5"].between(0, 5).all()
