import re
from collections import Counter
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, logout_user
from flask_wtf import FlaskForm
from sqlalchemy import func, or_
from wtforms import BooleanField, DateField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, ValidationError

from app import db
from models.evaluation import Evaluation
from models.evaluation import visible_evaluations
from models.faculty import Faculty
from models.semester import Semester
from models.user import User
from utils.keyword_extractor import (
    build_keyword_summary,
    extract_comment_keywords,
    extract_keywords,
    generate_wordcloud,
)
from utils.pdf_generator import build_all_reports_pdf, build_faculty_report_pdf
from utils.recommendations import generate_recommendations
from utils.timezone_utils import now_ph_naive

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


FACULTY_DEPARTMENT_CHOICES = [(code, code) for code in ("COTE", "CITE", "COHTM", "CCJE")]


class FacultyForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=100)])
    department = SelectField("Department", choices=FACULTY_DEPARTMENT_CHOICES, validators=[DataRequired()])
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


COURSE_CHOICES = [
    ("BSED Eng", "Bachelor of Secondary Education major in English"),
    ("BSED Math", "Bachelor of Secondary Education major in Math"),
    ("BEED", "Bachelor of Elementary Education"),
    ("BSCrim", "Bachelor of Science in Criminology"),
    ("BSHM", "Bachelor of Science in Hospitality Management (BSHM)"),
    ("BSTourism", "Bachelor of Science in Tourism Management"),
    ("BSIT", "Bachelor of Science in Information Technology"),
]


class StudentAccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    student_id = StringField("Student ID", validators=[Optional(), Length(max=20)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[Optional(), Length(max=120)])
    department = SelectField("Course", choices=COURSE_CHOICES, validators=[DataRequired()])
    password = PasswordField("Password", validators=[Optional(), Length(min=10, max=128)])
    confirm_password = PasswordField("Confirm Password", validators=[EqualTo("password", message="Passwords must match.")])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Student")

    def validate_password(self, password):
        if password.data and len(password.data.encode("utf-8")) > 72:
            raise ValidationError("Password must be no more than 72 bytes.")


class StudentPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=10, max=128)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")])
    submit = SubmitField("Reset Password")

    def validate_password(self, password):
        if len(password.data.encode("utf-8")) > 72:
            raise ValidationError("Password must be no more than 72 bytes.")


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


def _student_duplicate(field_name, value, student_id=None):
    value = sanitize_text(value)
    if not value:
        return False

    query = User.query.filter(getattr(User, field_name) == value)
    if student_id:
        query = query.filter(User.id != student_id)

    return query.first() is not None


def _validate_student_uniques(form, student_id=None):
    has_error = False

    if _student_duplicate("username", form.username.data, student_id):
        form.username.errors.append("Username already taken.")
        has_error = True

    if form.student_id.data and _student_duplicate("student_id", form.student_id.data, student_id):
        form.student_id.errors.append("Student ID already registered.")
        has_error = True

    if form.email.data and _student_duplicate("email", form.email.data, student_id):
        form.email.errors.append("Email already registered.")
        has_error = True

    return not has_error


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    semester_id = request.args.get("semester_id", type=int)
    selected_semester = get_selected_semester(semester_id)
    semester_options = Semester.query.order_by(Semester.id.desc()).all()

    query = visible_evaluations(Evaluation.query)
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
        faculty_query = visible_evaluations(Evaluation.query).filter_by(faculty_id=faculty.id)
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


@admin_bp.route("/students", methods=["GET", "POST"])
@admin_required
def students():
    create_form = StudentAccountForm()

    if create_form.validate_on_submit() and _validate_student_uniques(create_form):
        if not create_form.password.data:
            create_form.password.errors.append("Password is required for new student accounts.")
        else:
            student = User(
                username=sanitize_text(create_form.username.data),
                student_id=sanitize_text(create_form.student_id.data) or None,
                full_name=sanitize_text(create_form.full_name.data),
                email=sanitize_text(create_form.email.data) or None,
                role="student",
                department=create_form.department.data,
                is_active=create_form.is_active.data,
            )
            student.set_password(create_form.password.data)
            db.session.add(student)
            db.session.commit()
            flash("Student account created successfully.", "success")
            return redirect(url_for("admin.students"))

    elif request.method == "POST":
        flash("Please review the student account form.", "danger")

    search = sanitize_text(request.args.get("q"))
    status = request.args.get("status", "all")
    department = sanitize_text(request.args.get("department")) or "all"

    query = User.query.filter_by(role="student")
    if search:
        like_value = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(like_value),
                User.username.ilike(like_value),
                User.student_id.ilike(like_value),
                User.email.ilike(like_value),
                User.department.ilike(like_value),
            )
        )

    if department != "all":
        query = query.filter(User.department == department)

    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)

    query = query.order_by(User.date_created.desc(), User.full_name.asc())
    student_total = query.count()
    show_all_students = request.args.get("show_all") == "1"
    student_accounts = query.all() if show_all_students else query.limit(15).all()
    evaluation_counts = dict(
        db.session.query(Evaluation.student_id, db.func.count(Evaluation.id))
        .group_by(Evaluation.student_id)
        .all()
    )
    active = Semester.query.filter_by(is_active=True).first()
    departments = [
        row[0]
        for row in db.session.query(User.department)
        .filter(User.role == "student", User.department.isnot(None), User.department != "")
        .distinct()
        .order_by(User.department.asc())
        .all()
    ]

    return render_template(
        "admin/students.html",
        create_form=create_form,
        student_accounts=student_accounts,
        student_total=student_total,
        show_all_students=show_all_students,
        evaluation_counts=evaluation_counts,
        course_options=COURSE_CHOICES,
        selected_status=status,
        selected_department=department,
        department_options=departments,
        search_query=search,
        total_students=User.query.filter_by(role="student").count(),
        active_students=User.query.filter_by(role="student", is_active=True).count(),
        inactive_students=User.query.filter_by(role="student", is_active=False).count(),
        nav_semester=f"{active.label} • {active.school_year}" if active else "No Active Semester",
    )


@admin_bp.route("/students/<int:student_id>/update", methods=["POST"])
@admin_required
def update_student(student_id):
    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    form = StudentAccountForm()

    if form.validate_on_submit() and _validate_student_uniques(form, student.id):
        student.username = sanitize_text(form.username.data)
        student.student_id = sanitize_text(form.student_id.data) or None
        student.full_name = sanitize_text(form.full_name.data)
        student.email = sanitize_text(form.email.data) or None
        student.department = form.department.data
        student.is_active = form.is_active.data
        db.session.commit()
        flash("Student account updated successfully.", "success")
    else:
        flash("Please review the student account details.", "danger")

    return redirect(url_for("admin.students"))


@admin_bp.route("/students/<int:student_id>/toggle", methods=["POST"])
@admin_required
def toggle_student(student_id):
    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    student.is_active = not student.is_active
    db.session.commit()
    flash("Student account status updated.", "success")
    return redirect(url_for("admin.students", **request.args))


@admin_bp.route("/students/<int:student_id>/reset-password", methods=["POST"])
@admin_required
def reset_student_password(student_id):
    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    form = StudentPasswordForm()

    if form.validate_on_submit():
        student.set_password(form.password.data)
        student.must_change_password = True
        db.session.commit()
        flash(f"Temporary password set for {student.full_name}. They must change it at next login.", "success")
    else:
        flash("Password reset failed. Passwords must match and be at least 10 characters.", "danger")

    return redirect(url_for("admin.students"))


@admin_bp.route("/sentiment")
@admin_required
def sentiment():
    faculty_id = request.args.get("faculty_id", type=int)
    semester_id = request.args.get("semester_id", type=int)

    faculty_options = Faculty.query.filter_by(is_active=True).order_by(Faculty.full_name.asc()).all()
    semester_options = Semester.query.order_by(Semester.id.desc()).all()
    selected_semester = get_selected_semester(semester_id)

    query = visible_evaluations(Evaluation.query)
    query = query.join(Faculty).filter(Faculty.is_active.is_(True))
    if faculty_id:
        query = query.filter(Evaluation.faculty_id == faculty_id)
    if selected_semester:
        query = query.filter(Evaluation.semester_id == selected_semester.id)

    evaluations = query.order_by(Evaluation.submitted_at.desc()).all()
    sentiment_values = sentiment_percentages(evaluations)
    classified_comments = [row for row in evaluations if row.comment and row.comment.strip()]

    return render_template(
        "admin/sentiment.html",
        faculty_options=faculty_options,
        semester_options=semester_options,
        selected_faculty_id=faculty_id,
        selected_semester_id=selected_semester.id if selected_semester else None,
        positive_pct=sentiment_values["positive"],
        neutral_pct=sentiment_values["neutral"],
        negative_pct=sentiment_values["negative"],
        classified_comments=classified_comments,
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
    comment_keywords = []
    wordcloud_path = None

    if selected_faculty and selected_semester:
        keyword_data = extract_keywords(selected_faculty.id, selected_semester.id)
        positive_keywords = keyword_data.get("positive", [])
        negative_keywords = keyword_data.get("negative", [])
        neutral_keywords = keyword_data.get("neutral", [])
        wordcloud_path = generate_wordcloud(selected_faculty.id, selected_semester.id)
        recent_evaluations = (
            visible_evaluations(Evaluation.query).filter_by(
                faculty_id=selected_faculty.id,
                semester_id=selected_semester.id,
            )
            .filter(Evaluation.comment.isnot(None))
            .order_by(Evaluation.submitted_at.desc())
            .limit(20)
            .all()
        )
        comment_keywords = [
            {
                "sentiment": evaluation.sentiment_label,
                "submitted_at": evaluation.submitted_at,
                "keywords": extract_comment_keywords(evaluation.comment),
            }
            for evaluation in recent_evaluations
        ]

    return render_template(
        "admin/keywords.html",
        faculty_options=faculty_options,
        semester_options=semester_options,
        selected_faculty=selected_faculty,
        selected_semester=selected_semester,
        positive_keywords=positive_keywords,
        negative_keywords=negative_keywords,
        neutral_keywords=neutral_keywords,
        comment_keywords=comment_keywords,
        wordcloud_path=wordcloud_path,
        nav_semester=f"{selected_semester.label} • {selected_semester.school_year}" if selected_semester else "No Active Semester",
    )


@admin_bp.route("/reports")
@admin_required
def reports():
    semester_id = request.args.get("semester_id", type=int)
    sort_by = request.args.get("sort_by", default="rating_desc", type=str)
    selected_department = request.args.get("department", default="all", type=str)

    selected_semester = get_selected_semester(semester_id)
    semester_options = Semester.query.order_by(Semester.id.desc()).all()

    faculty_rows = []

    for faculty in Faculty.query.filter_by(is_active=True).order_by(Faculty.full_name.asc()).all():
        query = visible_evaluations(Evaluation.query).filter_by(faculty_id=faculty.id)
        if selected_semester:
            query = query.filter_by(semester_id=selected_semester.id)
        evaluations = query.order_by(Evaluation.submitted_at.desc()).all()

        if not evaluations:
            continue

        sentiment = sentiment_percentages(evaluations)
        avg_rating = round(sum(float(e.overall_rating) for e in evaluations) / len(evaluations), 2)

        extract_keywords(faculty.id, selected_semester.id)
        keywords = build_keyword_summary(faculty.id, selected_semester.id, limit=10)

        # Recommendations derived from faculty evaluation aggregates.
        recs = generate_recommendations(
            positive_pct=sentiment["positive"],
            negative_pct=sentiment["negative"],
            neutral_pct=sentiment["neutral"],
            avg_instructional=round(sum(_avg_instructional(e) for e in evaluations) / len(evaluations), 2),
            avg_personal_social=round(sum(_avg_personal_social(e) for e in evaluations) / len(evaluations), 2),
            keywords=[
                {"keyword": k.keyword, "frequency": k.frequency, "sentiment_category": k.sentiment_category}
                for k in keywords
            ],
        )

        faculty_rows.append({
            "faculty_id": faculty.id,
            "faculty_name": faculty.full_name,
            "department": faculty.department,
            "average_rating": avg_rating,
            "evaluation_count": len(evaluations),
            "positive_pct": sentiment["positive"],
            "negative_pct": sentiment["negative"],
            "neutral_pct": sentiment["neutral"],
            "total_comments": len([e for e in evaluations if e.comment and e.comment.strip()]),
            "avg_instructional": round(sum(_avg_instructional(e) for e in evaluations) / len(evaluations), 2),
            "avg_personal_social": round(sum(_avg_personal_social(e) for e in evaluations) / len(evaluations), 2),

            "keywords": keywords,
            "sample_comments": [e for e in evaluations if e.comment and e.comment.strip()][:5],
            "negative_comments": [
                e for e in evaluations
                if e.sentiment_label == "negative" and e.comment and e.comment.strip()
            ],
            "recommendations": recs,
        })

    departments = sorted({row["department"] for row in faculty_rows if row["department"]})

    if selected_department != "all":
        faculty_rows = [row for row in faculty_rows if row["department"] == selected_department]

    if sort_by == "rating_asc":
        faculty_rows.sort(key=lambda x: x["average_rating"])
    elif sort_by == "name_asc":
        faculty_rows.sort(key=lambda x: x["faculty_name"].lower())
    elif sort_by == "name_desc":
        faculty_rows.sort(key=lambda x: x["faculty_name"].lower(), reverse=True)
    else:
        faculty_rows.sort(key=lambda x: x["average_rating"], reverse=True)

    return render_template(
        "admin/reports.html",
        semester_options=semester_options,
        selected_semester=selected_semester,
        faculty_rows=faculty_rows,
        department_options=departments,
        selected_department=selected_department,
        selected_sort_by=sort_by,
        nav_semester=f"{selected_semester.label} • {selected_semester.school_year}" if selected_semester else "No Active Semester",
    )


@admin_bp.route("/reports/faculty/<int:faculty_id>/download")
@admin_required
def download_faculty_report(faculty_id):
    Faculty.query.filter_by(id=faculty_id, is_active=True).first_or_404()
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
        full_name = sanitize_text(faculty_form.full_name.data)
        duplicate = Faculty.query.filter(
            func.lower(func.trim(Faculty.full_name)) == full_name.lower()
        ).first()
        if duplicate:
            flash("A faculty member with that name already exists.", "danger")
            return redirect(url_for("admin.faculty"))

        new_faculty = Faculty(
            full_name=full_name,
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

    search = sanitize_text(request.args.get("q"))
    department = sanitize_text(request.args.get("department")) or "all"
    status = request.args.get("status", "all")
    faculty_query = Faculty.query
    if search:
        like_value = f"%{search}%"
        faculty_query = faculty_query.filter(or_(
            Faculty.full_name.ilike(like_value),
            Faculty.department.ilike(like_value),
            Faculty.position.ilike(like_value),
        ))
    if department != "all":
        faculty_query = faculty_query.filter(Faculty.department == department)
    if status == "active":
        faculty_query = faculty_query.filter_by(is_active=True)
    elif status == "inactive":
        faculty_query = faculty_query.filter_by(is_active=False)

    faculty_query = faculty_query.order_by(Faculty.created_at.desc())
    faculty_total = faculty_query.count()
    show_all_faculty = request.args.get("show_all") == "1"
    faculty_members = faculty_query.all() if show_all_faculty else faculty_query.limit(15).all()
    department_options = [row[0] for row in db.session.query(Faculty.department)
        .filter(Faculty.department.isnot(None), Faculty.department != "")
        .distinct().order_by(Faculty.department.asc()).all()]
    semesters = Semester.query.order_by(Semester.id.desc()).all()
    active = Semester.query.filter_by(is_active=True).first()

    return render_template(
        "admin/faculty.html",
        faculty_form=faculty_form,
        semester_form=semester_form,
        faculty_members=faculty_members,
        faculty_total=faculty_total,
        show_all_faculty=show_all_faculty,
        search_query=search,
        selected_department=department,
        selected_status=status,
        department_options=department_options,
        semesters=semesters,
        nav_semester=f"{active.label} • {active.school_year}" if active else "No Active Semester",
    )


@admin_bp.route("/faculty/<int:faculty_id>/toggle", methods=["POST"])
@admin_required
def toggle_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    if not faculty.is_active:
        faculty.data_visible_after = now_ph_naive()
        faculty.is_active = True
    else:
        faculty.is_active = False
    db.session.commit()
    flash("Faculty status updated.", "success")
    return redirect(url_for("admin.faculty", **request.args))


@admin_bp.route("/semester/<int:semester_id>/toggle", methods=["POST"])
@admin_required
def toggle_semester(semester_id):
    semester = Semester.query.get_or_404(semester_id)
    if semester.is_active:
        semester.is_active = False
        flash("Semester deactivated successfully.", "success")
    else:
        Semester.query.update({"is_active": False})
        semester.is_active = True
        flash("Semester activated successfully.", "success")
    db.session.commit()
    return redirect(url_for("admin.faculty"))
