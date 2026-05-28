# Rubric vs ML Score Comparison (ML-5)

## Purpose

The live CareerFinder recommender ranks opportunities using a deterministic **rubric score** (`target_score`). ML-5 compares that score to the hold-out **fair model prediction** (`predicted_score`) from the best leakage-safe regressor to see whether ML can serve as a trustworthy **secondary** signal before any production integration.

## Model and data

- **Best fair model:** `fair_gradient_boosting`
- **Rows compared (test split):** 1,730
- **Profiles compared:** 10
- **Split method:** GroupShuffleSplit
- **Train / test rows:** 6,574 / 1,730
- **No profile overlap across train/test:** True

## Score agreement

| Metric | Value |
|---|---:|
| Mean absolute difference | 5.834 |
| Median absolute difference | 5.280 |
| Max absolute difference | 25.709 |
| Pearson correlation | 0.833 |
| Spearman correlation | 0.784 |
| Average top-5 overlap (per profile) | 0.360 |

## What disagreement means

Large `absolute_difference` values mean the fair model assigns a very different numeric score than the rubric for the same profile–opportunity pair. Low **top-5 overlap** means the model would surface a different shortlist than the live recommender even when both use the same underlying opportunities.

Moderate Pearson/Spearman correlation with non-trivial MAE (~5.8 on the fair model) suggests the ML model captures broad fit patterns but does not replicate rubric weights exactly — expected because rubric component scores are excluded from fair model inputs.

## When ML may help

- **Shadow scoring:** log `predicted_score` alongside rubric `match_score` to find cases where text/metadata suggests higher fit than the rubric captured.
- **Tie-breaking:** when rubric scores cluster (e.g. many COOP listings near 55–65), ML may reorder within a narrow band — only after validation.
- **Offline analysis:** largest-disagreement exports highlight opportunities to review rubric weights or enrichment quality.

## Why rubric stays primary (for now)

- The rubric is **interpretable**, aligned with product copy (`score_breakdown`), and already powers `/recommend`.
- The fair model was trained to **predict** the rubric label, not user outcomes; it has not been A/B tested in production.
- Top-5 overlap is limited on a 10-profile hold-out set — not enough evidence to replace ranking.

## Recommendation

1. **Use ML as a secondary / shadow score first** (e.g. optional `ml_score` in API responses behind a feature flag).
2. **Do not replace live ranking yet** — keep sorting by rubric `match_score` until shadow logs show consistent benefit.
3. **Next engineering step:** wire shadow `ml_score` on `/recommend` without changing default sort order; compare rank deltas in logs.

## Artifacts

| File | Description |
|---|---|
| Full comparison | `data/processed/rubric_vs_ml_comparison.csv` |
| Largest disagreements | `data/processed/rubric_vs_ml_largest_disagreements.csv` |
| Per-profile top-5 overlap | `data/processed/rubric_vs_ml_profile_overlap.csv` |
| JSON summary | `data/processed/rubric_vs_ml_summary.json` |
