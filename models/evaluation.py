from datetime import datetime
from app import db


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    # A) Instructional Skills (18 items)
    is_1 = db.Column(db.Integer, nullable=False)
    is_2 = db.Column(db.Integer, nullable=False)
    is_3 = db.Column(db.Integer, nullable=False)
    is_4 = db.Column(db.Integer, nullable=False)
    is_5 = db.Column(db.Integer, nullable=False)
    is_6 = db.Column(db.Integer, nullable=False)
    is_7 = db.Column(db.Integer, nullable=False)
    is_8 = db.Column(db.Integer, nullable=False)
    is_9 = db.Column(db.Integer, nullable=False)
    is_10 = db.Column(db.Integer, nullable=False)
    is_11 = db.Column(db.Integer, nullable=False)
    is_12 = db.Column(db.Integer, nullable=False)
    is_13 = db.Column(db.Integer, nullable=False)
    is_14 = db.Column(db.Integer, nullable=False)
    is_15 = db.Column(db.Integer, nullable=False)
    is_16 = db.Column(db.Integer, nullable=False)
    is_17 = db.Column(db.Integer, nullable=False)
    is_18 = db.Column(db.Integer, nullable=False)

    # B) Personal and Social Qualities (9 items)
    ps_1 = db.Column(db.Integer, nullable=False)
    ps_2 = db.Column(db.Integer, nullable=False)
    ps_3 = db.Column(db.Integer, nullable=False)
    ps_4 = db.Column(db.Integer, nullable=False)
    ps_5 = db.Column(db.Integer, nullable=False)
    ps_6 = db.Column(db.Integer, nullable=False)
    ps_7 = db.Column(db.Integer, nullable=False)
    ps_8 = db.Column(db.Integer, nullable=False)
    ps_9 = db.Column(db.Integer, nullable=False)


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