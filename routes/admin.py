import re
from collections import Counter
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from app import db
from models.evaluation import Evaluation
from models.faculty import Faculty
from models.semester import Semester
from models.user import User
from utils.keyword_extractor import build_keyword_summary, extract_keywords, generate_wordcloud
from utils.pdf_generator import build_all_reports_pdf, build_faculty_report_pdf


def _avg_instructional(eval_obj):
    return sum(getattr(eval_obj, f"is_{i}") for i in range(1, 19)) / 18


def _avg_personal_social(eval_obj):
    return sum(getattr(eval_obj, f"ps_{i}") for i in range(1, 10)) / 9


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def sanitize_text(value):
    value = (value or "").strip()
    value = re.sub(r"<.*?>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            logout_user()
            flash("Unauthorized access. Please sign in again.", "danger")
            return redirect(url_for("auth.admin_login"))
        return view_func(*args, **kwargs)
    return wrapper


class FacultyForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=100)])
    department = StringField("Department", validators=[DataRequired(), Length(min=2, max=100)])
    position = StringField("Position", validators=[Optional(), Length(max=100)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Faculty")


class SemesterForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=20)])
    school_year = StringField("School Year", validators=[DataRequired(), Length(max=20)])
    start_date = DateField("Start Date", validators=[Optional()])
    end_date = DateField("End Date", validators=[Optional()])
    is_active = BooleanField("Set as active semester", default=False)
    submit = SubmitField("Save Semester")


def get_selected_semester(semester_id):
    if semester_id:
        return Semester.query.get(semester_id)
    return Semester.query.filter_by(is_active=True).first() or Semester.query.order_by(Semester.id.desc()).first()


def sentiment_percentages(evaluations):
    total = len(evaluations)
    if total == 0:
        return {"positive": 0, "negative": 0, "neutral": 0}
    counts = Counter([row.sentiment_label for row in evaluations])
    return {
        "positive": round((counts.get("positive", 0) / total) * 100, 2),
        "negative": round((counts.get("negative", 0) / total) * 100, 2),
        "neutral": round((counts.get("neutral", 0) / total) * 100, 2),
    }


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    semester_id = request.args.get("semester_id", type=int)
    selected_semester = get_selected_semester(semester_id)
    semester_options = Semester.query.order_by(Semester.id.desc()).all()

    query = Evaluation.query
    if selected_semester:
        query = query.filter_by(semester_id=selected_semester.id)

    evaluations = query.all()
    sentiment = sentiment_percentages(evaluations)
    total_evaluations = len(evaluations)
    faculty_evaluated = len({item.faculty_id for item in evaluations})

    total_students = User.query.filter_by(role="student", is_active=True).count()
    total_faculty = Faculty.query.filter_by(is_active=True).count()
    pending_count = max((total_students * total_faculty) - total_evaluations, 0)

    top_rated = []
    for faculty in Faculty.query.filter_by(is_active=True).order_by(Faculty.full_name.asc()).all():
        faculty_query = Evaluation.query.filter_by(faculty_id=faculty.id)
        if selected_semester:
            faculty_query = faculty_query.filter_by(semester_id=selected_semester.id)
        faculty_evals = faculty_query.all()
        if not faculty_evals:
            continue
        avg_rating = round(sum(float(e.overall_rating) for e in faculty_evals) / len(faculty_evals), 2)
        sentiment_counts = Counter([e.sentiment_label for e in faculty_evals])
        dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)

        top_rated.append({
            "faculty": faculty,
            "average_rating": avg_rating,
            "dominant_sentiment": dominant_sentiment,
        })

    top_rated.sort(key=lambda x: x["average_rating"], reverse=True)

    return render_template(
        "admin/dashboard.html",
        selected_semester=selected_semester,
        semester_options=semester_options,
        total_evaluations=total_evaluations,
        faculty_evaluated=faculty_evaluated,
        positive_pct=sentiment["positive"],
        pending_count=pending_count,
        top_rated=top_rated[:10],
        nav_semester=f"{selected_semester.label} • {selected_semester.school_year}" if selected_semester else "No Active Semester",
    )


@admin_bp.route("/sentiment")
@admin_required
def sentiment():
    faculty_id = request.args.get("faculty_id", type=int)
    semester_id = request.args.get("semester_id", type=int)

    faculty_options = Faculty.query.order_by(Faculty.full_name.asc()).all()
    semester_options = Semester.query.order_by(Semester.id.desc()).all()
    selected_semester = get_selected_semester(semester_id)

    query = Evaluation.query
    if faculty_id:
        query = query.filter_by(faculty_id=faculty_id)
    if selected_semester:
        query = query.filter_by(semester_id=selected_semester.id)

    evaluations = query.order_by(Evaluation.submitted_at.desc()).all()
    sentiment_values = sentiment_percentages(evaluations)

    return render_template(
        "admin/sentiment.html",
        faculty_options=faculty_options,
        semester_options=semester_options,
        selected_faculty_id=faculty_id,
        selected_semester_id=selected_semester.id if selected_semester else None,
        positive_pct=sentiment_values["positive"],
        neutral_pct=sentiment_values["neutral"],
        negative_pct=sentiment_values["negative"],
        sample_comments=evaluations[:10],
        nav_semester=f"{selected_semester.label} • {selected_semester.school_year}" if selected_semester else "No Active Semester",
    )


@admin_bp.route("/keywords")
@admin_required
def keywords():
    faculty_id = request.args.get("faculty_id", type=int)
    semester_id = request.args.get("semester_id", type=int)

    faculty_options = Faculty.query.order_by(Faculty.full_name.asc()).all()
    semester_options = Semester.query.order_by(Semester.id.desc()).all()
    selected_faculty = Faculty.query.get(faculty_id) if faculty_id else None
    selected_semester = get_selected_semester(semester_id)

    positive_keywords = []
    negative_keywords = []
    neutral_keywords = []
    wordcloud_path = None

    if selected_faculty and selected_semester:
        keyword_data = extract_keywords(selected_faculty.id, selected_semester.id)
        positive_keywords = keyword_data.get("positive", [])
        negative_keywords = keyword_data.get("negative", [])
        neutral_keywords = keyword_data.get("neutral", [])
        wordcloud_path = generate_wordcloud(selected_faculty.id, selected_semester.id)

    return render_template(
        "admin/keywords.html",
        faculty_options=faculty_options,
        semester_options=semester_options,
        selected_faculty=selected_faculty,
        selected_semester=selected_semester,
        positive_keywords=positive_keywords,
        negative_keywords=negative_keywords,
        neutral_keywords=neutral_keywords,
        wordcloud_path=wordcloud_path,
        nav_semester=f"{selected_semester.label} • {selected_semester.school_year}" if selected_semester else "No Active Semester",
    )


@admin_bp.route("/reports")
@admin_required
def reports():
    semester_id = request.args.get("semester_id", type=int)
    selected_semester = get_selected_semester(semester_id)
    semester_options = Semester.query.order_by(Semester.id.desc()).all()

    faculty_rows = []

    for faculty in Faculty.query.order_by(Faculty.full_name.asc()).all():
        query = Evaluation.query.filter_by(faculty_id=faculty.id)
        if selected_semester:
            query = query.filter_by(semester_id=selected_semester.id)
        evaluations = query.order_by(Evaluation.submitted_at.desc()).all()

        if not evaluations:
            continue

        sentiment = sentiment_percentages(evaluations)
        avg_rating = round(sum(float(e.overall_rating) for e in evaluations) / len(evaluations), 2)

        extract_keywords(faculty.id, selected_semester.id)
        keywords = build_keyword_summary(faculty.id, selected_semester.id, limit=10)

        faculty_rows.append({
            "faculty_id": faculty.id,
            "faculty_name": faculty.full_name,
            "department": faculty.department,
            "average_rating": avg_rating,
            "positive_pct": sentiment["positive"],
            "negative_pct": sentiment["negative"],
            "neutral_pct": sentiment["neutral"],
            "total_comments": len([e for e in evaluations if e.comment]),
            "avg_instructional": round(sum(_avg_instructional(e) for e in evaluations) / len(evaluations), 2),
            "avg_personal_social": round(sum(_avg_personal_social(e) for e in evaluations) / len(evaluations), 2),

            "keywords": keywords,
            "sample_comments": evaluations[:5],
        })

    return render_template(
        "admin/reports.html",
        semester_options=semester_options,
        selected_semester=selected_semester,
        faculty_rows=faculty_rows,
        nav_semester=f"{selected_semester.label} • {selected_semester.school_year}" if selected_semester else "No Active Semester",
    )


@admin_bp.route("/reports/faculty/<int:faculty_id>/download")
@admin_required
def download_faculty_report(faculty_id):
    semester_id = request.args.get("semester_id", type=int)
    selected_semester = get_selected_semester(semester_id)
    pdf_buffer, filename = build_faculty_report_pdf(faculty_id, selected_semester.id)
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@admin_bp.route("/reports/download-all")
@admin_required
def download_all_reports():
    semester_id = request.args.get("semester_id", type=int)
    selected_semester = get_selected_semester(semester_id)
    pdf_buffer, filename = build_all_reports_pdf(selected_semester.id)
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@admin_bp.route("/faculty", methods=["GET", "POST"])
@admin_required
def faculty():
    faculty_form = FacultyForm(prefix="faculty")
    semester_form = SemesterForm(prefix="semester")

    if faculty_form.submit.data and faculty_form.validate_on_submit():
        new_faculty = Faculty(
            full_name=sanitize_text(faculty_form.full_name.data),
            department=sanitize_text(faculty_form.department.data),
            position=sanitize_text(faculty_form.position.data),
            is_active=faculty_form.is_active.data,
        )
        db.session.add(new_faculty)
        db.session.commit()
        flash("Faculty member added successfully.", "success")
        return redirect(url_for("admin.faculty"))

    if semester_form.submit.data and semester_form.validate_on_submit():
        if semester_form.is_active.data:
            Semester.query.update({"is_active": False})

        new_semester = Semester(
            label=sanitize_text(semester_form.label.data),
            school_year=sanitize_text(semester_form.school_year.data),
            start_date=semester_form.start_date.data,
            end_date=semester_form.end_date.data,
            is_active=semester_form.is_active.data,
        )
        db.session.add(new_semester)
        db.session.commit()
        flash("Semester saved successfully.", "success")
        return redirect(url_for("admin.faculty"))

    faculty_members = Faculty.query.order_by(Faculty.created_at.desc()).all()
    semesters = Semester.query.order_by(Semester.id.desc()).all()
    active = Semester.query.filter_by(is_active=True).first()

    return render_template(
        "admin/faculty.html",
        faculty_form=faculty_form,
        semester_form=semester_form,
        faculty_members=faculty_members,
        semesters=semesters,
        nav_semester=f"{active.label} • {active.school_year}" if active else "No Active Semester",
    )


@admin_bp.route("/faculty/<int:faculty_id>/toggle")
@admin_required
def toggle_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    faculty.is_active = not faculty.is_active
    db.session.commit()
    flash("Faculty status updated.", "success")
    return redirect(url_for("admin.faculty"))


@admin_bp.route("/semester/<int:semester_id>/activate")
@admin_required
def activate_semester(semester_id):
    Semester.query.update({"is_active": False})
    semester = Semester.query.get_or_404(semester_id)
    semester.is_active = True
    db.session.commit()
    flash("Semester activated successfully.", "success")
    return redirect(url_for("admin.faculty"))