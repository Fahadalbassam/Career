"""
generate_recommendation_examples.py – Report-ready recommendation examples.

Reads:
    data/processed/fair_regression_predictions.csv
    data/processed/regression_test_split.csv
    data/processed/fair_model_error_analysis.csv (optional)

Writes:
    data/processed/report_recommendation_examples.csv
    docs/reports/example_recommendations.md

Run from the backend directory:
    python -m app.generate_recommendation_examples
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from app.analyze_model_errors import get_best_fair_model

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DOCS_REPORTS_DIR = REPO_ROOT / "docs" / "reports"

FAIR_PREDICTIONS_FILE = PROCESSED_DIR / "fair_regression_predictions.csv"
FAIR_METRICS_FILE = PROCESSED_DIR / "fair_regression_model_metrics.csv"
TEST_SPLIT_FILE = PROCESSED_DIR / "regression_test_split.csv"
ERROR_ANALYSIS_FILE = PROCESSED_DIR / "fair_model_error_analysis.csv"

EXAMPLES_CSV_FILE = PROCESSED_DIR / "report_recommendation_examples.csv"
EXAMPLES_MD_FILE = DOCS_REPORTS_DIR / "example_recommendations.md"

TOP_K = 5

# Curated profile picks from test split (profile_id -> report theme label)
CURATED_PROFILE_THEMES: List[Tuple[str, str]] = [
    ("eastern-province-cys", "Cybersecurity / SOC (Dammam / Khobar)"),
    ("cs-iau-backend", "Software engineering / backend"),
    ("ds-scientist-jeddah", "Data science"),
    ("ds-remote-coop", "AI / machine learning"),
    ("de-cloud-dammam", "Cloud / data engineering (Dammam)"),
    ("ce-network-dhahran", "Network engineering (Dhahran)"),
]

EXAMPLE_CSV_COLUMNS = [
    "example_id",
    "theme",
    "profile_id",
    "chat_message",
    "major",
    "city",
    "skills",
    "interest",
    "program_type",
    "work_mode",
    "rank_by_target",
    "opportunity_id",
    "company_name",
    "program_name",
    "opportunity_role_cluster",
    "opportunity_required_skills",
    "opportunity_preferred_skills",
    "target_score",
    "predicted_score",
    "absolute_error",
]


@dataclass
class ExampleSelection:
    profile_id: str
    theme: str
    selection_reason: str


def _safe_str(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def load_profile_predictions(
    predictions_df: pd.DataFrame,
    test_df: pd.DataFrame,
    error_df: Optional[pd.DataFrame],
    best_model: str,
    profile_id: str,
) -> pd.DataFrame:
    """Build per-opportunity rows for one profile with top-K by target_score."""
    pred = predictions_df[
        (predictions_df["model"] == best_model)
        & (predictions_df["profile_id"] == profile_id)
    ].copy()

    join_keys = ["profile_id", "opportunity_id"]
    context_cols = [
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
    test_context = test_df[join_keys + [c for c in context_cols if c in test_df.columns]]
    test_context = test_context.drop_duplicates(subset=join_keys)

    merged = pred.merge(test_context, on=join_keys, how="left", suffixes=("_pred", ""))
    if "target_score_pred" in merged.columns:
        merged["target_score"] = merged["target_score"].fillna(merged["target_score_pred"])
        merged = merged.drop(columns=["target_score_pred"])

    merged["absolute_error"] = (merged["target_score"] - merged["predicted_score"]).abs()

    if error_df is not None and not error_df.empty:
        err_subset = error_df[error_df["profile_id"] == profile_id][
            ["opportunity_id", "absolute_error"]
        ].drop_duplicates(subset=["opportunity_id"])
        if not err_subset.empty:
            merged = merged.drop(columns=["absolute_error"], errors="ignore")
            merged = merged.merge(err_subset, on="opportunity_id", how="left")
            merged["absolute_error"] = merged["absolute_error"].fillna(
                (merged["target_score"] - merged["predicted_score"]).abs()
            )

    merged = merged.sort_values("target_score", ascending=False).reset_index(drop=True)
    merged["rank_by_target"] = range(1, len(merged) + 1)
    return merged


def select_example_profiles(
    test_df: pd.DataFrame,
    error_df: Optional[pd.DataFrame],
    best_model: str,
    predictions_df: pd.DataFrame,
) -> List[ExampleSelection]:
    """
    Pick 6–8 representative profiles: curated themes plus one strong and one weak case.
    """
    available = set(test_df["profile_id"].unique())
    selections: List[ExampleSelection] = []
    seen: set[str] = set()

    for profile_id, theme in CURATED_PROFILE_THEMES:
        if profile_id not in available or profile_id in seen:
            continue
        seen.add(profile_id)
        selections.append(
            ExampleSelection(profile_id, theme, "curated test profile theme")
        )

    # Strong prediction: profile with lowest mean absolute error
    if error_df is not None and not error_df.empty:
        profile_mae = (
            error_df.groupby("profile_id")["absolute_error"]
            .mean()
            .sort_values()
        )
        for pid in profile_mae.index:
            if pid not in seen and pid in available:
                seen.add(pid)
                selections.append(
                    ExampleSelection(pid, "Strong prediction (low error)", "lowest mean MAE on test")
                )
                break

        # Weak prediction: profile with highest mean absolute error
        for pid in profile_mae.sort_values(ascending=False).index:
            if pid not in seen and pid in available:
                seen.add(pid)
                selections.append(
                    ExampleSelection(
                        pid, "Weak prediction (high error)", "highest mean MAE on test"
                    )
                )
                break
    else:
        # Fallback: use prediction spread per profile
        pred = predictions_df[predictions_df["model"] == best_model]
        profile_mae = pred.groupby("profile_id")["absolute_error"].mean().sort_values()
        for pid in profile_mae.index:
            if pid not in seen:
                seen.add(pid)
                selections.append(
                    ExampleSelection(pid, "Strong prediction (low error)", "lowest mean MAE")
                )
                break
        for pid in profile_mae.sort_values(ascending=False).index:
            if pid not in seen:
                seen.add(pid)
                selections.append(
                    ExampleSelection(pid, "Weak prediction (high error)", "highest mean MAE")
                )
                break

    return selections[:8]


def build_examples_dataframe(
    selections: Sequence[ExampleSelection],
    predictions_df: pd.DataFrame,
    test_df: pd.DataFrame,
    error_df: Optional[pd.DataFrame],
    best_model: str,
) -> pd.DataFrame:
    """Flatten top-K opportunities per selected profile into one CSV-ready frame."""
    rows: List[dict] = []

    for ex_idx, sel in enumerate(selections, start=1):
        profile_df = load_profile_predictions(
            predictions_df, test_df, error_df, best_model, sel.profile_id
        )
        top = profile_df.head(TOP_K)
        profile_row = test_df[test_df["profile_id"] == sel.profile_id].iloc[0]

        for _, opp in top.iterrows():
            rows.append(
                {
                    "example_id": ex_idx,
                    "theme": sel.theme,
                    "profile_id": sel.profile_id,
                    "chat_message": _safe_str(profile_row.get("chat_message")),
                    "major": _safe_str(profile_row.get("major")),
                    "city": _safe_str(profile_row.get("city")),
                    "skills": _safe_str(profile_row.get("skills")),
                    "interest": _safe_str(profile_row.get("interest")),
                    "program_type": _safe_str(profile_row.get("program_type")),
                    "work_mode": _safe_str(profile_row.get("work_mode")),
                    "rank_by_target": int(opp["rank_by_target"]),
                    "opportunity_id": int(opp["opportunity_id"]),
                    "company_name": _safe_str(opp.get("company_name")),
                    "program_name": _safe_str(opp.get("program_name")),
                    "opportunity_role_cluster": _safe_str(opp.get("opportunity_role_cluster")),
                    "opportunity_required_skills": _safe_str(
                        opp.get("opportunity_required_skills")
                    ),
                    "opportunity_preferred_skills": _safe_str(
                        opp.get("opportunity_preferred_skills")
                    ),
                    "target_score": float(opp["target_score"]),
                    "predicted_score": float(opp["predicted_score"]),
                    "absolute_error": float(opp["absolute_error"]),
                }
            )

    return pd.DataFrame(rows, columns=EXAMPLE_CSV_COLUMNS)


def _interpret_example(example_rows: pd.DataFrame, theme: str) -> str:
    """Short course-report interpretation from actual row values."""
    top = example_rows.sort_values("rank_by_target").head(TOP_K)
    mean_err = top["absolute_error"].mean()
    skills = _safe_str(top.iloc[0].get("skills"))
    interest = _safe_str(top.iloc[0].get("interest"))
    city = _safe_str(top.iloc[0].get("city"))
    clusters = top["opportunity_role_cluster"].dropna().astype(str).tolist()
    cluster_hint = ", ".join(dict.fromkeys(clusters[:3])) if clusters else "mixed roles"

    closeness = (
        "close"
        if mean_err < 4
        else "moderate"
        if mean_err < 8
        else "far"
    )

    matched_parts: List[str] = []
    if skills:
        matched_parts.append(f"listed skills ({skills})")
    if interest:
        matched_parts.append(f"interest ({interest})")
    if city:
        matched_parts.append(f"location preference ({city})")
    matched = (
        "The rubric-ranked top opportunities align with "
        + (" and ".join(matched_parts) if matched_parts else "profile text fields")
        + f", surfacing clusters such as {cluster_hint}."
    )

    missing = (
        "Some top rubric picks are generic COOP listings with thin skill metadata, "
        "so the model must infer fit mainly from text rather than structured skill overlap."
    )

    prediction_note = (
        f"On this hold-out profile, fair-model predictions were {closeness} to rubric "
        f"target scores (mean absolute error ≈ {mean_err:.1f} on the top {TOP_K})."
    )

    recommender_note = (
        "This shows the honest ML track can rank plausible opportunities from profile text, "
        "but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking."
    )

    return f"- **What matched:** {matched}\n- **What was missing:** {missing}\n- **Prediction quality:** {prediction_note}\n- **Takeaway:** {recommender_note}"


def build_examples_markdown(
    examples_df: pd.DataFrame,
    best_model: str,
) -> str:
    """Generate course-report-friendly markdown."""
    lines: List[str] = []
    lines.append("# Representative Recommendation Examples (ML-4)")
    lines.append("")
    lines.append(
        f"Generated from the test split using **`{best_model}`** (best fair / leakage-safe model). "
        "Top opportunities are ordered by **rubric `target_score`** (ground-truth label for training). "
        "Predicted scores are the fair model's hold-out estimates."
    )
    lines.append("")
    lines.append(
        "> **Note:** Rubric-assisted models are not shown here — they exhibit near-perfect metrics "
        "due to target leakage and are for sanity-check only."
    )
    lines.append("")

    for example_id in sorted(examples_df["example_id"].unique()):
        block = examples_df[examples_df["example_id"] == example_id]
        theme = str(block.iloc[0]["theme"])
        profile_id = str(block.iloc[0]["profile_id"])
        chat = str(block.iloc[0]["chat_message"])

        lines.append(f"## Example {example_id}: {theme}")
        lines.append("")
        lines.append(f"- **Profile ID:** `{profile_id}`")
        lines.append(f"- **User message:** {chat}")
        lines.append("")
        lines.append("**Parsed profile**")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|---|---|")
        for field in ["major", "city", "skills", "interest", "program_type", "work_mode"]:
            val = _safe_str(block.iloc[0].get(field)) or "—"
            lines.append(f"| {field} | {val} |")
        lines.append("")
        lines.append(f"**Top {TOP_K} opportunities (by rubric target score)**")
        lines.append("")
        lines.append(
            "| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |"
        )
        lines.append("|---:|---|---|---|---:|---:|---:|")
        for _, row in block.sort_values("rank_by_target").iterrows():
            ae = float(row["absolute_error"])
            lines.append(
                f"| {int(row['rank_by_target'])} "
                f"| {row['company_name']} "
                f"| {row['program_name']} "
                f"| {row['opportunity_role_cluster'] or '—'} "
                f"| {row['target_score']:.1f} "
                f"| {row['predicted_score']:.1f} "
                f"| {ae:.1f} |"
            )
        lines.append("")
        lines.append("**Interpretation**")
        lines.append("")
        lines.append(_interpret_example(block, theme))
        lines.append("")

    return "\n".join(lines)


def run_generate_examples(
    predictions_path: Path = FAIR_PREDICTIONS_FILE,
    metrics_path: Path = FAIR_METRICS_FILE,
    test_split_path: Path = TEST_SPLIT_FILE,
    error_analysis_path: Optional[Path] = ERROR_ANALYSIS_FILE,
    examples_csv_path: Path = EXAMPLES_CSV_FILE,
    examples_md_path: Path = EXAMPLES_MD_FILE,
) -> pd.DataFrame:
    """Generate CSV + markdown report examples."""
    examples_csv_path.parent.mkdir(parents=True, exist_ok=True)
    examples_md_path.parent.mkdir(parents=True, exist_ok=True)

    predictions_df = pd.read_csv(predictions_path)
    metrics_df = pd.read_csv(metrics_path)
    test_df = pd.read_csv(test_split_path)

    best_model = get_best_fair_model(metrics_df)

    error_df: Optional[pd.DataFrame] = None
    if error_analysis_path and error_analysis_path.exists():
        error_df = pd.read_csv(error_analysis_path)

    selections = select_example_profiles(test_df, error_df, best_model, predictions_df)
    examples_df = build_examples_dataframe(
        selections, predictions_df, test_df, error_df, best_model
    )
    examples_df.to_csv(examples_csv_path, index=False)

    md = build_examples_markdown(examples_df, best_model)
    examples_md_path.write_text(md, encoding="utf-8")

    return examples_df


def main() -> None:
    print("[generate_recommendation_examples] Loading inputs …")
    examples_df = run_generate_examples()
    n_profiles = examples_df["profile_id"].nunique()
    print(
        f"[generate_recommendation_examples] Wrote {len(examples_df)} rows "
        f"for {n_profiles} profiles"
    )
    print(f"[generate_recommendation_examples] CSV: {EXAMPLES_CSV_FILE}")
    print(f"[generate_recommendation_examples] Markdown: {EXAMPLES_MD_FILE}")


if __name__ == "__main__":
    main()
