from __future__ import annotations

from typing import Any, Dict, Tuple


VALID_LABELS = {"positive", "negative", "neutral"}


def _pick_highest(probabilities: Dict[str, Any]) -> Tuple[str, float]:
    """Pick highest probability label with deterministic tie-break."""
    # Ensure numeric probs
    cleaned = {}
    for k in ("positive", "negative", "neutral"):
        v = probabilities.get(k, 0.0)
        try:
            cleaned[k] = float(v)
        except (TypeError, ValueError):
            cleaned[k] = 0.0

    # Deterministic tie-break order: positive > neutral > negative (change if desired)
    tie_break = {"positive": 0, "neutral": 1, "negative": 2}

    best_label = None
    best_prob = None
    for label in ("positive", "negative", "neutral"):
        p = cleaned[label]
        if best_label is None:
            best_label, best_prob = label, p
            continue
        if p > best_prob:  # higher wins
            best_label, best_prob = label, p
        elif p == best_prob:
            # tie-break
            if tie_break[label] < tie_break[best_label]:
                best_label, best_prob = label, p

    return best_label or "neutral", float(best_prob or 0.0)


def normalize_prediction_to_label(prediction: Any) -> str:
    """Convert model output into one of: positive|negative|neutral.

    Accepts either the dict returned by ml.predict.predict_sentiment or any
    unexpected structure, and always returns a valid enum string.
    """
    if not isinstance(prediction, dict):
        return "neutral"

    label = prediction.get("label")
    if isinstance(label, str) and label in VALID_LABELS:
        return label

    probabilities = prediction.get("probabilities")
    if isinstance(probabilities, dict) and set(probabilities.keys()) & VALID_LABELS:
        best_label, _ = _pick_highest(probabilities)
        return best_label if best_label in VALID_LABELS else "neutral"

    # Fallback
    return "neutral"


def normalize_prediction_to_confidence(prediction: Any) -> float:
    """Best-effort numeric confidence for storage/display.

    The DB column is `confidence_score DECIMAL(5,4)` which can store up to 9.9999.
    Your ML output sometimes provides confidence as a percentage (e.g., 93.79),
    which is out of range.

    This function:
    - Accepts confidence as either 0..1 or 0..100
    - Converts 0..100 -> 0..1
    - Clamps to the DB-safe range
    """
    if not isinstance(prediction, dict):
        return 0.0

    conf = prediction.get("confidence")
    try:
        value = float(conf)
    except (TypeError, ValueError):
        return 0.0

    # If it's likely a percentage, convert to fraction.
    # (e.g., 93.79 -> 0.9379)
    if value > 1.0:
        value = value / 100.0

    # DB-safe clamp for DECIMAL(5,4) (non-negative confidence)
    if value < 0.0:
        value = 0.0
    if value > 9.9999:
        value = 9.9999

    return value

