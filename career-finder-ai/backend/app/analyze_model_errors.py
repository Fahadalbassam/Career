"""
analyze_model_errors.py – Error analysis for the best fair regression model.

Reads:
    data/processed/fair_regression_predictions.csv
    data/processed/regression_test_split.csv
    data/processed/fair_regression_model_metrics.csv
    data/processed/regression_split_summary.json

Writes:
    data/processed/fair_model_error_analysis.csv
    data/processed/fair_model_worst_predictions.csv
    data/processed/fair_model_best_predictions.csv
    data/processed/fair_model_profile_error_summary.csv
    data/processed/fair_model_error_summary.json

Run from the backend directory:
    python -m app.analyze_model_errors
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

FAIR_PREDICTIONS_FILE = PROCESSED_DIR / "fair_regression_predictions.csv"
FAIR_METRICS_FILE = PROCESSED_DIR / "fair_regression_model_metrics.csv"
TEST_SPLIT_FILE = PROCESSED_DIR / "regression_test_split.csv"
SPLIT_SUMMARY_FILE = PROCESSED_DIR / "regression_split_summary.json"

ERROR_ANALYSIS_FILE = PROCESSED_DIR / "fair_model_error_analysis.csv"
WORST_PREDICTIONS_FILE = PROCESSED_DIR / "fair_model_worst_predictions.csv"
BEST_PREDICTIONS_FILE = PROCESSED_DIR / "fair_model_best_predictions.csv"
PROFILE_ERROR_SUMMARY_FILE = PROCESSED_DIR / "fair_model_profile_error_summary.csv"
ERROR_SUMMARY_JSON_FILE = PROCESSED_DIR / "fair_model_error_summary.json"

TOP_N = 25

CONTEXT_COLUMNS = [
    "profile_id",
    "opportunity_id",
    "chat_message",
    "major",
    "city",
    "skills",
    "interest",
    "program_type",
    "work_mode",
    "company_name",
    "program_name",
    "opportunity_role_cluster",
    "opportunity_required_skills",
    "opportunity_preferred_skills",
    "target_score",
    "predicted_score",
    "absolute_error",
]

PROFILE_SUMMARY_COLUMNS = [
    "profile_id",
    "chat_message",
    "major",
    "city",
    "skills",
    "interest",
    "row_count",
    "mean_absolute_error",
    "max_absolute_error",
    "mean_target_score",
    "mean_predicted_score",
]


def get_best_fair_model(metrics_df: pd.DataFrame) -> str:
    """Return model name with lowest MAE among fair track rows."""
    fair = metrics_df[metrics_df["track"] == "fair"] if "track" in metrics_df.columns else metrics_df
    if fair.empty:
        fair = metrics_df
    return str(fair.sort_values("mae").iloc[0]["model"])


def load_best_fair_metrics_row(metrics_df: pd.DataFrame, model: str) -> pd.Series:
    fair = metrics_df[metrics_df["track"] == "fair"] if "track" in metrics_df.columns else metrics_df
    row = fair[fair["model"] == model]
    if row.empty:
        row = metrics_df[metrics_df["model"] == model]
    if row.empty:
        raise ValueError(f"Metrics row not found for model {model!r}")
    return row.iloc[0]


def build_error_analysis_frame(
    predictions_df: pd.DataFrame,
    test_df: pd.DataFrame,
    best_model: str,
) -> pd.DataFrame:
    """Join best-model predictions with test-split context columns."""
    pred = predictions_df[predictions_df["model"] == best_model].copy()
    if pred.empty:
        raise ValueError(f"No predictions found for model {best_model!r}")

    join_keys = ["profile_id", "opportunity_id"]
    context_cols = [
        c
        for c in [
            "chat_message",
            "major",
            "city",
            "skills",
            "interest",
            "program_type",
            "work_mode",
            "company_name",
            "program_name",
            "opportunity_role_cluster",
            "opportunity_required_skills",
            "opportunity_preferred_skills",
            "target_score",
        ]
        if c in test_df.columns
    ]

    test_context = test_df[join_keys + context_cols].drop_duplicates(subset=join_keys)
    merged = pred.merge(test_context, on=join_keys, how="left", suffixes=("_pred", ""))

    if "target_score_pred" in merged.columns:
        merged["target_score"] = merged["target_score"].fillna(merged["target_score_pred"])
        merged = merged.drop(columns=["target_score_pred"])

    out_cols = [c for c in CONTEXT_COLUMNS if c in merged.columns]
    result = merged[out_cols].copy()
    result["absolute_error"] = (result["target_score"] - result["predicted_score"]).abs()
    return result.sort_values("absolute_error", ascending=False).reset_index(drop=True)


def build_profile_error_summary(error_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-profile error statistics."""
    summary = (
        error_df.groupby("profile_id", as_index=False)
        .agg(
            chat_message=("chat_message", "first"),
            major=("major", "first"),
            city=("city", "first"),
            skills=("skills", "first"),
            interest=("interest", "first"),
            row_count=("absolute_error", "size"),
            mean_absolute_error=("absolute_error", "mean"),
            max_absolute_error=("absolute_error", "max"),
            mean_target_score=("target_score", "mean"),
            mean_predicted_score=("predicted_score", "mean"),
        )
        .sort_values("mean_absolute_error", ascending=False)
        .reset_index(drop=True)
    )
    return summary[[c for c in PROFILE_SUMMARY_COLUMNS if c in summary.columns]]


def build_error_summary_json(
    best_model: str,
    metrics_row: pd.Series,
    error_df: pd.DataFrame,
    split_summary: Optional[dict],
) -> Dict[str, Any]:
    """Build JSON summary with required keys."""
    errors = error_df["absolute_error"]
    total_test_rows = int(len(error_df))
    if split_summary and "test_rows" in split_summary:
        total_test_rows = int(split_summary["test_rows"])

    return {
        "best_model": best_model,
        "mae": float(metrics_row["mae"]),
        "rmse": float(metrics_row["rmse"]),
        "r2": float(metrics_row["r2"]),
        "precision_at_1": float(metrics_row["precision_at_1"]),
        "precision_at_3": float(metrics_row["precision_at_3"]),
        "precision_at_5": float(metrics_row["precision_at_5"]),
        "total_test_rows": total_test_rows,
        "worst_error": float(errors.max()),
        "best_error": float(errors.min()),
        "mean_error": float(errors.mean()),
        "median_error": float(errors.median()),
        "profiles_analyzed": int(error_df["profile_id"].nunique()),
    }


def run_error_analysis(
    predictions_path: Path = FAIR_PREDICTIONS_FILE,
    metrics_path: Path = FAIR_METRICS_FILE,
    test_split_path: Path = TEST_SPLIT_FILE,
    split_summary_path: Path = SPLIT_SUMMARY_FILE,
    output_dir: Path = PROCESSED_DIR,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run full error analysis pipeline.

    Returns (error_analysis_df, error_summary_dict).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions_df = pd.read_csv(predictions_path)
    metrics_df = pd.read_csv(metrics_path)
    test_df = pd.read_csv(test_split_path)

    best_model = get_best_fair_model(metrics_df)
    metrics_row = load_best_fair_metrics_row(metrics_df, best_model)

    error_df = build_error_analysis_frame(predictions_df, test_df, best_model)
    profile_summary = build_profile_error_summary(error_df)

    split_summary: Optional[dict] = None
    if split_summary_path.exists():
        with open(split_summary_path, encoding="utf-8") as f:
            split_summary = json.load(f)

    summary_json = build_error_summary_json(
        best_model, metrics_row, error_df, split_summary
    )

    error_df.to_csv(output_dir / "fair_model_error_analysis.csv", index=False)
    error_df.head(TOP_N).to_csv(output_dir / "fair_model_worst_predictions.csv", index=False)
    (
        error_df.sort_values("absolute_error", ascending=True)
        .head(TOP_N)
        .to_csv(output_dir / "fair_model_best_predictions.csv", index=False)
    )
    profile_summary.to_csv(output_dir / "fair_model_profile_error_summary.csv", index=False)

    with open(output_dir / "fair_model_error_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    return error_df, summary_json


def main() -> None:
    print("[analyze_model_errors] Loading inputs …")
    error_df, summary = run_error_analysis()

    print(f"[analyze_model_errors] Best fair model: {summary['best_model']}")
    print(
        f"[analyze_model_errors] MAE={summary['mae']:.3f}, "
        f"median error={summary['median_error']:.3f}, "
        f"worst error={summary['worst_error']:.3f}"
    )
    print(f"[analyze_model_errors] Profiles analyzed: {summary['profiles_analyzed']}")
    print(f"[analyze_model_errors] Wrote {ERROR_ANALYSIS_FILE}")
    print(f"[analyze_model_errors] Wrote {WORST_PREDICTIONS_FILE}")
    print(f"[analyze_model_errors] Wrote {BEST_PREDICTIONS_FILE}")
    print(f"[analyze_model_errors] Wrote {PROFILE_ERROR_SUMMARY_FILE}")
    print(f"[analyze_model_errors] Wrote {ERROR_SUMMARY_JSON_FILE}")


if __name__ == "__main__":
    main()
