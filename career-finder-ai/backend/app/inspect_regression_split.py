"""
inspect_regression_split.py — ML-2C readable train/test split inspection.

Loads the regression dataset and applies the same GroupShuffleSplit strategy
used by the training scripts to produce readable, verifiable split files.

Run from the backend directory:
    python -m app.inspect_regression_split

Reads:
    data/processed/student_opportunity_regression_dataset.csv

Writes:
    data/processed/regression_train_split.csv
    data/processed/regression_test_split.csv
    data/processed/regression_split_profile_ids.csv
    data/processed/regression_split_summary.json

Expected invariants:
    overlapping_profile_ids == []
    train_ratio ≈ 0.80
    test_ratio  ≈ 0.20
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

DATASET_FILE = PROCESSED_DIR / "student_opportunity_regression_dataset.csv"
TRAIN_FILE = PROCESSED_DIR / "regression_train_split.csv"
TEST_FILE = PROCESSED_DIR / "regression_test_split.csv"
PROFILE_IDS_FILE = PROCESSED_DIR / "regression_split_profile_ids.csv"
SUMMARY_FILE = PROCESSED_DIR / "regression_split_summary.json"

RANDOM_STATE = 42
TEST_SIZE = 0.2
SPLIT_METHOD = "GroupShuffleSplit"
GROUP_COLUMN = "profile_id"


def compute_split(
    dataset_path: Path = DATASET_FILE,
    random_state: int = RANDOM_STATE,
    test_size: float = TEST_SIZE,
) -> dict:
    """Compute and persist the train/test split.

    Returns
    -------
    dict
        Summary dict matching ``regression_split_summary.json`` structure.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Regression dataset not found: {dataset_path}\n"
            "Run: python -m app.build_regression_dataset"
        )

    df = pd.read_csv(dataset_path)

    if GROUP_COLUMN not in df.columns:
        raise ValueError(
            f"Column '{GROUP_COLUMN}' not found in {dataset_path}. "
            "Expected profile_id column for GroupShuffleSplit."
        )

    groups = df[GROUP_COLUMN]
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, test_idx = next(splitter.split(df, groups=groups))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    train_profiles = set(train_df[GROUP_COLUMN].unique())
    test_profiles = set(test_df[GROUP_COLUMN].unique())
    overlap = sorted(train_profiles & test_profiles)

    total_rows = len(df)
    train_rows = len(train_df)
    test_rows = len(test_df)
    total_profiles = int(df[GROUP_COLUMN].nunique())

    summary = {
        "total_rows": total_rows,
        "train_rows": train_rows,
        "test_rows": test_rows,
        "train_ratio": round(train_rows / total_rows, 4) if total_rows else 0.0,
        "test_ratio": round(test_rows / total_rows, 4) if total_rows else 0.0,
        "total_profiles": total_profiles,
        "train_profiles": len(train_profiles),
        "test_profiles": len(test_profiles),
        "overlapping_profile_ids": overlap,
        "random_state": random_state,
        "test_size": test_size,
        "split_method": SPLIT_METHOD,
    }

    # Write split files
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(TRAIN_FILE, index=False)
    test_df.to_csv(TEST_FILE, index=False)

    profile_ids_df = pd.DataFrame(
        {
            "profile_id": sorted(df[GROUP_COLUMN].unique()),
            "split": [
                "train" if pid in train_profiles else "test"
                for pid in sorted(df[GROUP_COLUMN].unique())
            ],
        }
    )
    profile_ids_df.to_csv(PROFILE_IDS_FILE, index=False)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def _print_summary(summary: dict) -> None:
    total = summary["total_rows"]
    print()
    print("=" * 60)
    print("  Regression Dataset Split Inspection  (ML-2C)")
    print("=" * 60)
    print(f"  Split method  : {summary['split_method']} by {GROUP_COLUMN}")
    print(f"  Random state  : {summary['random_state']}")
    print(f"  Test size     : {summary['test_size']}")
    print()
    print(f"  Total rows    : {total:,}")
    print(
        f"  Train rows    : {summary['train_rows']:,}  "
        f"({summary['train_ratio']:.1%})"
    )
    print(
        f"  Test rows     : {summary['test_rows']:,}  "
        f"({summary['test_ratio']:.1%})"
    )
    print()
    print(f"  Total profiles: {summary['total_profiles']}")
    print(f"  Train profiles: {summary['train_profiles']}")
    print(f"  Test profiles : {summary['test_profiles']}")

    overlap = summary["overlapping_profile_ids"]
    if overlap:
        print(f"\n  *** WARNING: {len(overlap)} overlapping profile_id(s): {overlap}")
    else:
        print("  Profile overlap: NONE  [OK]")

    print()
    print(f"  Saved: {TRAIN_FILE.name}")
    print(f"  Saved: {TEST_FILE.name}")
    print(f"  Saved: {PROFILE_IDS_FILE.name}")
    print(f"  Saved: {SUMMARY_FILE.name}")
    print("=" * 60)
    print()


def main() -> None:
    summary = compute_split()
    _print_summary(summary)


if __name__ == "__main__":
    main()
