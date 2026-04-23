from datetime import datetime
from app import db


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    rating_effectiveness = db.Column(db.Integer, nullable=False)
    rating_mastery = db.Column(db.Integer, nullable=False)
    rating_communication = db.Column(db.Integer, nullable=False)
    rating_punctuality = db.Column(db.Integer, nullable=False)

    overall_rating = db.Column(db.Numeric(3, 2), nullable=False)
    comment = db.Column(db.Text, nullable=False)

    sentiment_label = db.Column(
        db.Enum("positive", "negative", "neutral", name="sentiment_label_enum"),
        nullable=False
    )

    is_anonymous = db.Column(db.Boolean, default=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Evaluation {self.id}>"


class Keyword(db.Model):
    __tablename__ = "keywords"

    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)
    keyword = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.Integer, nullable=False, default=0)
    sentiment_category = db.Column(
        db.Enum("positive", "negative", "neutral", name="keyword_sentiment_enum"),
        nullable=False
    )
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Keyword {self.keyword}>"