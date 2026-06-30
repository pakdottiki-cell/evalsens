import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC

try:
    from ml.preprocess import preprocess_text
except ImportError:
    from preprocess import preprocess_text

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATHS = [
    BASE_DIR / "dataset.csv",
    BASE_DIR / "faculty_evaluation_sentiment.csv",
]
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"
RESULTS_PATH = BASE_DIR / "training_results.json"


def evaluate_model(model_name, model, x_train, y_train, x_test, y_test):
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    result = {
        "model": model_name,
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
    }
    return result


def print_comparison_table(results):
    print("\nMODEL COMPARISON")
    print("-" * 90)
    print(f"{'Model':<30}{'Accuracy':<12}{'Precision':<12}{'Recall':<12}{'F1-Score':<12}")
    print("-" * 90)
    for row in results:
        print(
            f"{row['model']:<30}"
            f"{row['accuracy']:<12}"
            f"{row['precision']:<12}"
            f"{row['recall']:<12}"
            f"{row['f1_score']:<12}"
        )
    print("-" * 90)


def train_and_save():
    dfs = []
    for p in DATASET_PATHS:
        part = pd.read_csv(p)
        if "comment" not in part.columns or "sentiment" not in part.columns:
            raise ValueError(f"{p} must contain 'comment' and 'sentiment' columns")
        dfs.append(part[["comment", "sentiment"]])

    df = pd.concat(dfs, ignore_index=True)
    df["cleaned_comment"] = df["comment"].astype(str).apply(preprocess_text)

    x = df["cleaned_comment"]
    y = df["sentiment"]

    x_train, x_temp, y_train, y_temp = train_test_split(
        x, y, test_size=0.30, random_state=42, stratify=y
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    x_train_vec = vectorizer.fit_transform(x_train)
    x_val_vec = vectorizer.transform(x_val)
    x_test_vec = vectorizer.transform(x_test)

    nb_model = MultinomialNB()
    svm_model = SVC(kernel="linear", probability=True, random_state=42)

    nb_result = evaluate_model("Multinomial Naive Bayes", nb_model, x_train_vec, y_train, x_test_vec, y_test)
    svm_result = evaluate_model("Support Vector Machine", svm_model, x_train_vec, y_train, x_test_vec, y_test)

    results = [nb_result, svm_result]
    print_comparison_table(results)

    print(f"\nValidation set size: {len(x_val)}")
    print(f"Test set size: {len(x_test)}")

    for result in results:
        print(f"\n{result['model']} Confusion Matrix:")
        print(result["confusion_matrix"])
        print(f"\n{result['model']} Classification Report:")
        print(json.dumps(result["classification_report"], indent=2))

    winner = max(results, key=lambda item: (item["f1_score"], item["accuracy"]))

    if winner["model"] == "Multinomial Naive Bayes":
        best_model = MultinomialNB()
    else:
        best_model = SVC(kernel="linear", probability=True, random_state=42)

    best_model.fit(x_train_vec, y_train)

    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    summary = {
        "rows": int(len(df)),
        "train_size": int(len(x_train)),
        "validation_size": int(len(x_val)),
        "test_size": int(len(x_test)),
        "winner": winner["model"],
        "reason": (
            f"{winner['model']} won because it achieved the highest weighted "
            f"F1-score ({winner['f1_score']}) and strong accuracy ({winner['accuracy']})."
        ),
        "results": results,
    }

    RESULTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nWinner: {winner['model']}")
    print(f"Why: {summary['reason']}")
    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved vectorizer -> {VECTORIZER_PATH}")

    return summary


if __name__ == "__main__":
    train_and_save()