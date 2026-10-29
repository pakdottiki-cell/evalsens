import os
import secrets
import sys
import time
from datetime import timedelta
from pathlib import Path

from flask import Flask, redirect, session, url_for, flash, request
from flask_wtf.csrf import CSRFError
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import inspect, text

from config import Config
from utils.timezone_utils import format_ph, now_ph_aware, now_ph_naive

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
                return redirect(url_for("auth.student_login"))

        session["last_activity"] = now

        if (
            current_user.is_authenticated
            and current_user.role == "student"
            and current_user.must_change_password
            and request.endpoint not in {"auth.change_password", "auth.logout", "static"}
        ):
            return redirect(url_for("auth.change_password"))

    @app.before_request
    def archive_long_inactive_students():
        now = time.time()
        if now - app.extensions.get("student_archive_checked_at", 0) < 86400:
            return

        from models.user import User

        cutoff = now_ph_naive() - timedelta(days=365)
        expired_students = User.query.filter(
            User.role == "student",
            User.is_active.is_(False),
            User.inactive_since.isnot(None),
            User.inactive_since <= cutoff,
        ).all()

        archived_ids = set()
        for student in expired_students:
            # Remove login access and identifying details while retaining the
            # linked evaluation rows used by faculty reports.
            student.username = f"archived-{student.id}-{secrets.token_hex(8)}"
            student.student_id = None
            student.full_name = f"Archived Student {student.id}"
            student.email = None
            student.password_hash = bcrypt.generate_password_hash(
                secrets.token_urlsafe(32)
            ).decode("utf-8")
            student.role = "archived_student"
            student.department = "Archived"
            student.inactive_since = None
            archived_ids.add(student.id)

        if expired_students:
            db.session.commit()
            if current_user.is_authenticated and current_user.id in archived_ids:
                logout_user()
                session.clear()
                flash("Your inactive account has been archived.", "warning")
        app.extensions["student_archive_checked_at"] = now

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "connect-src 'self' https:;"
        )
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "EvalSense",
            "institution_name": "Buenavista Community College, Buenavista, Bohol",
            "format_ph": format_ph,
            "now_ph": now_ph_aware,
        }

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.dashboard"))
        return redirect(url_for("auth.student_login"))

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        flash("Your form session expired or token is invalid. Please try again.", "warning")
        if request.path.startswith("/register"):
            return redirect(url_for("auth.register"))
        if request.path.startswith("/admin"):
            return redirect(url_for("auth.admin_login"))
        return redirect(url_for("auth.student_login"))

    @app.errorhandler(403)
    def forbidden(_error):
        flash("Access denied.", "danger")
        # Send users back to the appropriate login page.
        if current_user.is_authenticated and current_user.role == "admin":
            return redirect(url_for("auth.admin_login"))
        return redirect(url_for("auth.student_login"))

    @app.errorhandler(404)
    def not_found(_error):
        flash("Page not found.", "warning")
        return redirect(url_for("index"))

    with app.app_context():
        try:
            db.create_all()
            if "inactive_since" not in {
                column["name"] for column in inspect(db.engine).get_columns("users")
            }:
                with db.engine.begin() as connection:
                    connection.execute(
                        text("ALTER TABLE users ADD COLUMN inactive_since DATETIME NULL")
                    )
                    connection.execute(text(
                        "UPDATE users SET inactive_since = CURRENT_TIMESTAMP "
                        "WHERE role = 'student' AND is_active = 0 AND inactive_since IS NULL"
                    ))
            if "must_change_password" not in {
                column["name"] for column in inspect(db.engine).get_columns("users")
            }:
                with db.engine.begin() as connection:
                    connection.execute(text(
                        "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0"
                    ))
            if "data_visible_after" not in {
                column["name"] for column in inspect(db.engine).get_columns("faculty")
            }:
                with db.engine.begin() as connection:
                    connection.execute(text(
                        "ALTER TABLE faculty ADD COLUMN data_visible_after DATETIME NULL"
                    ))
        except Exception as e:
            # Typical cause: database/schema.sql is out-of-sync with models.
            # For example: missing column `users.username`.
            msg = str(e)
            if "users.username" in msg or "Unknown column" in msg:
                print("[DB SCHEMA MISMATCH]", msg)
                print("Your MySQL schema appears out of sync with SQLAlchemy models.")
                print("Rebuild DB using:")
                print("  - database/schema.sql")
                print("  - database/seed.sql only for isolated demo data")
            else:
                raise

    return app


app = create_app()

if __name__ == "__main__":
    debug_enabled = os.getenv("FLASK_DEBUG", "0") in {"1", "true", "True"}
    app.run(debug=debug_enabled, use_reloader=False)
