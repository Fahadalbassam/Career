"""
ml_scoring.py – Optional ML shadow scoring for /recommend.

Feature flag: CAREERFINDER_ENABLE_ML_SCORE=true

When enabled, this module lazy-loads the best fair regression model
(fair_gradient_boosting_model.joblib) and computes a secondary ml_score
for each recommendation.  The rubric match_score and ranking are never
modified.

Public API
----------
is_ml_score_enabled() -> bool
get_ml_score_source() -> str
predict_ml_scores(profile, opportunities) -> dict[int, float | None]
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "models" / "fair_gradient_boosting_model.joblib"
ML_SCORE_SOURCE = "fair_gradient_boosting"

# These must match train_fair_regression_model.CATEGORICAL_COLUMNS /
# COUNT_FEATURE_COLUMNS exactly — the saved pipeline's ColumnTransformer
# looks them up by name.
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

_model = None
_model_load_attempted: bool = False


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def is_ml_score_enabled() -> bool:
    """Return True when CAREERFINDER_ENABLE_ML_SCORE=true."""
    return os.environ.get("CAREERFINDER_ENABLE_ML_SCORE", "").strip().lower() == "true"


def get_ml_score_source() -> str:
    """Return the model identifier string attached to ml_score_source."""
    return ML_SCORE_SOURCE


# ---------------------------------------------------------------------------
# Internal: model loading
# ---------------------------------------------------------------------------

def _load_model():
    """Lazy-load the fair GB pipeline.  Logs on failure; returns None."""
    global _model, _model_load_attempted
    if _model_load_attempted:
        return _model
    _model_load_attempted = True
    try:
        import joblib  # noqa: PLC0415

        if not MODEL_PATH.exists():
            logger.warning("[ml_scoring] Model artifact not found: %s", MODEL_PATH)
            return None
        _model = joblib.load(MODEL_PATH)
        logger.info("[ml_scoring] Loaded %s from %s", ML_SCORE_SOURCE, MODEL_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ml_scoring] Failed to load ML model: %s", exc)
        _model = None
    return _model


# ---------------------------------------------------------------------------
# Internal: feature construction
# ---------------------------------------------------------------------------

def _safe_str(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _join_list(items: Optional[List[str]], sep: str = "; ") -> str:
    if not items:
        return ""
    return sep.join(_safe_str(x) for x in items if _safe_str(x))


def _build_feature_row(profile, opp) -> dict:
    """Build the 12-column feature dict for the GB pipeline.

    Replicates the feature engineering from
    train_fair_regression_model.build_fair_feature_frame for a single
    live profile–opportunity pair.

    Categorical values missing from the live profile default to
    ``"unknown"``; the pipeline's OneHotEncoder(handle_unknown="ignore")
    will produce an all-zeros vector for any unseen category, which is
    the same safe fallback used by the training pipeline.
    """
    from app.rubric import infer_role_cluster  # noqa: PLC0415

    # ------------------------------------------------------------------
    # Categorical features
    # ------------------------------------------------------------------
    major = _safe_str(profile.major) or "unknown"
    city = _safe_str(profile.city) or "unknown"
    program_type = _safe_str(profile.program_type) or "unknown"
    work_mode = _safe_str(profile.work_mode) or "unknown"
    opp_program_type = _safe_str(opp.program_type) or "unknown"
    opp_work_mode = _safe_str(opp.work_mode) or "unknown"
    opp_role_cluster = _safe_str(infer_role_cluster(opp)) or "unknown"

    # ------------------------------------------------------------------
    # Count features
    # ------------------------------------------------------------------
    skill_token_count = len(profile.skills or [])
    qualification_token_count = len(profile.qualifications or [])
    preferred_role_count = len(profile.preferred_roles or [])
    preferred_location_count = len(profile.preferred_locations or [])

    # text_length: approximate the training combined_text size so the
    # count feature stays in a realistic range.  The GB model has no
    # TF-IDF step; text_length is used as a numeric feature only.
    text_parts = [
        _safe_str(profile.major),
        _safe_str(profile.university),
        _safe_str(profile.city),
        _join_list(profile.preferred_locations),
        _join_list(profile.skills),
        _join_list(profile.qualifications),
        _safe_str(profile.interest),
        _safe_str(profile.program_type),
        _safe_str(profile.work_mode),
        _join_list(profile.preferred_roles),
        _safe_str(profile.interview_preference),
        _safe_str(opp.company),
        _safe_str(opp.title),
        _safe_str(opp.city),
        _safe_str(opp.program_type),
        _safe_str(opp.work_mode),
        _join_list(opp.skills_list),
        _safe_str(opp.requirements),
        opp_role_cluster,
    ]
    combined_text = " ".join(p for p in text_parts if p)
    text_length = len(combined_text)

    return {
        "major": major,
        "city": city,
        "program_type": program_type,
        "work_mode": work_mode,
        "opportunity_program_type": opp_program_type,
        "opportunity_work_mode": opp_work_mode,
        "opportunity_role_cluster": opp_role_cluster,
        "text_length": text_length,
        "skill_token_count": skill_token_count,
        "qualification_token_count": qualification_token_count,
        "preferred_role_count": preferred_role_count,
        "preferred_location_count": preferred_location_count,
    }


# ---------------------------------------------------------------------------
# Public: batch prediction
# ---------------------------------------------------------------------------

def predict_ml_scores(profile, opportunities) -> Dict[int, Optional[float]]:
    """Return mapping of opportunity.id → ml_score (0–100) or None.

    Always safe: returns an all-None dict when the flag is disabled,
    the model artifact is missing, or prediction raises any exception.
    Ranking and rubric scoring are never affected.
    """
    result: Dict[int, Optional[float]] = {opp.id: None for opp in opportunities}

    if not is_ml_score_enabled():
        return result

    model = _load_model()
    if model is None:
        return result

    try:
        import pandas as pd  # noqa: PLC0415

        ids: List[int] = []
        rows: List[dict] = []
        for opp in opportunities:
            rows.append(_build_feature_row(profile, opp))
            ids.append(opp.id)

        if not rows:
            return result

        all_cols = CATEGORICAL_COLUMNS + COUNT_FEATURE_COLUMNS
        df = pd.DataFrame(rows, columns=all_cols)
        preds = model.predict(df)

        for opp_id, raw_pred in zip(ids, preds):
            clamped = float(max(0.0, min(100.0, float(raw_pred))))
            result[opp_id] = round(clamped, 1)

    except Exception as exc:  # noqa: BLE001
        logger.warning("[ml_scoring] Prediction failed: %s", exc)
        # result already initialised to all-None

    return result
