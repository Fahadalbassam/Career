"""
train_fair_regression_model.py – Fair regression evaluation without rubric leakage.

Trains on profile/opportunity text and categorical fields only.  Does NOT use
rubric component score columns that were used to construct target_score.

Loads from pre-computed split files (produced by inspect_regression_split.py)
when they exist; falls back to GroupShuffleSplit when they do not.

Run from the backend directory:
    python -m app.train_fair_regression_model

Outputs:
    models/fair_ridge_model.joblib
    models/fair_random_forest_model.joblib
    models/fair_gradient_boosting_model.joblib
    data/processed/fair_regression_model_metrics.csv
    data/processed/fair_regression_predictions.csv
    reports/figures/fair_regression_prediction_vs_actual.png
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import joblib
import matplotlib
matplotlib.use("Agg")
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
DOCS_REPORTS_DIR = REPO_ROOT / "docs" / "reports"

TRAIN_SPLIT_FILE = PROCESSED_DIR / "regression_train_split.csv"
TEST_SPLIT_FILE = PROCESSED_DIR / "regression_test_split.csv"

FAIR_METRICS_FILE = PROCESSED_DIR / "fair_regression_model_metrics.csv"
FAIR_PREDICTIONS_FILE = PROCESSED_DIR / "fair_regression_predictions.csv"
FAIR_FIGURE_FILE = FIGURES_DIR / "fair_regression_prediction_vs_actual.png"

RIDGE_MODEL_FILE = MODELS_DIR / "fair_ridge_model.joblib"
RANDOM_FOREST_MODEL_FILE = MODELS_DIR / "fair_random_forest_model.joblib"
GRADIENT_BOOSTING_MODEL_FILE = MODELS_DIR / "fair_gradient_boosting_model.joblib"

RANDOM_STATE = 42
RELEVANCE_THRESHOLD = 70.0
TRACK_LABEL = "fair"

# Rubric columns must never appear as model inputs
EXCLUDED_RUBRIC_COLUMNS: List[str] = list(NUMERIC_COMPONENT_COLUMNS) + [TARGET_COLUMN]

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
    "opportunity_inferred_role_cluster",
    "opportunity_inferred_interests",
    "opportunity_inferred_skills",
    "opportunity_required_skills",
    "opportunity_preferred_skills",
    "interview_required",
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


# ---------------------------------------------------------------------------
# Split file loading
# ---------------------------------------------------------------------------

def load_split_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load train/test from pre-computed split files if they exist."""
    if TRAIN_SPLIT_FILE.exists() and TEST_SPLIT_FILE.exists():
        train_df = pd.read_csv(TRAIN_SPLIT_FILE)
        test_df = pd.read_csv(TEST_SPLIT_FILE)
        print(
            f"[train_fair_regression_model] Loaded split files: "
            f"train={len(train_df)} rows / {train_df[GROUP_COLUMN].nunique()} profiles, "
            f"test={len(test_df)} rows / {test_df[GROUP_COLUMN].nunique()} profiles"
        )
        return train_df, test_df
    print(
        "[train_fair_regression_model] Split files not found — "
        "falling back to GroupShuffleSplit on full dataset."
    )
    raw_df = load_regression_dataset(DATASET_FILE)
    return group_train_test_split(raw_df)


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
# Metrics helpers
# ---------------------------------------------------------------------------

def _compute_all_precision(ranking_frame: pd.DataFrame) -> Dict[str, float]:
    """Compute precision at 1, 3, and 5 (re-uses precision_at_k with different k)."""
    result: Dict[str, float] = {}
    for k_val in (1, 3, 5):
        p = precision_at_k(
            ranking_frame,
            k=k_val,
            relevance_threshold=RELEVANCE_THRESHOLD,
        )
        result[f"precision_at_{k_val}"] = p["precision_at_5"]
    return result


def _add_rank_columns(predictions_df: pd.DataFrame) -> pd.DataFrame:
    """Add rank_actual and rank_predicted per profile (1 = best)."""
    df = predictions_df.copy()
    df["rank_actual"] = (
        df.groupby(GROUP_COLUMN)["target_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    df["rank_predicted"] = (
        df.groupby(GROUP_COLUMN)["predicted_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    return df


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
) -> Tuple[Dict, pd.DataFrame]:
    """Fit fair pipeline and return metrics plus test predictions."""
    model_kind = (
        model_name.replace("fair_", "").replace("_model", "")
    )
    # Map compound names to pipeline kind
    if model_kind in ("random_forest",):
        kind_key = "random_forest"
    elif model_kind in ("gradient_boosting",):
        kind_key = "gradient_boosting"
    else:
        kind_key = "ridge"

    assert_no_rubric_features(get_fair_model_input_columns(kind_key))

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
    ranking_frame = ranking_frame.rename(columns={TARGET_COLUMN: "actual_score"})

    # Precision at 1, 3, 5
    frame_for_precision = ranking_frame.rename(columns={"actual_score": TARGET_COLUMN})
    precision_metrics = _compute_all_precision(frame_for_precision)
    metrics.update(precision_metrics)

    # Profile counts
    train_profiles = int(train_df[GROUP_COLUMN].nunique())
    test_profiles = int(test_df[GROUP_COLUMN].nunique())

    metrics["track"] = TRACK_LABEL
    metrics["model"] = model_name
    metrics["train_rows"] = int(len(train_df))
    metrics["test_rows"] = int(len(test_df))
    metrics["train_profiles"] = train_profiles
    metrics["test_profiles"] = test_profiles
    metrics["feature_set"] = "text_and_categorical_no_rubric"
    metrics["leakage_safe"] = True

    # Build predictions frame with required columns
    preds = ranking_frame.rename(columns={"actual_score": "target_score"})
    preds["model"] = model_name
    preds["absolute_error"] = (preds["target_score"] - preds["predicted_score"]).abs()
    preds = _add_rank_columns(preds)

    predictions = preds[
        [
            GROUP_COLUMN,
            "opportunity_id",
            "company_name",
            "program_name",
            "target_score",
            "predicted_score",
            "absolute_error",
            "model",
            "rank_actual",
            "rank_predicted",
        ]
    ]
    return metrics, predictions


def save_prediction_plot(
    predictions: pd.DataFrame,
    model_name: str,
    output_path: Path = FAIR_FIGURE_FILE,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(
        predictions["target_score"],
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


def train_all_fair_models() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Train fair models and persist metrics, predictions, and model files."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    train_df, test_df = load_split_files()

    print(
        f"[train_fair_regression_model] train={len(train_df)} rows, "
        f"test={len(test_df)} rows"
    )
    print(
        "[train_fair_regression_model] EXCLUDED rubric features: "
        + ", ".join(EXCLUDED_RUBRIC_COLUMNS)
    )

    all_metrics: List[Dict] = []
    all_predictions: List[pd.DataFrame] = []

    models = [
        ("fair_ridge", build_text_only_ridge_pipeline, RIDGE_MODEL_FILE),
        ("fair_random_forest", build_text_categorical_rf_pipeline, RANDOM_FOREST_MODEL_FILE),
        ("fair_gradient_boosting", build_engineered_gb_pipeline, GRADIENT_BOOSTING_MODEL_FILE),
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
            f"  MAE={metrics['mae']:.3f}  RMSE={metrics['rmse']:.3f}  "
            f"R²={metrics['r2']:.3f}  P@1={metrics['precision_at_1']:.3f}  "
            f"P@3={metrics['precision_at_3']:.3f}  P@5={metrics['precision_at_5']:.3f}"
        )
        print(f"  Saved: {model_path}")

    # Build metrics DataFrame with canonical column order
    metrics_df = pd.DataFrame(all_metrics)[
        [
            "track", "model", "mae", "rmse", "r2",
            "precision_at_1", "precision_at_3", "precision_at_5",
            "train_rows", "test_rows", "train_profiles", "test_profiles",
            "feature_set", "leakage_safe",
        ]
    ]
    metrics_df.to_csv(FAIR_METRICS_FILE, index=False)

    predictions_df = pd.concat(all_predictions, ignore_index=True)
    predictions_df.to_csv(FAIR_PREDICTIONS_FILE, index=False)

    best_name = metrics_df.sort_values("rmse").iloc[0]["model"]
    best_predictions = predictions_df[predictions_df["model"] == best_name]
    save_prediction_plot(best_predictions, str(best_name))

    print(f"\n[train_fair_regression_model] Metrics saved to {FAIR_METRICS_FILE}")
    print(f"[train_fair_regression_model] Predictions saved to {FAIR_PREDICTIONS_FILE}")
    print(f"[train_fair_regression_model] Figure saved to {FAIR_FIGURE_FILE}")

    best_row = metrics_df.sort_values("mae").iloc[0]
    print(
        f"\n[train_fair_regression_model] Best fair model: {best_row['model']} "
        f"(MAE={best_row['mae']:.3f}, RMSE={best_row['rmse']:.3f}, R²={best_row['r2']:.3f})"
    )

    return metrics_df, predictions_df


def main() -> None:
    train_all_fair_models()


if __name__ == "__main__":
    main()
