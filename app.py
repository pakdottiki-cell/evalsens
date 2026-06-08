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
                return redirect(url_for("auth.student_login"))


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
        db.create_all()
        try:
            if User.query.count() == 0:
                # Import and seed default accounts when database is empty.
                # diagnose_auth imports app.db at module import-time, so avoid importing it at startup
                # until after app/db are fully initialized.
                import diagnose_auth

                diagnose_auth.setup_test_users()
        except Exception as e:
            # Typical cause: database/schema.sql is out-of-sync with models.
            # For example: missing column `users.username`.
            msg = str(e)
            if "users.username" in msg or "Unknown column" in msg:
                print("[DB SCHEMA MISMATCH]", msg)
                print("Your MySQL schema appears out of sync with SQLAlchemy models.")
                print("Rebuild DB using:")
                print("  - database/schema.sql")
                print("  - database/seed.sql (optional but recommended)")
            else:
                raise


    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)