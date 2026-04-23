import os
import sys
import time
from pathlib import Path

from flask import Flask, redirect, session, url_for, flash, request
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from config import Config

sys.modules["app"] = sys.modules[__name__]

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "warning"

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PDF_OUTPUT_FOLDER"], exist_ok=True)

    from models.user import User
    from models.faculty import Faculty
    from models.semester import Semester
    from models.evaluation import Evaluation, Keyword

    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def session_management():
        session.permanent = True
        now = int(time.time())
        last_activity = session.get("last_activity")

        if current_user.is_authenticated:
            if last_activity and (now - last_activity) > app.config["SESSION_TIMEOUT"]:
                logout_user()
                session.clear()
                flash("Your session expired due to inactivity.", "warning")
                return redirect(url_for("auth.login"))

        session["last_activity"] = now

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "EvalSense",
            "institution_name": "Buenavista Community College, Buenavista, Bohol",
        }

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(_error):
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def not_found(_error):
        flash("Page not found.", "warning")
        return redirect(url_for("index"))

    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            sync_default_accounts()

    return app


def sync_default_accounts():
    from models.user import User

    default_accounts = [
        ("admin", None, "System Administrator", "admin", "Administration", "admin123"),
        ("student001", "2024-0001", "Student One", "student", "BSIT", "student123"),
        ("student002", "2024-0002", "Student Two", "student", "BSIT", "student123"),
        ("student003", "2024-0003", "Student Three", "student", "BSIT", "student123"),
        ("student004", "2024-0004", "Student Four", "student", "BSIT", "student123"),
        ("student005", "2024-0005", "Student Five", "student", "BSIT", "student123"),
        ("student006", "2024-0006", "Student Six", "student", "BSIT", "student123"),
        ("student007", "2024-0007", "Student Seven", "student", "BSIT", "student123"),
        ("student008", "2024-0008", "Student Eight", "student", "BSIT", "student123"),
        ("student009", "2024-0009", "Student Nine", "student", "BSIT", "student123"),
("student010", "2024-0010", "Student Ten", "student", "BSIT", "student123"),
        ("admin2", None, "Backup Administrator", "admin", "Administration", "admin123"),
    ]

    changed = False

    for username, student_id, full_name, role, department, password in default_accounts:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(
                student_id=student_id,
                full_name=full_name,
                username=username,
                role=role,
                department=department,
                is_active=True,
            )
            user.set_password(password)
            db.session.add(user)
            changed = True
        else:
            user.student_id = student_id
            user.full_name = full_name
            user.role = role
            user.department = department
            user.is_active = True
            if not user.check_password(password):
                user.set_password(password)
            changed = True

    if changed:
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)