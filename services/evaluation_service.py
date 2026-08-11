"""Business service for safely recording a student evaluation."""

import re

from app import db
from core.evaluation import (
    DEFAULT_SENTIMENT,
    MAX_EVALUATIONS_PER_FACULTY_PER_SEMESTER,
    RATING_FIELDS,
    calculate_overall_rating,
)
from ml.predict import predict_sentiment
from models.evaluation import Evaluation
from utils.keyword_extractor import extract_keywords, generate_wordcloud
from utils.sentiment_utils import normalize_prediction_to_confidence, normalize_prediction_to_label


class EvaluationLimitReached(Exception):
    """Raised when a student has reached the permitted evaluation count."""


def sanitize_text(value: str) -> str:
    """Normalize free-text submitted from the evaluation form."""
    value = (value or "").strip()
    value = re.sub(r"<.*?>", "", value)
    return re.sub(r"\s+", " ", value)


def _best_sentiment_label(prediction: object, normalized_label: str) -> str:
    """Prefer a non-neutral label when classifier probabilities clearly support it."""
    if normalized_label != DEFAULT_SENTIMENT or not isinstance(prediction, dict):
        return normalized_label

    probabilities = prediction.get("probabilities")
    if not isinstance(probabilities, dict):
        return normalized_label

    positive = float(probabilities.get("positive", 0) or 0)
    negative = float(probabilities.get("negative", 0) or 0)
    neutral = float(probabilities.get("neutral", 0) or 0)
    if negative >= neutral and negative > positive:
        return "negative"
    if positive >= neutral and positive > negative:
        return "positive"
    return normalized_label


def submit_evaluation(*, student_id: int, faculty_id: int, semester_id: int, subject: str,
                      comment: str, ratings: dict[str, int]) -> Evaluation:
    """Create, classify, and finalize an evaluation as one coordinated workflow."""
    existing_count = Evaluation.query.filter_by(
        student_id=student_id, faculty_id=faculty_id, semester_id=semester_id
    ).count()
    if existing_count >= MAX_EVALUATIONS_PER_FACULTY_PER_SEMESTER:
        raise EvaluationLimitReached

    clean_comment = sanitize_text(comment)
    evaluation = Evaluation(
        student_id=student_id,
        faculty_id=faculty_id,
        semester_id=semester_id,
        subject=sanitize_text(subject),
        comment=clean_comment,
        overall_rating=calculate_overall_rating(ratings),
        sentiment_label=DEFAULT_SENTIMENT,
        is_anonymous=True,
        **{field: ratings[field] for field in RATING_FIELDS},
    )
    db.session.add(evaluation)
    db.session.flush()

    prediction = predict_sentiment(clean_comment)
    label = normalize_prediction_to_label(prediction)
    evaluation.sentiment_label = _best_sentiment_label(prediction, label)
    evaluation.confidence_score = normalize_prediction_to_confidence(prediction)

    db.session.commit()
    extract_keywords(faculty_id, semester_id)
    generate_wordcloud(faculty_id, semester_id)
    return evaluation
