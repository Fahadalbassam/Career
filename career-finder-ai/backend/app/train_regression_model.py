"""
train_regression_model.py – Rubric-assisted regression (leakage demo / sanity check).

Uses rubric component scores (major_fit_score, skill_match_score, …) as numeric
features alongside text.  Because target_score is a linear combination of those
same component scores, metrics here are unrealistically strong and should NOT be
presented as honest model performance.

Loads from pre-computed split files (produced by inspect_regression_split.py)
when they exist; falls back to GroupShuffleSplit when they do not.

Run from the backend directory:
    python -m app.train_regression_model

Outputs:
    models/rubric_assisted_ridge_model.joblib
    models/rubric_assisted_random_forest_model.joblib
    models/rubric_assisted_gradient_boosting_model.joblib
    models/rubric_assisted_vectorizer.joblib
    data/processed/rubric_assisted_regression_model_metrics.csv
    data/processed/rubric_assisted_regression_predictions.csv
    reports/figures/rubric_assisted_regression_prediction_vs_actual.png
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
MODELS_DIR = REPO_ROOT / "models"
FIGURES_DIR = REPO_ROOT / "reports" / "figures"

DATASET_FILE = PROCESSED_DIR / "student_opportunity_regression_dataset.csv"
TRAIN_SPLIT_FILE = PROCESSED_DIR / "regression_train_split.csv"
TEST_SPLIT_FILE = PROCESSED_DIR / "regression_test_split.csv"

METRICS_FILE = PROCESSED_DIR / "rubric_assisted_regression_model_metrics.csv"
PREDICTIONS_FILE = PROCESSED_DIR / "rubric_assisted_regression_predictions.csv"
FIGURE_FILE = FIGURES_DIR / "rubric_assisted_regression_prediction_vs_actual.png"

RIDGE_MODEL_FILE = MODELS_DIR / "rubric_assisted_ridge_model.joblib"
RANDOM_FOREST_MODEL_FILE = MODELS_DIR / "rubric_assisted_random_forest_model.joblib"
GRADIENT_BOOSTING_MODEL_FILE = MODELS_DIR / "rubric_assisted_gradient_boosting_model.joblib"
VECTORIZER_FILE = MODELS_DIR / "rubric_assisted_vectorizer.joblib"

TARGET_COLUMN = "target_score"
GROUP_COLUMN = "profile_id"
RELEVANCE_THRESHOLD = 70.0
PRECISION_K = 5
RANDOM_STATE = 42
TEST_SIZE = 0.2
TRACK_LABEL = "rubric_assisted"

TEXT_FEATURE_COLUMNS: List[str] = [
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
]

NUMERIC_COMPONENT_COLUMNS: List[str] = [
    "major_fit_score",
    "skill_match_score",
    "role_interest_score",
    "city_match_score",
    "program_type_score",
    "work_mode_score",
    "verification_score",
    "interview_score",
]

REQUIRED_COLUMNS: List[str] = (
    [GROUP_COLUMN, TARGET_COLUMN, "opportunity_id", "company_name", "program_name"]
    + TEXT_FEATURE_COLUMNS
    + NUMERIC_COMPONENT_COLUMNS
)

COMBINED_TEXT_COLUMN = "combined_text"


# ---------------------------------------------------------------------------
# Data loading and features
# ---------------------------------------------------------------------------

def _safe_str(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def build_combined_text(row: pd.Series) -> str:
    """Concatenate profile and opportunity text fields into one feature string."""
    parts = [_safe_str(row.get(column, "")) for column in TEXT_FEATURE_COLUMNS]
    return " ".join(part for part in parts if part)


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add combined_text and ensure numeric rubric columns are float."""
    features = df.copy()
    features[COMBINED_TEXT_COLUMN] = features.apply(build_combined_text, axis=1)
    for column in NUMERIC_COMPONENT_COLUMNS:
        features[column] = pd.to_numeric(features[column], errors="coerce").fillna(0.0)
    return features


def validate_required_columns(
    df: pd.DataFrame,
    required: Optional[Sequence[str]] = None,
) -> None:
    """Raise ValueError when expected columns are missing."""
    columns = list(required or REQUIRED_COLUMNS)
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def load_regression_dataset(path: Path = DATASET_FILE) -> pd.DataFrame:
    """Load and validate the regression training CSV."""
    if not path.exists():
        raise FileNotFoundError(
            f"Regression dataset not found at {path}. "
            "Run: python -m app.build_regression_dataset"
        )
    df = pd.read_csv(path)
    validate_required_columns(df)
    if df.empty:
        raise ValueError("Regression dataset is empty.")
    return df


def group_train_test_split(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split by profile_id so all rows for a profile stay in one fold.

    Uses GroupShuffleSplit (80/20 by default).
    """
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )
    groups = df[GROUP_COLUMN].astype(str)
    train_idx, test_idx = next(splitter.split(df, groups=groups))
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)
    return train_df, test_df


def load_split_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load train/test from pre-computed split files if they exist."""
    if TRAIN_SPLIT_FILE.exists() and TEST_SPLIT_FILE.exists():
        train_df = pd.read_csv(TRAIN_SPLIT_FILE)
        test_df = pd.read_csv(TEST_SPLIT_FILE)
        print(
            f"[train_regression_model] Loaded split files: "
            f"train={len(train_df)} rows / {train_df[GROUP_COLUMN].nunique()} profiles, "
            f"test={len(test_df)} rows / {test_df[GROUP_COLUMN].nunique()} profiles"
        )
        return train_df, test_df
    print(
        "[train_regression_model] Split files not found — "
        "falling back to GroupShuffleSplit on full dataset."
    )
    raw_df = load_regression_dataset(DATASET_FILE)
    return group_train_test_split(raw_df)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Return MAE, RMSE, and R² for continuous targets."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    mse = mean_squared_error(y_true_arr, y_pred_arr)
    return {
        "mae": float(mean_absolute_error(y_true_arr, y_pred_arr)),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true_arr, y_pred_arr)),
    }


def precision_at_k(
    frame: pd.DataFrame,
    predicted_column: str = "predicted_score",
    actual_column: str = TARGET_COLUMN,
    group_column: str = GROUP_COLUMN,
    k: int = PRECISION_K,
    relevance_threshold: float = RELEVANCE_THRESHOLD,
) -> Dict[str, float]:
    """
    Ranking metric by profile: fraction of top-k predictions that are relevant.

    Relevant when actual target_score >= relevance_threshold.
    Returns key 'precision_at_5' for backward compatibility regardless of k.
    """
    if frame.empty:
        return {
            "precision_at_5": 0.0,
            "avg_actual_top5": 0.0,
            "avg_predicted_top5": 0.0,
        }

    precisions: List[float] = []
    actual_top5: List[float] = []
    predicted_top5: List[float] = []

    for _, group in frame.groupby(group_column):
        ranked = group.sort_values(predicted_column, ascending=False).head(k)
        if ranked.empty:
            continue
        relevant_count = (ranked[actual_column] >= relevance_threshold).sum()
        precisions.append(relevant_count / min(k, len(ranked)))
        actual_top5.append(float(ranked[actual_column].mean()))
        predicted_top5.append(float(ranked[predicted_column].mean()))

    return {
        "precision_at_5": float(np.mean(precisions)) if precisions else 0.0,
        "avg_actual_top5": float(np.mean(actual_top5)) if actual_top5 else 0.0,
        "avg_predicted_top5": float(np.mean(predicted_top5)) if predicted_top5 else 0.0,
    }


def clip_predictions(values: np.ndarray) -> np.ndarray:
    """Clamp model outputs to the 0–100 recommendation scale."""
    return np.clip(values, 0.0, 100.0)


def _compute_all_precision(ranking_frame: pd.DataFrame) -> Dict[str, float]:
    """Compute precision at 1, 3, and 5."""
    result: Dict[str, float] = {}
    for k_val in (1, 3, 5):
        p = precision_at_k(ranking_frame, k=k_val, relevance_threshold=RELEVANCE_THRESHOLD)
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
# Model builders
# ---------------------------------------------------------------------------

def build_ridge_pipeline() -> Pipeline:
    """TF-IDF text + scaled rubric components → Ridge regression."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), max_features=3000),
                COMBINED_TEXT_COLUMN,
            ),
            ("numeric", StandardScaler(), NUMERIC_COMPONENT_COLUMNS),
        ],
        sparse_threshold=0.3,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        ]
    )


def build_random_forest_pipeline() -> Pipeline:
    """TF-IDF text + rubric components → Random Forest."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), max_features=2000),
                COMBINED_TEXT_COLUMN,
            ),
            ("numeric", "passthrough", NUMERIC_COMPONENT_COLUMNS),
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
                    max_depth=12,
                    min_samples_leaf=2,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def build_gradient_boosting_pipeline() -> Pipeline:
    """Rubric numeric components only → Gradient Boosting (dense features)."""
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
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


def extract_tfidf_vectorizer(pipeline: Pipeline) -> TfidfVectorizer:
    """Extract the fitted TF-IDF step from the Ridge pipeline."""
    preprocessor: ColumnTransformer = pipeline.named_steps["preprocessor"]
    return preprocessor.named_transformers_["tfidf"]


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def _feature_matrix_for_pipeline(
    pipeline: Pipeline,
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return the input columns expected by a fitted/unfitted pipeline."""
    if "preprocessor" in pipeline.named_steps:
        return frame[[COMBINED_TEXT_COLUMN, *NUMERIC_COMPONENT_COLUMNS]]
    return frame[NUMERIC_COMPONENT_COLUMNS]


def evaluate_model(
    model_name: str,
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[Dict, pd.DataFrame]:
    """Fit pipeline, compute metrics, and build test prediction rows."""
    train_features = build_feature_frame(train_df)
    test_features = build_feature_frame(test_df)

    x_train = _feature_matrix_for_pipeline(pipeline, train_features)
    x_test = _feature_matrix_for_pipeline(pipeline, test_features)
    y_train = train_features[TARGET_COLUMN].to_numpy(dtype=float)
    y_test = test_features[TARGET_COLUMN].to_numpy(dtype=float)

    pipeline.fit(x_train, y_train)
    y_pred = clip_predictions(pipeline.predict(x_test))

    metrics = regression_metrics(y_test, y_pred)

    ranking_frame = test_features[
        [GROUP_COLUMN, "opportunity_id", "company_name", "program_name", TARGET_COLUMN]
    ].copy()
    ranking_frame["predicted_score"] = y_pred

    precision_metrics = _compute_all_precision(ranking_frame)
    metrics.update(precision_metrics)

    metrics["track"] = TRACK_LABEL
    metrics["model"] = model_name
    metrics["train_rows"] = int(len(train_df))
    metrics["test_rows"] = int(len(test_df))
    metrics["train_profiles"] = int(train_df[GROUP_COLUMN].nunique())
    metrics["test_profiles"] = int(test_df[GROUP_COLUMN].nunique())
    metrics["feature_set"] = "text_and_rubric_components"
    metrics["leakage_safe"] = False

    # Predictions with required columns
    preds = ranking_frame.rename(columns={TARGET_COLUMN: "target_score"})
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
    output_path: Path = FIGURE_FILE,
) -> None:
    """Scatter plot of actual vs predicted scores for one model."""
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
    ax.set_title(f"Rubric-assisted – Actual vs Predicted ({model_name})")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def train_all_models() -> Tuple[pd.DataFrame, pd.DataFrame, Pipeline]:
    """
    Train Ridge, Random Forest, and Gradient Boosting; save artefacts.

    Returns:
        metrics_df, predictions_df, fitted_ridge_pipeline
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    train_df, test_df = load_split_files()

    print(
        f"[train_regression_model] train={len(train_df)} rows, "
        f"test={len(test_df)} rows"
    )
    print(
        "[train_regression_model] WARNING: target_score was built from rubric "
        "component columns also used as numeric features — expect strong metrics. "
        "This is the rubric_assisted (leakage demo) track."
    )

    all_metrics: List[Dict] = []
    all_predictions: List[pd.DataFrame] = []
    ridge_pipeline: Optional[Pipeline] = None

    model_builders = [
        ("rubric_assisted_ridge", build_ridge_pipeline),
        ("rubric_assisted_random_forest", build_random_forest_pipeline),
        ("rubric_assisted_gradient_boosting", build_gradient_boosting_pipeline),
    ]

    for model_name, builder in model_builders:
        print(f"[train_regression_model] Training {model_name} …")
        pipeline = builder()
        metrics, predictions = evaluate_model(
            model_name=model_name,
            pipeline=pipeline,
            train_df=train_df,
            test_df=test_df,
        )
        all_metrics.append(metrics)
        all_predictions.append(predictions)

        if "ridge" in model_name:
            ridge_pipeline = pipeline
            joblib.dump(pipeline, RIDGE_MODEL_FILE)
            joblib.dump(extract_tfidf_vectorizer(pipeline), VECTORIZER_FILE)
        elif "random_forest" in model_name:
            joblib.dump(pipeline, RANDOM_FOREST_MODEL_FILE)
        elif "gradient_boosting" in model_name:
            joblib.dump(pipeline, GRADIENT_BOOSTING_MODEL_FILE)

        print(
            f"  MAE={metrics['mae']:.3f}  RMSE={metrics['rmse']:.3f}  "
            f"R²={metrics['r2']:.3f}  P@5={metrics['precision_at_5']:.3f}"
        )

    # Build metrics DataFrame with canonical column order
    metrics_df = pd.DataFrame(all_metrics)[
        [
            "track", "model", "mae", "rmse", "r2",
            "precision_at_1", "precision_at_3", "precision_at_5",
            "train_rows", "test_rows", "train_profiles", "test_profiles",
            "feature_set", "leakage_safe",
        ]
    ]
    metrics_df.to_csv(METRICS_FILE, index=False)

    predictions_df = pd.concat(all_predictions, ignore_index=True)
    predictions_df.to_csv(PREDICTIONS_FILE, index=False)

    best_name = metrics_df.sort_values("rmse").iloc[0]["model"]
    best_predictions = predictions_df[predictions_df["model"] == best_name]
    save_prediction_plot(best_predictions, str(best_name))

    print(f"[train_regression_model] Metrics saved to {METRICS_FILE}")
    print(f"[train_regression_model] Predictions saved to {PREDICTIONS_FILE}")
    print(f"[train_regression_model] Figure saved to {FIGURE_FILE}")
    print(f"[train_regression_model] Models saved under {MODELS_DIR}")
    print(
        "[train_regression_model] NOTE: These metrics are NOT leakage-safe. "
        "Do not report them as honest model performance."
    )

    assert ridge_pipeline is not None
    return metrics_df, predictions_df, ridge_pipeline


def main() -> None:
    """CLI entry point."""
    train_all_models()


if __name__ == "__main__":
    main()
