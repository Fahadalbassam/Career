"""
compare_rubric_vs_ml.py – Compare rubric target_score vs fair ML predicted_score.

Reads:
    data/processed/fair_regression_predictions.csv
    data/processed/regression_test_split.csv
    data/processed/fair_regression_model_metrics.csv
    data/processed/regression_split_summary.json

Writes:
    data/processed/rubric_vs_ml_comparison.csv
    data/processed/rubric_vs_ml_largest_disagreements.csv
    data/processed/rubric_vs_ml_profile_overlap.csv
    data/processed/rubric_vs_ml_summary.json
    docs/reports/rubric_vs_ml_comparison.md

Run from the backend directory:
    python -m app.compare_rubric_vs_ml
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.analyze_model_errors import get_best_fair_model

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DOCS_REPORTS_DIR = REPO_ROOT / "docs" / "reports"

FAIR_PREDICTIONS_FILE = PROCESSED_DIR / "fair_regression_predictions.csv"
FAIR_METRICS_FILE = PROCESSED_DIR / "fair_regression_model_metrics.csv"
TEST_SPLIT_FILE = PROCESSED_DIR / "regression_test_split.csv"
SPLIT_SUMMARY_FILE = PROCESSED_DIR / "regression_split_summary.json"

COMPARISON_FILE = PROCESSED_DIR / "rubric_vs_ml_comparison.csv"
LARGEST_DISAGREEMENTS_FILE = PROCESSED_DIR / "rubric_vs_ml_largest_disagreements.csv"
PROFILE_OVERLAP_FILE = PROCESSED_DIR / "rubric_vs_ml_profile_overlap.csv"
SUMMARY_JSON_FILE = PROCESSED_DIR / "rubric_vs_ml_summary.json"
REPORT_MD_FILE = DOCS_REPORTS_DIR / "rubric_vs_ml_comparison.md"

TOP_K = 5
TOP_DISAGREEMENTS = 25

COMPARISON_COLUMNS = [
    "profile_id",
    "opportunity_id",
    "company_name",
    "program_name",
    "chat_message",
    "major",
    "city",
    "skills",
    "interest",
    "program_type",
    "work_mode",
    "target_score",
    "predicted_score",
    "score_difference",
    "absolute_difference",
    "rank_by_rubric",
    "rank_by_ml",
]


def spearman_correlation(x: pd.Series, y: pd.Series) -> float:
    """Rank-based correlation without scipy."""
    if len(x) < 2:
        return float("nan")
    rx = x.rank(method="average")
    ry = y.rank(method="average")
    return float(rx.corr(ry))


def build_comparison_frame(
    predictions_df: pd.DataFrame,
    test_df: pd.DataFrame,
    best_model: str,
) -> pd.DataFrame:
    """Join best-model predictions with test context and add ranks/differences."""
    pred = predictions_df[predictions_df["model"] == best_model].copy()
    if pred.empty:
        raise ValueError(f"No predictions for model {best_model!r}")

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
            "target_score",
        ]
        if c in test_df.columns
    ]

    test_context = test_df[join_keys + context_cols].drop_duplicates(subset=join_keys)
    merged = pred.merge(test_context, on=join_keys, how="left", suffixes=("_pred", ""))

    if "target_score_pred" in merged.columns:
        merged["target_score"] = merged["target_score"].fillna(merged["target_score_pred"])
        merged = merged.drop(columns=["target_score_pred"])

    merged["score_difference"] = merged["predicted_score"] - merged["target_score"]
    merged["absolute_difference"] = merged["score_difference"].abs()

    merged["rank_by_rubric"] = (
        merged.groupby("profile_id")["target_score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    merged["rank_by_ml"] = (
        merged.groupby("profile_id")["predicted_score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    out_cols = [c for c in COMPARISON_COLUMNS if c in merged.columns]
    return merged[out_cols].sort_values(
        ["profile_id", "rank_by_rubric"], ascending=[True, True]
    ).reset_index(drop=True)


def _top_k_ids(df: pd.DataFrame, score_col: str, k: int = TOP_K) -> List[int]:
    top = df.nlargest(k, score_col)
    return [int(x) for x in top["opportunity_id"].tolist()]


def build_profile_overlap_frame(comparison_df: pd.DataFrame) -> pd.DataFrame:
    """Per-profile top-5 overlap between rubric and ML rankings."""
    rows: List[dict] = []

    for profile_id, group in comparison_df.groupby("profile_id"):
        rubric_ids = _top_k_ids(group, "target_score")
        ml_ids = _top_k_ids(group, "predicted_score")
        overlap = len(set(rubric_ids) & set(ml_ids))

        rubric_companies = (
            group.nlargest(TOP_K, "target_score")["company_name"].astype(str).tolist()
        )
        ml_companies = (
            group.nlargest(TOP_K, "predicted_score")["company_name"].astype(str).tolist()
        )

        chat = group["chat_message"].iloc[0] if "chat_message" in group.columns else ""

        rows.append(
            {
                "profile_id": profile_id,
                "chat_message": chat,
                "rubric_top5_ids": ";".join(str(i) for i in rubric_ids),
                "ml_top5_ids": ";".join(str(i) for i in ml_ids),
                "overlap_count_at_5": overlap,
                "overlap_ratio_at_5": overlap / TOP_K,
                "rubric_top_company_names": "; ".join(rubric_companies),
                "ml_top_company_names": "; ".join(ml_companies),
            }
        )

    return pd.DataFrame(rows).sort_values("overlap_ratio_at_5").reset_index(drop=True)


def build_summary_json(
    comparison_df: pd.DataFrame,
    overlap_df: pd.DataFrame,
    best_model: str,
    split_summary: Optional[dict],
) -> Dict[str, Any]:
    """Aggregate comparison statistics."""
    diff = comparison_df["absolute_difference"]
    pearson = float(comparison_df["target_score"].corr(comparison_df["predicted_score"]))
    spearman = spearman_correlation(
        comparison_df["target_score"], comparison_df["predicted_score"]
    )

    summary: Dict[str, Any] = {
        "best_model": best_model,
        "rows_compared": int(len(comparison_df)),
        "profiles_compared": int(comparison_df["profile_id"].nunique()),
        "mean_absolute_difference": float(diff.mean()),
        "median_absolute_difference": float(diff.median()),
        "max_absolute_difference": float(diff.max()),
        "pearson_correlation": pearson,
        "spearman_correlation": spearman,
        "average_overlap_at_5": float(overlap_df["overlap_ratio_at_5"].mean()),
    }

    if split_summary:
        summary["split_method"] = split_summary.get("split_method", "")
        summary["train_rows"] = int(split_summary.get("train_rows", 0))
        summary["test_rows"] = int(split_summary.get("test_rows", len(comparison_df)))
        overlap_ids = split_summary.get("overlapping_profile_ids", [])
        summary["no_profile_overlap"] = len(overlap_ids) == 0
    else:
        summary["split_method"] = ""
        summary["train_rows"] = 0
        summary["test_rows"] = int(len(comparison_df))
        summary["no_profile_overlap"] = True

    return summary


def build_report_markdown(summary: Dict[str, Any]) -> str:
    """Course-report markdown for rubric vs ML comparison."""
    lines: List[str] = []
    lines.append("# Rubric vs ML Score Comparison (ML-5)")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "The live CareerFinder recommender ranks opportunities using a deterministic "
        "**rubric score** (`target_score`). ML-5 compares that score to the hold-out "
        "**fair model prediction** (`predicted_score`) from the best leakage-safe regressor "
        "to see whether ML can serve as a trustworthy **secondary** signal before any "
        "production integration."
    )
    lines.append("")
    lines.append("## Model and data")
    lines.append("")
    lines.append(f"- **Best fair model:** `{summary['best_model']}`")
    lines.append(f"- **Rows compared (test split):** {summary['rows_compared']:,}")
    lines.append(f"- **Profiles compared:** {summary['profiles_compared']}")
    lines.append(f"- **Split method:** {summary.get('split_method', 'n/a')}")
    lines.append(
        f"- **Train / test rows:** {summary.get('train_rows', 'n/a'):,} / "
        f"{summary.get('test_rows', 'n/a'):,}"
    )
    lines.append(
        f"- **No profile overlap across train/test:** "
        f"{summary.get('no_profile_overlap', True)}"
    )
    lines.append("")
    lines.append("## Score agreement")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Mean absolute difference | {summary['mean_absolute_difference']:.3f} |")
    lines.append(f"| Median absolute difference | {summary['median_absolute_difference']:.3f} |")
    lines.append(f"| Max absolute difference | {summary['max_absolute_difference']:.3f} |")
    lines.append(f"| Pearson correlation | {summary['pearson_correlation']:.3f} |")
    lines.append(f"| Spearman correlation | {summary['spearman_correlation']:.3f} |")
    lines.append(f"| Average top-5 overlap (per profile) | {summary['average_overlap_at_5']:.3f} |")
    lines.append("")
    lines.append("## What disagreement means")
    lines.append("")
    lines.append(
        "Large `absolute_difference` values mean the fair model assigns a very different "
        "numeric score than the rubric for the same profile–opportunity pair. Low "
        "**top-5 overlap** means the model would surface a different shortlist than the "
        "live recommender even when both use the same underlying opportunities."
    )
    lines.append("")
    lines.append(
        "Moderate Pearson/Spearman correlation with non-trivial MAE (~5.8 on the fair model) "
        "suggests the ML model captures broad fit patterns but does not replicate rubric "
        "weights exactly — expected because rubric component scores are excluded from fair "
        "model inputs."
    )
    lines.append("")
    lines.append("## When ML may help")
    lines.append("")
    lines.append(
        "- **Shadow scoring:** log `predicted_score` alongside rubric `match_score` to find "
        "cases where text/metadata suggests higher fit than the rubric captured."
    )
    lines.append(
        "- **Tie-breaking:** when rubric scores cluster (e.g. many COOP listings near 55–65), "
        "ML may reorder within a narrow band — only after validation."
    )
    lines.append(
        "- **Offline analysis:** largest-disagreement exports highlight opportunities to "
        "review rubric weights or enrichment quality."
    )
    lines.append("")
    lines.append("## Why rubric stays primary (for now)")
    lines.append("")
    lines.append(
        "- The rubric is **interpretable**, aligned with product copy (`score_breakdown`), "
        "and already powers `/recommend`."
    )
    lines.append(
        "- The fair model was trained to **predict** the rubric label, not user outcomes; "
        "it has not been A/B tested in production."
    )
    lines.append(
        "- Top-5 overlap is limited on a 10-profile hold-out set — not enough evidence to "
        "replace ranking."
    )
    lines.append("")
    lines.append("## Recommendation")
    lines.append("")
    lines.append(
        "1. **Use ML as a secondary / shadow score first** (e.g. optional `ml_score` in API "
        "responses behind a feature flag)."
    )
    lines.append(
        "2. **Do not replace live ranking yet** — keep sorting by rubric `match_score` until "
        "shadow logs show consistent benefit."
    )
    lines.append(
        "3. **Next engineering step:** wire shadow `ml_score` on `/recommend` without changing "
        "default sort order; compare rank deltas in logs."
    )
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("| File | Description |")
    lines.append("|---|---|")
    artifacts = [
        ("Full comparison", "data/processed/rubric_vs_ml_comparison.csv"),
        ("Largest disagreements", "data/processed/rubric_vs_ml_largest_disagreements.csv"),
        ("Per-profile top-5 overlap", "data/processed/rubric_vs_ml_profile_overlap.csv"),
        ("JSON summary", "data/processed/rubric_vs_ml_summary.json"),
    ]
    for name, path in artifacts:
        lines.append(f"| {name} | `{path}` |")
    lines.append("")

    return "\n".join(lines)


def run_rubric_vs_ml_comparison(
    predictions_path: Path = FAIR_PREDICTIONS_FILE,
    metrics_path: Path = FAIR_METRICS_FILE,
    test_split_path: Path = TEST_SPLIT_FILE,
    split_summary_path: Path = SPLIT_SUMMARY_FILE,
    output_dir: Path = PROCESSED_DIR,
    report_path: Path = REPORT_MD_FILE,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run full rubric-vs-ML comparison pipeline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    predictions_df = pd.read_csv(predictions_path)
    metrics_df = pd.read_csv(metrics_path)
    test_df = pd.read_csv(test_split_path)

    best_model = get_best_fair_model(metrics_df)
    comparison_df = build_comparison_frame(predictions_df, test_df, best_model)
    overlap_df = build_profile_overlap_frame(comparison_df)

    split_summary: Optional[dict] = None
    if split_summary_path.exists():
        with open(split_summary_path, encoding="utf-8") as f:
            split_summary = json.load(f)

    summary = build_summary_json(comparison_df, overlap_df, best_model, split_summary)

    comparison_df.to_csv(output_dir / "rubric_vs_ml_comparison.csv", index=False)
    (
        comparison_df.sort_values("absolute_difference", ascending=False)
        .head(TOP_DISAGREEMENTS)
        .to_csv(output_dir / "rubric_vs_ml_largest_disagreements.csv", index=False)
    )
    overlap_df.to_csv(output_dir / "rubric_vs_ml_profile_overlap.csv", index=False)

    with open(output_dir / "rubric_vs_ml_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    report_path.write_text(build_report_markdown(summary), encoding="utf-8")

    return comparison_df, summary


def main() -> None:
    print("[compare_rubric_vs_ml] Loading inputs …")
    _, summary = run_rubric_vs_ml_comparison()

    print(f"[compare_rubric_vs_ml] Best fair model: {summary['best_model']}")
    print(
        f"[compare_rubric_vs_ml] Mean |diff|={summary['mean_absolute_difference']:.3f}, "
        f"median={summary['median_absolute_difference']:.3f}, "
        f"max={summary['max_absolute_difference']:.3f}"
    )
    print(
        f"[compare_rubric_vs_ml] Pearson={summary['pearson_correlation']:.3f}, "
        f"Spearman={summary['spearman_correlation']:.3f}, "
        f"avg overlap@5={summary['average_overlap_at_5']:.3f}"
    )
    print(f"[compare_rubric_vs_ml] Wrote {COMPARISON_FILE}")
    print(f"[compare_rubric_vs_ml] Wrote {LARGEST_DISAGREEMENTS_FILE}")
    print(f"[compare_rubric_vs_ml] Wrote {PROFILE_OVERLAP_FILE}")
    print(f"[compare_rubric_vs_ml] Wrote {SUMMARY_JSON_FILE}")
    print(f"[compare_rubric_vs_ml] Wrote {REPORT_MD_FILE}")


if __name__ == "__main__":
    main()
