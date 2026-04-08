from pathlib import Path
import joblib
import numpy as np

try:
    from ml.preprocess import preprocess_text
except ImportError:
    from preprocess import preprocess_text

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"


def ensure_model_files():
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        try:
            from ml.train_model import train_and_save
        except ImportError:
            from train_model import train_and_save
        train_and_save()


def predict_sentiment(comment):
    ensure_model_files()

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    cleaned = preprocess_text(comment)
    vector = vectorizer.transform([cleaned])

    label = model.predict(vector)[0]
    probabilities = model.predict_proba(vector)[0]
    classes = list(model.classes_)

    probability_map = {
        cls: round(float(score), 4)
        for cls, score in zip(classes, probabilities)
    }

    return {
        "label": label,
        "confidence": round(float(np.max(probabilities)), 4),
        "probabilities": {
            "positive": probability_map.get("positive", 0.0),
            "negative": probability_map.get("negative", 0.0),
            "neutral": probability_map.get("neutral", 0.0),
        }
    }


if __name__ == "__main__":
    sample = "Magaling magturo si maam at malinaw ang examples."
    print(predict_sentiment(sample))