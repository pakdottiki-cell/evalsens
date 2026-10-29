import re
import time
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
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
    # Forwarded headers are client controlled unless a trusted proxy middleware
    # has been configured. Use the socket peer to prevent spoofed rate-limit keys.
    ip = request.remote_addr or "unknown"
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
    password = PasswordField("Password", validators=[DataRequired(), Length(min=10, max=128)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Register")

    def validate_password(self, password):
        if len(password.data.encode("utf-8")) > 72:
            raise ValidationError("Password must be no more than 72 bytes.")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken.")

    def validate_email(self, email):
        if email.data and User.query.filter_by(email=email.data.strip()).first():
            raise ValidationError("Email already registered.")

    def validate_student_id(self, student_id):
        if student_id.data:
            user = User.query.filter_by(student_id=student_id.data).first()
            if user:
                raise ValidationError("Student ID already registered.")


class ChangePasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=10, max=128)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Change Password")

    def validate_password(self, password):
        if len(password.data.encode("utf-8")) > 72:
            raise ValidationError("Password must be no more than 72 bytes.")


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
        session.clear()
        login_user(user)
        if user.must_change_password:
            flash("Your temporary password must be changed before continuing.", "warning")
            return redirect(url_for("auth.change_password"))
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
        session.clear()
        login_user(user)
        flash(f"Welcome, {user.full_name}.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "auth/admin_login.html",
        form=form
    )


@auth_bp.route("/student/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if current_user.role != "student":
        return redirect(url_for("admin.dashboard"))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        current_user.must_change_password = False
        db.session.commit()
        flash("Your password has been changed. You can continue to Evalsense.", "success")
        return redirect(url_for("student.dashboard"))
    return render_template("auth/change_password.html", form=form)


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
            # Public registration can only create student accounts. Never trust
            # the hidden role field supplied by the browser.
            role="student",
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
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
