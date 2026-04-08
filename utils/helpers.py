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

def anonymize_evaluation(eval_obj):
    # Return evaluation dict without student identifying fields
    return {
        'faculty_id': eval_obj.faculty_id,
        'rating_effectiveness': eval_obj.rating_effectiveness,
        'rating_mastery': eval_obj.rating_mastery,
        'rating_communication': eval_obj.rating_communication,
        'rating_punctuality': eval_obj.rating_punctuality,
        'comment': eval_obj.comment,
        'sentiment_label': eval_obj.sentiment_label,
        'confidence_score': eval_obj.confidence_score,
        'submitted_at': eval_obj.submitted_at
    }
