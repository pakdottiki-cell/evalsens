from app import db


class Semester(db.Model):
    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(20), nullable=True)
    school_year = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    evaluations = db.relationship("Evaluation", backref="semester", lazy=True, cascade="all, delete-orphan")
    keywords = db.relationship("Keyword", backref="semester", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Semester {self.label} {self.school_year}>"