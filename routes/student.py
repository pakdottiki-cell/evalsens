import re
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

from app import db
from ml.predict import predict_sentiment
from models.evaluation import Evaluation
from models.faculty import Faculty
from models.semester import Semester
from utils.keyword_extractor import extract_keywords, generate_wordcloud

student_bp = Blueprint("student", __name__, url_prefix="/student")


def sanitize_text(value):
    value = (value or "").strip()
    value = re.sub(r"<.*?>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


class EvaluationForm(FlaskForm):
    rating_effectiveness = RadioField(
        "Teaching Effectiveness",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        coerce=int,
        validators=[DataRequired()],
    )
    rating_mastery = RadioField(
        "Subject Mastery",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        coerce=int,
        validators=[DataRequired()],
    )
    rating_communication = RadioField(
        "Communication Skills",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        coerce=int,
        validators=[DataRequired()],
    )
    rating_punctuality = RadioField(
        "Punctuality and Attendance",
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        coerce=int,
        validators=[DataRequired()],
    )
    comment = TextAreaField("Comment", validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField("Submit Evaluation")


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "student":
            logout_user()
            flash("Unauthorized access. Please sign in again.", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


def active_semester():
    return Semester.query.filter_by(is_active=True).first()


@student_bp.route("/dashboard")
@student_required
def dashboard():
    semester = active_semester()
    faculty_members = Faculty.query.filter_by(is_active=True).order_by(Faculty.full_name.asc()).all()

    submitted_ids = set()
    history = []

    if semester:
        history = (
            Evaluation.query.filter_by(student_id=current_user.id, semester_id=semester.id)
            .order_by(Evaluation.submitted_at.desc())
            .all()
        )
        submitted_ids = {item.faculty_id for item in history}

    return render_template(
        "student/dashboard.html",
        active_semester=semester,
        faculty_members=faculty_members,
        submitted_ids=submitted_ids,
        history=history,
        nav_semester=f"{semester.label} • {semester.school_year}" if semester else "No Active Semester",
    )


@student_bp.route("/evaluate/<int:faculty_id>", methods=["GET", "POST"])
@student_required
def evaluate(faculty_id):
    semester = active_semester()
    if not semester:
        flash("There is no active semester available for evaluation.", "warning")
        return redirect(url_for("student.dashboard"))

    faculty = Faculty.query.filter_by(id=faculty_id, is_active=True).first_or_404()

    existing = Evaluation.query.filter_by(
        student_id=current_user.id,
        faculty_id=faculty.id,
        semester_id=semester.id,
    ).first()

    if existing:
        flash("You already submitted an evaluation for this faculty member this semester.", "danger")
        return redirect(url_for("student.dashboard"))

    form = EvaluationForm()

    if form.validate_on_submit():
        comment = sanitize_text(form.comment.data)

        ratings = [
            form.rating_effectiveness.data,
            form.rating_mastery.data,
            form.rating_communication.data,
            form.rating_punctuality.data,
        ]

        overall = Decimal(sum(ratings) / 4).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        evaluation = Evaluation(
            student_id=current_user.id,
            faculty_id=faculty.id,
            semester_id=semester.id,
            rating_effectiveness=form.rating_effectiveness.data,
            rating_mastery=form.rating_mastery.data,
            rating_communication=form.rating_communication.data,
            rating_punctuality=form.rating_punctuality.data,
            overall_rating=overall,
            comment=comment,
            sentiment_label="neutral",
            confidence_score=0.0000,
            is_anonymous=True,
        )
        db.session.add(evaluation)
        db.session.commit()

        prediction = predict_sentiment(comment)
        evaluation.sentiment_label = prediction["label"]
        evaluation.confidence_score = prediction["confidence"]
        db.session.commit()

        extract_keywords(faculty.id, semester.id)
        generate_wordcloud(faculty.id, semester.id)

        flash("Evaluation submitted successfully.", "success")
        return redirect(url_for("student.confirmation", evaluation_id=evaluation.id))

    return render_template(
        "student/evaluate.html",
        form=form,
        faculty=faculty,
        active_semester=semester,
        nav_semester=f"{semester.label} • {semester.school_year}",
    )


@student_bp.route("/confirmation/<int:evaluation_id>")
@student_required
def confirmation(evaluation_id):
    evaluation = Evaluation.query.filter_by(id=evaluation_id, student_id=current_user.id).first_or_404()
    return render_template(
        "student/confirmation.html",
        evaluation=evaluation,
        nav_semester=f"{evaluation.semester.label} • {evaluation.semester.school_year}",
    )