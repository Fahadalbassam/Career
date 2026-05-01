"""
train_model.py – Train and save a TF-IDF + Logistic Regression fit classifier.

Run after build_training_data.py has been executed.

Output:
    models/fit_classifier.joblib
    models/tfidf_vectorizer.joblib
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRAINING_FILE = PROCESSED_DIR / "training_fit_dataset.csv"
CLASSIFIER_FILE = MODELS_DIR / "fit_classifier.joblib"
VECTORIZER_FILE = MODELS_DIR / "tfidf_vectorizer.joblib"


def build_text_feature(row: pd.Series) -> str:
    """Concatenate text fields into a single feature string."""
    parts = [
        str(row.get("title", "")),
        str(row.get("company", "")),
        str(row.get("program_type", "")),
        str(row.get("student_major", "")),
    ]
    return " ".join(p for p in parts if p)


def train() -> None:
    """Load training data, train the classifier, and persist artefacts."""
    if not TRAINING_FILE.exists():
        print("[train_model] Training file not found. Run build_training_data.py first.")
        return

    print("[train_model] Loading training data …")
    df = pd.read_csv(TRAINING_FILE)

    df["text"] = df.apply(build_text_feature, axis=1)
    X = df["text"]
    y = df["fit_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[train_model] Fitting TF-IDF vectorizer …")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print("[train_model] Training Logistic Regression classifier …")
    clf = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
    clf.fit(X_train_vec, y_train)

    print("[train_model] Evaluation on test set:")
    y_pred = clf.predict(X_test_vec)
    print(classification_report(y_test, y_pred))

    print("[train_model] Saving model artefacts …")
    joblib.dump(clf, CLASSIFIER_FILE)
    joblib.dump(vectorizer, VECTORIZER_FILE)
    print(f"[train_model] Saved: {CLASSIFIER_FILE}, {VECTORIZER_FILE}")


if __name__ == "__main__":
    train()
