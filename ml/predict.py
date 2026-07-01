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


# NOTE: We intentionally do NOT apply additional neutral-forcing thresholds here.
# The model is trained directly on the dataset's sentiment classes: positive|negative|neutral.





POSITIVE_CUE_WORDS = {
    "clear",
    "clearly",
    "interesting",
    "engaging",
    "helpful",
    "good",
    "great",
    "excellent",
    "well",
    "effective",
    "understandable",
    "easy",
    "nice",
    "best",
    "amazing",
    "awesome",
    "love",
    "liked",
    "organized",
    "knowledgeable",
    "patient",
}


def _has_positive_cues(text: str) -> bool:
    t = f" {str(text).lower()} "
    return any(f" {w} " in t for w in POSITIVE_CUE_WORDS)


def predict_sentiment(comment):
    ensure_model_files()

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    cleaned = preprocess_text(comment)
    vector = vectorizer.transform([cleaned])

    # Use probabilities from the trained model.
    probabilities = model.predict_proba(vector)[0]

    classes = list(model.classes_)

    # Build a probability map in the model's own label space.
    raw_prob_map = {cls: float(prob) for cls, prob in zip(classes, probabilities)}

    # DB enum is: positive|negative|neutral (dataset.csv matches this).
    # If model was trained with different labels, map them; otherwise use directly.
    label_map = {
        "pos": "positive",
        "neg": "negative",
        "neu": "neutral",
        "Pos": "positive",
        "Neg": "negative",
        "Neu": "neutral",
        "Positive": "positive",
        "Negative": "negative",
        "Neutral": "neutral",
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral",
    }

    normalized_prob_map = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    for raw_label, prob in raw_prob_map.items():
        db_label = label_map.get(raw_label, raw_label)
        if db_label in normalized_prob_map:
            normalized_prob_map[db_label] += prob

    # Choose top class, with a conservative disambiguation for borderline neutral-vs-positive.
    sorted_items = sorted(normalized_prob_map.items(), key=lambda kv: kv[1], reverse=True)
    top_label, top_prob = sorted_items[0]

    # If neutral is only slightly above positive, and positive cues exist in text,
    # prefer positive to reduce false-neutral outcomes on comments like:
    # "he explain topics clearly and makes it interesting"
    if top_label == "neutral":
        positive_prob = normalized_prob_map["positive"]
        negative_prob = normalized_prob_map["negative"]
        margin = float(top_prob) - float(positive_prob)

        # Rescue positive-leaning comments that the model marks neutral.
        # For this project goal, prioritize positive when clear positive cues are present
        # and neutral is not overwhelmingly dominant.
        if _has_positive_cues(comment) and (
            margin <= 0.30 or (positive_prob >= 0.22 and negative_prob < 0.35)
        ):
            top_label = "positive"
            top_prob = max(positive_prob, top_prob)

    confidence_pct = round(float(top_prob) * 100, 2)

    return {
        "label": top_label,
        "confidence": confidence_pct,
        "probabilities": {
            "positive": round(normalized_prob_map["positive"], 4),
            "negative": round(normalized_prob_map["negative"], 4),
            "neutral": round(normalized_prob_map["neutral"], 4),
        },
    }






if __name__ == "__main__":
    sample = "Magaling magturo si maam at malinaw ang examples."
    print(predict_sentiment(sample))