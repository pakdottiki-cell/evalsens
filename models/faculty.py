from datetime import datetime
from app import db


class Faculty(db.Model):
    __tablename__ = "faculty"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    evaluations = db.relationship("Evaluation", backref="faculty", lazy=True, cascade="all, delete-orphan")
    keywords = db.relationship("Keyword", backref="faculty", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Faculty {self.full_name}>"