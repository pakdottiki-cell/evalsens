import re
from collections import Counter
from ml.preprocess import preprocess_text

def extract_top_keywords(comments, top_n=10):
    tokens = []
    for c in comments:
        t = preprocess_text(c)
        tokens.extend(t.split())
    cnt = Counter(tokens)
    return cnt.most_common(top_n)

def _avg_18(eval_obj):
    vals = [
        getattr(eval_obj, f"is_{i}") for i in range(1, 19)
    ]
    return round(sum(vals) / len(vals), 2) if vals else 0


def _avg_9(eval_obj):
    vals = [
        getattr(eval_obj, f"ps_{i}") for i in range(1, 10)
    ]
    return round(sum(vals) / len(vals), 2) if vals else 0


def anonymize_evaluation(eval_obj):
    # Return evaluation dict without student identifying fields
    return {
        'faculty_id': eval_obj.faculty_id,
        # Derived category averages from 27-item instrument
        'avg_instructional_skills': _avg_18(eval_obj),
        'avg_personal_social': _avg_9(eval_obj),
        'comment': eval_obj.comment,
        'sentiment_label': eval_obj.sentiment_label,
        'confidence_score': eval_obj.confidence_score,
        'submitted_at': eval_obj.submitted_at
    }


