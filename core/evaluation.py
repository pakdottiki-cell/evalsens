"""Domain rules used by the faculty-evaluation workflow."""

from decimal import Decimal, ROUND_HALF_UP


INSTRUCTIONAL_FIELDS = tuple(f"is_{number}" for number in range(1, 19))
PERSONAL_SOCIAL_FIELDS = tuple(f"ps_{number}" for number in range(1, 10))
RATING_FIELDS = INSTRUCTIONAL_FIELDS + PERSONAL_SOCIAL_FIELDS

MAX_EVALUATIONS_PER_FACULTY_PER_SEMESTER = 3
DEFAULT_SENTIMENT = "neutral"


def calculate_overall_rating(ratings: dict[str, int]) -> Decimal:
    """Return a two-decimal overall score from all required rating fields."""
    missing_fields = [field for field in RATING_FIELDS if field not in ratings]
    if missing_fields:
        raise ValueError("All evaluation rating fields are required.")

    values = [ratings[field] for field in RATING_FIELDS]
    if any(value is None or not 1 <= int(value) <= 5 for value in values):
        raise ValueError("Each evaluation rating must be between 1 and 5.")

    return Decimal(sum(values) / len(RATING_FIELDS)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
