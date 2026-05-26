"""
train_fair_regression_model.py – Fair regression evaluation without rubric leakage.

Trains on profile/opportunity text and categorical fields only. Does NOT use
rubric component score columns that were used to construct target_score.

Run from the backend directory:
    python -m app.train_fair_regression_model

Outputs:
    models/regression_text_only_ridge.joblib
    models/regression_text_only_random_forest.joblib
    models/regression_text_only_gradient_boosting.joblib
    data/processed/fair_regression_model_metrics.csv
    data/processed/fair_regression_predictions.csv
    reports/figures/fair_regression_prediction_vs_actual.png
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.train_regression_model import (
    COMBINED_TEXT_COLUMN,
    DATASET_FILE,
    GROUP_COLUMN,
    NUMERIC_COMPONENT_COLUMNS,
    TARGET_COLUMN,
    clip_predictions,
    group_train_test_split,
    load_regression_dataset,
    precision_at_k,
    regression_metrics,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
MODELS_DIR = REPO_ROOT / "models"
FIGURES_DIR = REPO_ROOT / "reports" / "figures"

FAIR_METRICS_FILE = PROCESSED_DIR / "fair_regression_model_metrics.csv"
FAIR_PREDICTIONS_FILE = PROCESSED_DIR / "fair_regression_predictions.csv"
FAIR_FIGURE_FILE = FIGURES_DIR / "fair_regression_prediction_vs_actual.png"
RUBRIC_METRICS_FILE = PROCESSED_DIR / "regression_model_metrics.csv"

RIDGE_MODEL_FILE = MODELS_DIR / "regression_text_only_ridge.joblib"
RANDOM_FOREST_MODEL_FILE = MODELS_DIR / "regression_text_only_random_forest.joblib"
GRADIENT_BOOSTING_MODEL_FILE = MODELS_DIR / "regression_text_only_gradient_boosting.joblib"

RANDOM_STATE = 42

# Rubric columns must never appear as model inputs
EXCLUDED_RUBRIC_COLUMNS: List[str] = list(NUMERIC_COMPONENT_COLUMNS)

FAIR_TEXT_COLUMNS: List[str] = [
    "chat_message",
    "major",
    "university",
    "city",
    "preferred_locations",
    "skills",
    "qualifications",
    "interest",
    "program_type",
    "work_mode",
    "preferred_roles",
    "interview_preference",
    "company_name",
    "program_name",
    "opportunity_city",
    "opportunity_program_type",
    "opportunity_work_mode",
    "opportunity_skills",
    "opportunity_requirements",
    "opportunity_role_cluster",
    "interview_required",
    "source_url",
    "verified_opportunity",
]

CATEGORICAL_COLUMNS: List[str] = [
    "major",
    "city",
    "program_type",
    "work_mode",
    "opportunity_program_type",
    "opportunity_work_mode",
    "opportunity_role_cluster",
]

COUNT_FEATURE_COLUMNS: List[str] = [
    "text_length",
    "skill_token_count",
    "qualification_token_count",
    "preferred_role_count",
    "preferred_location_count",
]

FAIR_REQUIRED_COLUMNS: List[str] = (
    [GROUP_COLUMN, TARGET_COLUMN, "opportunity_id", "company_name", "program_name"]
    + FAIR_TEXT_COLUMNS
    + EXCLUDED_RUBRIC_COLUMNS
)


# ---------------------------------------------------------------------------
# Fair feature engineering
# ---------------------------------------------------------------------------

def _safe_str(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _count_semicolon_items(value: object) -> int:
    text = _safe_str(value)
    if not text:
        return 0
    return len([part for part in text.split(";") if part.strip()])


def build_fair_combined_text(row: pd.Series) -> str:
    """Concatenate fair text fields only (no rubric component columns)."""
    parts = [_safe_str(row.get(column, "")) for column in FAIR_TEXT_COLUMNS]
    return " ".join(part for part in parts if part)


def build_fair_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Build fair features; rubric score columns are not added or used."""
    features = df.copy()
    features[COMBINED_TEXT_COLUMN] = features.apply(build_fair_combined_text, axis=1)
    features["text_length"] = features[COMBINED_TEXT_COLUMN].str.len()
    features["skill_token_count"] = features["skills"].map(_count_semicolon_items)
    features["qualification_token_count"] = features["qualifications"].map(
        _count_semicolon_items
    )
    features["preferred_role_count"] = features["preferred_roles"].map(
        _count_semicolon_items
    )
    features["preferred_location_count"] = features["preferred_locations"].map(
        _count_semicolon_items
    )

    for column in CATEGORICAL_COLUMNS:
        features[column] = features[column].fillna("").astype(str).replace("", "unknown")

    if "verified_opportunity" in features.columns:
        features["verified_opportunity"] = (
            features["verified_opportunity"].fillna(False).astype(str).str.lower()
        )

    return features


def get_fair_model_input_columns(model_kind: str) -> List[str]:
    """Return column names passed to a fair model pipeline (for tests/validation)."""
    if model_kind == "ridge":
        return [COMBINED_TEXT_COLUMN]
    if model_kind == "random_forest":
        return [COMBINED_TEXT_COLUMN, *CATEGORICAL_COLUMNS, *COUNT_FEATURE_COLUMNS]
    if model_kind == "gradient_boosting":
        return [*CATEGORICAL_COLUMNS, *COUNT_FEATURE_COLUMNS]
    raise ValueError(f"Unknown model_kind: {model_kind}")


def assert_no_rubric_features(feature_columns: Sequence[str]) -> None:
    """Ensure rubric leakage columns are not used as inputs."""
    overlap = set(feature_columns) & set(EXCLUDED_RUBRIC_COLUMNS)
    if overlap:
        raise ValueError(f"Rubric component columns must not be features: {sorted(overlap)}")


# ---------------------------------------------------------------------------
# Model builders (no rubric numeric columns)
# ---------------------------------------------------------------------------

def build_text_only_ridge_pipeline() -> Pipeline:
    """TF-IDF on combined_text → Ridge."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), max_features=4000),
            ),
            ("regressor", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        ]
    )


def build_text_categorical_rf_pipeline() -> Pipeline:
    """TF-IDF + one-hot categoricals + count features → Random Forest."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), max_features=2500),
                COMBINED_TEXT_COLUMN,
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", max_categories=25),
                CATEGORICAL_COLUMNS,
            ),
            ("counts", "passthrough", COUNT_FEATURE_COLUMNS),
        ],
        sparse_threshold=0.3,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=120,
                    max_depth=14,
                    min_samples_leaf=2,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def build_engineered_gb_pipeline() -> Pipeline:
    """One-hot categoricals + count features → Gradient Boosting (dense only)."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", max_categories=25),
                CATEGORICAL_COLUMNS,
            ),
            ("counts", "passthrough", COUNT_FEATURE_COLUMNS),
        ],
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                GradientBoostingRegressor(
                    random_state=RANDOM_STATE,
                    n_estimators=150,
                    max_depth=4,
                    learning_rate=0.08,
                ),
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Training / evaluation
# ---------------------------------------------------------------------------

def _feature_matrix(pipeline: Pipeline, frame: pd.DataFrame):
    """Select input columns for a fair pipeline (Series for text-only Ridge)."""
    if "tfidf" in pipeline.named_steps and "preprocessor" not in pipeline.named_steps:
        return frame[COMBINED_TEXT_COLUMN]
    if "preprocessor" in pipeline.named_steps:
        preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
        columns: List[str] = []
        for _name, _transformer, cols in preprocessor.transformers:
            if isinstance(cols, str):
                columns.append(cols)
            else:
                columns.extend(list(cols))
        return frame[columns]
    raise ValueError("Unrecognized fair pipeline structure.")


def evaluate_fair_model(
    model_name: str,
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Fit fair pipeline and return metrics plus test predictions."""
    model_kind = model_name.replace("text_only_", "")
    assert_no_rubric_features(get_fair_model_input_columns(model_kind))

    train_features = build_fair_feature_frame(train_df)
    test_features = build_fair_feature_frame(test_df)

    x_train = _feature_matrix(pipeline, train_features)
    x_test = _feature_matrix(pipeline, test_features)
    if isinstance(x_train, pd.DataFrame):
        assert_no_rubric_features(x_train.columns)

    y_train = train_features[TARGET_COLUMN].to_numpy(dtype=float)
    y_test = test_features[TARGET_COLUMN].to_numpy(dtype=float)

    pipeline.fit(x_train, y_train)
    y_pred = clip_predictions(pipeline.predict(x_test))

    metrics = regression_metrics(y_test, y_pred)
    ranking_frame = test_features[
        [GROUP_COLUMN, "opportunity_id", "company_name", "program_name", TARGET_COLUMN]
    ].copy()
    ranking_frame["predicted_score"] = y_pred
    metrics.update(precision_at_k(ranking_frame))
    metrics["model_name"] = model_name
    metrics["feature_strategy"] = "text_and_categorical_no_rubric"
    metrics["train_rows"] = float(len(train_df))
    metrics["test_rows"] = float(len(test_df))

    predictions = ranking_frame.rename(columns={TARGET_COLUMN: "actual_score"})
    predictions["model_name"] = model_name
    return metrics, predictions[
        [
            GROUP_COLUMN,
            "opportunity_id",
            "company_name",
            "program_name",
            "actual_score",
            "predicted_score",
            "model_name",
        ]
    ]


def save_prediction_plot(
    predictions: pd.DataFrame,
    model_name: str,
    output_path: Path = FAIR_FIGURE_FILE,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(
        predictions["actual_score"],
        predictions["predicted_score"],
        alpha=0.35,
        s=12,
        edgecolors="none",
    )
    ax.plot([0, 100], [0, 100], "r--", linewidth=1, label="Perfect prediction")
    ax.set_xlabel("Actual target_score")
    ax.set_ylabel("Predicted score")
    ax.set_title(f"Fair regression – Actual vs Predicted ({model_name})")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_rubric_comparison(fair_metrics: pd.DataFrame) -> None:
    """Print side-by-side summary if rubric-assisted metrics file exists."""
    if not RUBRIC_METRICS_FILE.exists():
        print(
            "[train_fair_regression_model] No rubric-assisted metrics at "
            f"{RUBRIC_METRICS_FILE} — skip comparison."
        )
        return

    rubric_metrics = pd.read_csv(RUBRIC_METRICS_FILE)
    print("\n=== Comparison: rubric-assisted vs fair (no rubric features) ===")
    print(
        "Rubric-assisted models used major_fit_score … interview_score as inputs.\n"
        "Fair models use text + categoricals only — lower R² is expected and healthier.\n"
    )

    compare_cols = ["model_name", "mae", "rmse", "r2", "precision_at_5"]
    print("Rubric-assisted (previous):")
    print(rubric_metrics[compare_cols].to_string(index=False))
    print("\nFair text/profile-based (this run):")
    print(fair_metrics[compare_cols].to_string(index=False))

    rubric_best_r2 = float(rubric_metrics["r2"].max())
    fair_best_r2 = float(fair_metrics["r2"].max())
    print(
        f"\nBest R² — rubric-assisted: {rubric_best_r2:.3f} | fair: {fair_best_r2:.3f}"
    )


def train_all_fair_models(
    dataset_path: Path = DATASET_FILE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Train fair models and persist metrics, predictions, and model files."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    raw_df = load_regression_dataset(dataset_path)
    missing_fair = [c for c in FAIR_REQUIRED_COLUMNS if c not in raw_df.columns]
    if missing_fair:
        raise ValueError(f"Dataset missing columns for fair training: {missing_fair}")

    train_df, test_df = group_train_test_split(raw_df)

    print(
        f"[train_fair_regression_model] Dataset rows: {len(raw_df)} "
        f"(train={len(train_df)}, test={len(test_df)})"
    )
    print(
        f"[train_fair_regression_model] Split: GroupShuffleSplit({GROUP_COLUMN}), "
        "test_size=0.2, random_state=42"
    )
    print(
        "[train_fair_regression_model] EXCLUDED rubric features: "
        + ", ".join(EXCLUDED_RUBRIC_COLUMNS)
    )

    all_metrics: List[Dict[str, float]] = []
    all_predictions: List[pd.DataFrame] = []

    models = [
        ("text_only_ridge", build_text_only_ridge_pipeline, RIDGE_MODEL_FILE),
        ("text_only_random_forest", build_text_categorical_rf_pipeline, RANDOM_FOREST_MODEL_FILE),
        (
            "text_only_gradient_boosting",
            build_engineered_gb_pipeline,
            GRADIENT_BOOSTING_MODEL_FILE,
        ),
    ]

    for model_name, builder, model_path in models:
        print(f"[train_fair_regression_model] Training {model_name} …")
        pipeline = builder()
        metrics, predictions = evaluate_fair_model(
            model_name=model_name,
            pipeline=pipeline,
            train_df=train_df,
            test_df=test_df,
        )
        all_metrics.append(metrics)
        all_predictions.append(predictions)
        joblib.dump(pipeline, model_path)
        print(
            f"  MAE={metrics['mae']:.3f} RMSE={metrics['rmse']:.3f} "
            f"R²={metrics['r2']:.3f} Precision@5={metrics['precision_at_5']:.3f}"
        )

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df["split_method"] = f"GroupShuffleSplit({GROUP_COLUMN})"
    metrics_df["rubric_features_used"] = False
    metrics_df.to_csv(FAIR_METRICS_FILE, index=False)

    predictions_df = pd.concat(all_predictions, ignore_index=True)
    predictions_df.to_csv(FAIR_PREDICTIONS_FILE, index=False)

    best_name = metrics_df.sort_values("rmse").iloc[0]["model_name"]
    best_predictions = predictions_df[predictions_df["model_name"] == best_name]
    save_prediction_plot(best_predictions, str(best_name))

    print(f"\n[train_fair_regression_model] Metrics saved to {FAIR_METRICS_FILE}")
    print(f"[train_fair_regression_model] Predictions saved to {FAIR_PREDICTIONS_FILE}")
    print(f"[train_fair_regression_model] Figure saved to {FAIR_FIGURE_FILE}")
    print_rubric_comparison(metrics_df)

    return metrics_df, predictions_df


def main() -> None:
    train_all_fair_models()


if __name__ == "__main__":
    main()
