"""
build_training_data.py – Build a labelled training dataset for the ML fit classifier.

Reads cleaned opportunities and assigns a fit label (High / Medium / Low)
based on the major_fit field versus a target major.

Run after clean_data.py has been executed.

Output:
    data/processed/training_fit_dataset.csv
"""

from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = PROCESSED_DIR / "training_fit_dataset.csv"

MAJORS = ["CS", "AI", "CYS", "CIS", "DS", "DE", "CE", "FT"]


def assign_fit_label(opportunity_major_fit: str, student_major: str) -> str:
    """
    Assign a fit label given the opportunity's accepted majors and a student major.

    Args:
        opportunity_major_fit: Comma-separated accepted majors string.
        student_major: The student's major code.

    Returns:
        "High", "Medium", or "Low".
    """
    if not isinstance(opportunity_major_fit, str) or not opportunity_major_fit.strip():
        return "Medium"  # open to all
    accepted = [m.strip().upper() for m in opportunity_major_fit.split(",")]
    if student_major.upper() in accepted:
        return "High"
    if len(accepted) >= 3:
        return "Medium"  # broad opportunity
    return "Low"


def build_training_data(opps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand the opportunities dataframe by generating one row per (opportunity, major) pair.

    Args:
        opps_df: Cleaned opportunities dataframe with a ``major_fit`` column.

    Returns:
        Training dataframe with columns: opportunity_id, title, company, major,
        fit_label, and any available text features.
    """
    rows = []
    for _, row in opps_df.iterrows():
        for major in MAJORS:
            label = assign_fit_label(str(row.get("major_fit", "")), major)
            rows.append({
                "opportunity_id": row.get("id", ""),
                "title": row.get("title", ""),
                "company": row.get("company", ""),
                "city": row.get("city", ""),
                "work_mode": row.get("work_mode", ""),
                "program_type": row.get("program_type", ""),
                "student_major": major,
                "fit_label": label,
            })
    return pd.DataFrame(rows)


def main() -> None:
    """Run the training data builder."""
    opps_path = PROCESSED_DIR / "opportunities_clean.csv"
    if not opps_path.exists():
        print("[build_training_data] opportunities_clean.csv not found. Run clean_data.py first.")
        return

    print("[build_training_data] Loading cleaned opportunities …")
    opps = pd.read_csv(opps_path)

    print("[build_training_data] Building training dataset …")
    training_df = build_training_data(opps)

    print(f"[build_training_data] Generated {len(training_df)} training examples.")
    training_df.to_csv(OUTPUT_FILE, index=False)
    print(f"[build_training_data] Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
