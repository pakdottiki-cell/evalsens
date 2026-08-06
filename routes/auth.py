import re
import time
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

from models.user import User
from app import db

auth_bp = Blueprint("auth", __name__)

# Simple in-memory throttling for login attempts (per process).
# For production multi-worker deployments, move this to Redis/shared store.
_LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


def clean_input(value):
    value = (value or "").strip()
    value = re.sub(r"<.*?>", "", value)
    return value


def _client_key(role: str) -> str:
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    if "," in ip:
        ip = ip.split(",")[0].strip()
    return f"{role}:{ip}"


def _is_locked(key: str):
    entry = _LOGIN_ATTEMPTS.get(key)
    if not entry:
        return False, 0
    now = int(time.time())
    if entry.get("locked_until", 0) > now:
        return True, max(entry["locked_until"] - now, 0)
    return False, 0


def _record_failed_attempt(key: str):
    now = int(time.time())
    entry = _LOGIN_ATTEMPTS.setdefault(key, {"count": 0, "locked_until": 0})
    if entry.get("locked_until", 0) > now:
        return
    entry["count"] += 1
    if entry["count"] >= MAX_LOGIN_ATTEMPTS:
        entry["locked_until"] = now + LOCKOUT_SECONDS
        entry["count"] = 0


def _clear_attempts(key: str):
    if key in _LOGIN_ATTEMPTS:
        del _LOGIN_ATTEMPTS[key]


# =========================
# LOGIN FORM
# =========================
class LoginForm(FlaskForm):
    identifier = StringField("Username/Student ID", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    role = HiddenField("Role", default="student", validators=[DataRequired()])
    submit = SubmitField("Login")


# =========================
# REGISTER FORM
# =========================
class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    student_id = StringField("Student ID (optional)", validators=[Length(max=20)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email (optional)", validators=[Length(max=120)])
    department = StringField("Department", validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    role = HiddenField("Role", default="student")
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken.")

    def validate_student_id(self, student_id):
        if student_id.data:
            user = User.query.filter_by(student_id=student_id.data).first()
            if user:
                raise ValidationError("Student ID already registered.")


# =========================
# LOGIN ROUTES
# =========================
@auth_bp.before_app_request
def prevent_login_page_for_authenticated_users():
    # If already logged in, never show login pages.
    if current_user.is_authenticated and request.endpoint in {"auth.student_login", "auth.admin_login", "auth.login"}:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))

    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Backward-compatible entrypoint: always send students to student login.
    return redirect(url_for("auth.student_login"))


@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))

    form = LoginForm()
    form.role.data = "student"

    if form.validate_on_submit():
        key = _client_key("student")
        locked, retry_after = _is_locked(key)
        if locked:
            flash(f"Too many failed login attempts. Try again in {retry_after} seconds.", "danger")
            return render_template(
                "auth/login.html",
                form=form,
                selected_role="student"
            )

        identifier = clean_input(form.identifier.data)
        password = form.password.data

        user = (
            User.query.filter(
                (User.username == identifier) | (User.student_id == identifier)
            )
            .filter_by(role="student", is_active=True)
            .first()
        )

        if not user or not user.check_password(password):
            _record_failed_attempt(key)
            flash("Invalid credentials. Please try again.", "danger")
            return render_template(
                "auth/login.html",
                form=form,
                selected_role="student"
            )

        _clear_attempts(key)
        login_user(user)
        flash(f"Welcome, {user.full_name}.", "success")
        return redirect(url_for("student.dashboard"))

    return render_template(
        "auth/login.html",
        form=form,
        selected_role="student"
    )


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))

    form = LoginForm()
    form.role.data = "admin"

    if form.validate_on_submit():
        key = _client_key("admin")
        locked, retry_after = _is_locked(key)
        if locked:
            flash(f"Too many failed login attempts. Try again in {retry_after} seconds.", "danger")
            return render_template(
                "auth/admin_login.html",
                form=form
            )

        identifier = clean_input(form.identifier.data)
        password = form.password.data

        user = User.query.filter_by(
            username=identifier,
            role="admin",
            is_active=True
        ).first()

        if not user or not user.check_password(password):
            _record_failed_attempt(key)
            flash("Invalid credentials. Please try again.", "danger")
            return render_template(
                "auth/admin_login.html",
                form=form
            )

        _clear_attempts(key)
        login_user(user)
        flash(f"Welcome, {user.full_name}.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "auth/admin_login.html",
        form=form
    )


# =========================
# REGISTER ROUTE
# =========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=clean_input(form.username.data),
            student_id=clean_input(form.student_id.data) if form.student_id.data else None,
            full_name=clean_input(form.full_name.data),
            email=clean_input(form.email.data) if form.email.data else None,
            role=form.role.data,
            department=clean_input(form.department.data),
            is_active=True
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))