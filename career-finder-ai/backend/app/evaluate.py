"""
evaluate.py – Evaluate the trained fit classifier and report metrics.

Run after train_model.py has been executed.

Outputs:
    reports/figures/confusion_matrix.png
    reports/figures/metrics_table.csv
"""

from pathlib import Path

import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)
from sklearn.model_selection import train_test_split

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
FIGURES_DIR = Path("reports/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

TRAINING_FILE = PROCESSED_DIR / "training_fit_dataset.csv"
CLASSIFIER_FILE = MODELS_DIR / "fit_classifier.joblib"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.joblib"


def evaluate() -> None:
    """Load the saved model and evaluate it on a held-out test split."""
    if not TRAINING_FILE.exists():
        print("[evaluate] Training file not found. Run build_training_data.py first.")
        return
    if not CLASSIFIER_FILE.exists() or not VECTORIZER_FILE.exists():
        print("[evaluate] Model artefacts not found. Run train_model.py first.")
        return

    print("[evaluate] Loading data and model …")
    df = pd.read_csv(TRAINING_FILE)
    df["text"] = df.apply(
        lambda r: " ".join([str(r.get("title", "")), str(r.get("company", "")),
                            str(r.get("program_type", "")), str(r.get("student_major", ""))]),
        axis=1,
    )
    X = df["text"]
    y = df["fit_label"]

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    vectorizer = joblib.load(VECTORIZER_FILE)
    clf = joblib.load(CLASSIFIER_FILE)

    X_test_vec = vectorizer.transform(X_test)
    y_pred = clf.predict(X_test_vec)

    # Classification report
    report_dict = classification_report(y_test, y_pred, output_dict=True)
    metrics_df = pd.DataFrame(report_dict).transpose()
    metrics_df.to_csv(FIGURES_DIR / "metrics_table.csv")
    print("[evaluate] Classification report:")
    print(classification_report(y_test, y_pred))

    # Confusion matrix
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=labels, yticklabels=labels,
                cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Fit Classifier – Confusion Matrix")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)
    print(f"[evaluate] Saved confusion matrix to {FIGURES_DIR}/confusion_matrix.png")


if __name__ == "__main__":
    evaluate()
