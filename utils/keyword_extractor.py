import os
from collections import Counter, defaultdict
import re
from pathlib import Path
from wordcloud import WordCloud

from app import db
from ml.preprocess import preprocess_text
from models.evaluation import Evaluation, Keyword

GENERIC_WORDS = {
    "professor", "teacher", "subject", "class", "course", "faculty",
    "student", "students", "sir", "maam", "mam", "lesson", "lessons",
    "discussion", "topic", "topics", "school", "college", "semester",
    "instructor", "prof", "classroom"
}


def extract_keywords(faculty_id, semester_id):
    evaluations = (
        Evaluation.query.filter_by(faculty_id=faculty_id, semester_id=semester_id)
        .filter(Evaluation.comment.isnot(None))
        .all()
    )

    grouped = defaultdict(list)
    for evaluation in evaluations:
        comment = (evaluation.comment or "").strip()
        if not comment:
            continue
        sentiment = (evaluation.sentiment_label or "neutral").strip().lower()
        if sentiment not in {"positive", "negative", "neutral"}:
            sentiment = "neutral"
        grouped[sentiment].append(comment)

    result = {"positive": [], "negative": [], "neutral": []}

    for sentiment in ["positive", "negative", "neutral"]:
        phrases = []
        for comment in grouped.get(sentiment, []):
            cleaned = preprocess_text(comment)
            words = [w for w in cleaned.split() if w and re.fullmatch(r"[a-z]+", w)]
            if len(words) < 2:
                continue

            for i in range(len(words) - 1):
                first, second = words[i], words[i + 1]
                if first in GENERIC_WORDS or second in GENERIC_WORDS:
                    continue
                phrase = f"{first} {second}"
                if len(phrase) <= 4:
                    continue
                phrases.append(phrase)

        counts = Counter(phrases)
        result[sentiment] = counts.most_common(10)

    existing = Keyword.query.filter_by(faculty_id=faculty_id, semester_id=semester_id).all()
    existing_map = {(row.keyword, row.sentiment_category): row for row in existing}
    used_keys = set()

    for sentiment, items in result.items():
        for keyword, frequency in items:
            key = (keyword, sentiment)
            used_keys.add(key)

            if key in existing_map:
                existing_map[key].frequency = int(frequency)
            else:
                db.session.add(
                    Keyword(
                        faculty_id=faculty_id,
                        semester_id=semester_id,
                        keyword=keyword,
                        frequency=int(frequency),
                        sentiment_category=sentiment,
                    )
                )

    for key, row in existing_map.items():
        if key not in used_keys:
            db.session.delete(row)

    db.session.commit()
    return result


def generate_wordcloud(faculty_id, semester_id):
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "static" / "img" / "wordclouds"
    os.makedirs(output_dir, exist_ok=True)

    keyword_rows = Keyword.query.filter_by(faculty_id=faculty_id, semester_id=semester_id).all()
    if not keyword_rows:
        extract_keywords(faculty_id, semester_id)
        keyword_rows = Keyword.query.filter_by(faculty_id=faculty_id, semester_id=semester_id).all()

    frequencies = {row.keyword: row.frequency for row in keyword_rows if row.frequency > 0}
    filename = f"faculty_{faculty_id}_semester_{semester_id}.png"
    filepath = output_dir / filename

    if frequencies:
        wc = WordCloud(width=1200, height=600, background_color="white", colormap="viridis")
        wc.generate_from_frequencies(frequencies)
        wc.to_file(str(filepath))

    return f"img/wordclouds/{filename}"


def build_keyword_summary(faculty_id, semester_id, limit=10):
    return (
        Keyword.query.filter_by(faculty_id=faculty_id, semester_id=semester_id)
        .order_by(Keyword.frequency.desc(), Keyword.keyword.asc())
        .limit(limit)
        .all()
    )