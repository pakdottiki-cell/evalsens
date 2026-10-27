from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, bcrypt
from utils.timezone_utils import now_ph_naive

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False, index=True)
    department = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=now_ph_naive)
    inactive_since = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password exceeds bcrypt's 72-byte limit.")
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        if len(password.encode("utf-8")) > 72:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_role_label(self):
        return {'student': 'Student', 'admin': 'Administrator'}[self.role]
