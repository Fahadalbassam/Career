"""
enrich_opportunities_dataset.py — ML-2C enriched opportunity dataset builder.

Loads Opportunities_Clean.xlsx, applies enrich_opportunity_signals() to each
row, and writes the result to Opportunities_Enriched.csv with five new columns:

    inferred_role_cluster
    inferred_interests
    inferred_skills
    required_skills
    preferred_skills

List-valued columns are stored as semicolon-separated strings.
The source Excel is never mutated.

Run from the backend directory:
    python -m app.enrich_opportunities_dataset

Output:
    data/processed/Opportunities_Enriched.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from app.opportunity_enrichment import enrich_opportunity_signals
from app.recommender import OPPORTUNITIES_XLSX_PATH, load_opportunities_from_xlsx
from app.schemas import Opportunity

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "Opportunities_Enriched.csv"

ENRICHED_COLUMNS = [
    "inferred_role_cluster",
    "inferred_interests",
    "inferred_skills",
    "required_skills",
    "preferred_skills",
]


def _join_list(values: object) -> str:
    """Convert a list to a semicolon-separated string."""
    if isinstance(values, list):
        return "; ".join(str(v) for v in values if v)
    return str(values) if values else ""


def _load_raw_dataframe(xlsx_path: Path = OPPORTUNITIES_XLSX_PATH) -> pd.DataFrame:
    """Load the raw Excel into a DataFrame, trying the named sheet first."""
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Opportunities Excel not found: {xlsx_path}")
    try:
        df = pd.read_excel(xlsx_path, sheet_name="opportunities_clean")
    except ValueError:
        df = pd.read_excel(xlsx_path)
    return df


def build_enriched_dataframe(
    xlsx_path: Path = OPPORTUNITIES_XLSX_PATH,
) -> pd.DataFrame:
    """Return a DataFrame with original columns plus five enriched signal columns.

    Parameters
    ----------
    xlsx_path:
        Path to the source Opportunities_Clean.xlsx.  Not mutated.

    Returns
    -------
    pd.DataFrame
        Original rows with enriched columns appended.  List columns are stored
        as semicolon-separated strings.
    """
    raw_df = _load_raw_dataframe(xlsx_path)
    opportunities: List[Opportunity] = load_opportunities_from_xlsx(xlsx_path)

    if len(opportunities) != len(raw_df):
        # Tolerate minor row-count drift from malformed / blank rows
        pass

    enriched_rows = []
    for opp in opportunities:
        signals = enrich_opportunity_signals(opp)
        enriched_rows.append(
            {
                "inferred_role_cluster": signals.get("role_cluster") or "",
                "inferred_interests": _join_list(signals.get("inferred_interests", [])),
                "inferred_skills": _join_list(signals.get("inferred_skills", [])),
                "required_skills": _join_list(signals.get("required_skills", [])),
                "preferred_skills": _join_list(signals.get("preferred_skills", [])),
            }
        )

    enriched_df = pd.DataFrame(enriched_rows)

    # Align indices before concat
    raw_df = raw_df.reset_index(drop=True)
    enriched_df = enriched_df.reset_index(drop=True)

    # Keep only rows we have enrichment for (handles count drift)
    n = min(len(raw_df), len(enriched_df))
    result = pd.concat([raw_df.iloc[:n], enriched_df.iloc[:n]], axis=1)

    # If these columns already exist in raw_df, prefer the new enriched values
    for col in ENRICHED_COLUMNS:
        if col in raw_df.columns:
            result[col] = enriched_df[col].values[:n]

    return result


def main() -> None:
    """Build and save Opportunities_Enriched.csv."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[enrich_opportunities_dataset] Loading: {OPPORTUNITIES_XLSX_PATH}")
    df = build_enriched_dataframe()

    df.to_csv(OUTPUT_FILE, index=False)

    has_role_cluster = (df["inferred_role_cluster"].fillna("") != "").sum()
    has_required = (df["required_skills"].fillna("") != "").sum()
    has_preferred = (df["preferred_skills"].fillna("") != "").sum()

    print(f"[enrich_opportunities_dataset] Input rows : {len(df)}")
    print(f"[enrich_opportunities_dataset] Output rows: {len(df)}")
    print(f"[enrich_opportunities_dataset] Has inferred_role_cluster : {has_role_cluster}")
    print(f"[enrich_opportunities_dataset] Has required_skills        : {has_required}")
    print(f"[enrich_opportunities_dataset] Has preferred_skills       : {has_preferred}")
    print(f"[enrich_opportunities_dataset] Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
