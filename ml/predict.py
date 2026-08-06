from pathlib import Path
import hashlib
import joblib
import numpy as np

from config import Config

try:
    from ml.preprocess import preprocess_text, tokenize_text
except ImportError:
    from preprocess import preprocess_text, tokenize_text

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
VECTORIZER_PATH = BASE_DIR / "vectorizer.pkl"


def _sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_artifact_hash(path: Path, expected_hash: str, label: str):
    if not expected_hash:
        return
    actual = _sha256_of_file(path)
    if actual.lower() != expected_hash.lower().strip():
        raise RuntimeError(f"{label} integrity check failed. Expected SHA-256 does not match.")


def ensure_model_files():
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        try:
            from ml.train_model import train_and_save
        except ImportError:
            from train_model import train_and_save
        train_and_save()

    # Optional integrity checks (configured via env in config.Config).
    _validate_artifact_hash(MODEL_PATH, Config.MODEL_SHA256, "Model artifact")
    _validate_artifact_hash(VECTORIZER_PATH, Config.VECTORIZER_SHA256, "Vectorizer artifact")


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

NEGATIVE_CUE_WORDS = {
    "confusing",
    "unclear",
    "boring",
    "late",
    "rude",
    "bad",
    "poor",
    "terrible",
    "difficult",
    "hard",
    "disorganized",
    "unprepared",
    "slow",
    "inconsistent",
    "ineffective",
    "worst",
}


def _cue_scores(tokens):
    pos = 0
    neg = 0
    for tok in tokens:
        if tok in POSITIVE_CUE_WORDS:
            pos += 1
        elif tok in NEGATIVE_CUE_WORDS:
            neg += 1
        elif tok.startswith("not_"):
            base = tok[4:]
            if base in POSITIVE_CUE_WORDS:
                neg += 1
            elif base in NEGATIVE_CUE_WORDS:
                pos += 1
    return pos, neg


def predict_sentiment(comment):
    ensure_model_files()

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    tokens = tokenize_text(comment)
    cleaned = " ".join(tokens) if tokens else preprocess_text(comment)
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

    # Use token-level sentiment cues to reduce neutral over-prediction.
    pos_cues, neg_cues = _cue_scores(tokens)
    positive_prob = normalized_prob_map["positive"]
    negative_prob = normalized_prob_map["negative"]
    neutral_prob = normalized_prob_map["neutral"]

    if top_label == "neutral":
        if pos_cues > neg_cues and (neutral_prob - positive_prob) <= 0.35:
            top_label = "positive"
            top_prob = max(positive_prob, top_prob)
        elif neg_cues > pos_cues and (neutral_prob - negative_prob) <= 0.35:
            top_label = "negative"
            top_prob = max(negative_prob, top_prob)

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