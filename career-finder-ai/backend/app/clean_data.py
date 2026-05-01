"""
clean_data.py – Dataset cleaning pipeline.

Run this script after placing raw files in data/raw/.

Expected input files:
    data/raw/companies_raw.csv
    data/raw/opportunities_raw.csv

Expected output files:
    data/processed/companies_clean.csv
    data/processed/opportunities_clean.csv
    data/processed/missing_values_report.csv
    data/processed/data_dictionary.xlsx
"""

from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Normalisation maps
CITY_ALIASES: dict[str, str] = {
    "الرياض": "Riyadh",
    "جدة": "Jeddah",
    "الدمام": "Dammam",
    "مكة": "Mecca",
    "المدينة": "Medina",
    "الخبر": "Khobar",
    "الظهران": "Dhahran",
}

WORK_MODE_ALIASES: dict[str, str] = {
    "عن بعد": "Remote",
    "حضوري": "On-site",
    "هجين": "Hybrid",
    "remote": "Remote",
    "on-site": "On-site",
    "onsite": "On-site",
    "hybrid": "Hybrid",
}

PROGRAM_TYPE_ALIASES: dict[str, str] = {
    "تعاوني": "COOP",
    "تدريب": "Internship",
    "coop": "COOP",
    "co-op": "COOP",
    "internship": "Internship",
    "intern": "Internship",
}


def normalise_column(series: pd.Series, alias_map: dict[str, str]) -> pd.Series:
    """Apply a case-insensitive alias map to a string Series."""
    lowered = series.str.strip().str.lower()
    mapping = {k.lower(): v for k, v in alias_map.items()}
    return lowered.map(mapping).fillna(series.str.strip())


def clean_companies(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the companies dataframe."""
    df = df.drop_duplicates(subset=["company_name"]).copy()
    df["company_name"] = df["company_name"].str.strip().str.title()
    if "city" in df.columns:
        df["city"] = normalise_column(df["city"], CITY_ALIASES)
    return df


def clean_opportunities(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the opportunities dataframe."""
    df = df.drop_duplicates().copy()
    if "city" in df.columns:
        df["city"] = normalise_column(df["city"], CITY_ALIASES)
    if "work_mode" in df.columns:
        df["work_mode"] = normalise_column(df["work_mode"], WORK_MODE_ALIASES)
    if "program_type" in df.columns:
        df["program_type"] = normalise_column(df["program_type"], PROGRAM_TYPE_ALIASES)
    return df


def generate_missing_values_report(dataframes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return a summary dataframe of missing value counts per column."""
    rows = []
    for name, df in dataframes.items():
        for col in df.columns:
            missing = df[col].isna().sum()
            rows.append({"dataset": name, "column": col, "missing_count": missing,
                         "missing_pct": round(missing / len(df) * 100, 2) if len(df) else 0})
    return pd.DataFrame(rows)


def main() -> None:
    """Run the full cleaning pipeline."""
    companies_path = RAW_DIR / "companies_raw.csv"
    opps_path = RAW_DIR / "opportunities_raw.csv"

    if not companies_path.exists() or not opps_path.exists():
        print("[clean_data] Raw files not found in data/raw/. Skipping.")
        print("  Expected: companies_raw.csv, opportunities_raw.csv")
        return

    print("[clean_data] Loading raw data …")
    companies = pd.read_csv(companies_path)
    opportunities = pd.read_csv(opps_path)

    print("[clean_data] Cleaning …")
    companies_clean = clean_companies(companies)
    opps_clean = clean_opportunities(opportunities)

    print("[clean_data] Saving processed files …")
    companies_clean.to_csv(PROCESSED_DIR / "companies_clean.csv", index=False)
    opps_clean.to_csv(PROCESSED_DIR / "opportunities_clean.csv", index=False)

    report = generate_missing_values_report(
        {"companies": companies_clean, "opportunities": opps_clean}
    )
    report.to_csv(PROCESSED_DIR / "missing_values_report.csv", index=False)

    # Write simple data dictionary to Excel
    with pd.ExcelWriter(PROCESSED_DIR / "data_dictionary.xlsx") as writer:
        for name, df in [("companies", companies_clean), ("opportunities", opps_clean)]:
            info = pd.DataFrame({
                "column": df.columns,
                "dtype": df.dtypes.values,
                "sample": [df[c].dropna().iloc[0] if not df[c].dropna().empty else "" for c in df.columns],
            })
            info.to_excel(writer, sheet_name=name, index=False)

    print("[clean_data] Done. Outputs saved to data/processed/")


if __name__ == "__main__":
    main()
