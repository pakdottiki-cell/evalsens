import re
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
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
from utils.sentiment_utils import normalize_prediction_to_label, normalize_prediction_to_confidence


student_bp = Blueprint("student", __name__, url_prefix="/student")


def sanitize_text(value):
    value = (value or "").strip()
    value = re.sub(r"<.*?>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value


class EvaluationForm(FlaskForm):
    rating_choices = [

        (1, "Poor"),
        (2, "Fair"),
        (3, "Satisfactory"),
        (4, "Very satisfactory"),
        (5, "Outstanding"),
    ]

    # A. Instructional Skills
    is_1 = RadioField("1. Explains course objectives, requirements and grading system at the start of the semester", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_2 = RadioField("2. Provides course outline/study guide", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_3 = RadioField("3. Is prepared and organized for classes", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_4 = RadioField("4. Exhibits mastery of subject matter", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_5 = RadioField("5. Explains the lesson clearly", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_6 = RadioField("6. Speaks clearly and fluently", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_7 = RadioField("7. Uses effective teaching strategies", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_8 = RadioField("8. Uses appropriate instructional aids effectively", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_9 = RadioField("9. Provides opportunities for students participation", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_10 = RadioField("10. Discuss up-to-date information related to subject matter", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_11 = RadioField("11. Makes classroom activities interesting", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_12 = RadioField("12. Guides students to accomplish learning goals", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_13 = RadioField("13. Encourages class participation and critical thinking", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_14 = RadioField("14. Welcomes questions", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_15 = RadioField("15. Gives and check relevant assignment and projects", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_16 = RadioField("16. Starts and ends classes on time", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_17 = RadioField("17. Maintains classroom discipline", choices=rating_choices, coerce=int, validators=[DataRequired()])
    is_18 = RadioField("18. Makes use of the whole period for class activities", choices=rating_choices, coerce=int, validators=[DataRequired()])

    # B. Personal and Social Qualities
    ps_1 = RadioField("1. Respect the students dignity and worth", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_2 = RadioField("2. Manifest love and concern with students", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_3 = RadioField("3. Promotes smooth and students-teacher relationship", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_4 = RadioField("4. Is open-minded and approachable", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_5 = RadioField("5. Commands respect of the students", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_6 = RadioField("6. Possesses a healthy sense of humor and cheerfulness", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_7 = RadioField("7. Dresses appropriately", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_8 = RadioField("8. Has well-modulated voice", choices=rating_choices, coerce=int, validators=[DataRequired()])
    ps_9 = RadioField("9. Is available for students consultations and assistance", choices=rating_choices, coerce=int, validators=[DataRequired()])


    subject = TextAreaField("Subject (free-text)", validators=[DataRequired(), Length(min=2, max=200)])
    comment = TextAreaField("Comment", validators=[DataRequired(), Length(min=10, max=2000)])

    submit = SubmitField("Submit Evaluation")



def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "student":
            logout_user()
            flash("Unauthorized access. Please sign in again.", "danger")
            return redirect(url_for("auth.student_login"))
        return view_func(*args, **kwargs)
    return wrapper


def active_semester():
    return Semester.query.filter_by(is_active=True).first()


@student_bp.route("/dashboard")
@student_required
def dashboard():
    semester = active_semester()

    q = (request.args.get("q") or "").strip()
    selected_department = (request.args.get("department") or "").strip()

    faculty_query = Faculty.query.filter_by(is_active=True)

    if q:
        faculty_query = faculty_query.filter(Faculty.full_name.ilike(f"%{q}%"))

    if selected_department:
        faculty_query = faculty_query.filter(Faculty.department == selected_department)

    faculty_members = faculty_query.order_by(Faculty.department.asc(), Faculty.full_name.asc()).all()

    departments = [
        row[0]
        for row in db.session.query(Faculty.department)
        .filter(Faculty.is_active.is_(True), Faculty.department.isnot(None), Faculty.department != "")
        .distinct()
        .order_by(Faculty.department.asc())
        .all()
    ]

    history = []

    if semester:
        history = (
            Evaluation.query.filter_by(student_id=current_user.id, semester_id=semester.id)
            .order_by(Evaluation.submitted_at.desc())
            .all()
        )

    # Keep submitted_ids for backward compatibility with the template,
    # but do not use it to block evaluations anymore.
    submitted_ids = {item.faculty_id for item in history}

    return render_template(
        "student/dashboard.html",
        active_semester=semester,
        faculty_members=faculty_members,
        submitted_ids=submitted_ids,
        history=history,
        departments=departments,
        q=q,
        selected_department=selected_department,
        nav_semester=f"{semester.label} • {semester.school_year}" if semester else "No Active Semester",
    )


@student_bp.route("/evaluate", methods=["GET"])
@student_required
def evaluate_select():
    return redirect(url_for("student.dashboard", focus="faculty"))

@student_bp.route("/evaluate/<int:faculty_id>", methods=["GET", "POST"])
@student_required
def evaluate(faculty_id):
    semester = active_semester()
    if not semester:
        flash("There is no active semester available for evaluation.", "warning")
        return redirect(url_for("student.dashboard"))

    faculty = Faculty.query.filter_by(id=faculty_id, is_active=True).first_or_404()

    form = EvaluationForm()


    if form.validate_on_submit():
        # Allow a student to evaluate the same instructor multiple times per active semester
        existing_count = Evaluation.query.filter_by(
            student_id=current_user.id,
            faculty_id=faculty.id,
            semester_id=semester.id,
        ).count()
        if existing_count >= 3:
            flash("You have already submitted the maximum number of evaluations (3) for this faculty member this semester.", "warning")
            return redirect(url_for("student.dashboard"))

        comment = sanitize_text(form.comment.data)

        ratings = [
            form.is_1.data, form.is_2.data, form.is_3.data, form.is_4.data, form.is_5.data,
            form.is_6.data, form.is_7.data, form.is_8.data, form.is_9.data, form.is_10.data,
            form.is_11.data, form.is_12.data, form.is_13.data, form.is_14.data, form.is_15.data,
            form.is_16.data, form.is_17.data, form.is_18.data,
            form.ps_1.data, form.ps_2.data, form.ps_3.data, form.ps_4.data, form.ps_5.data,
            form.ps_6.data, form.ps_7.data, form.ps_8.data, form.ps_9.data,
        ]

        overall = Decimal(sum(ratings) / 27).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        evaluation = Evaluation(
            student_id=current_user.id,
            faculty_id=faculty.id,
            semester_id=semester.id,
            subject=sanitize_text(form.subject.data),

            is_1=form.is_1.data,
            is_2=form.is_2.data,
            is_3=form.is_3.data,
            is_4=form.is_4.data,
            is_5=form.is_5.data,
            is_6=form.is_6.data,
            is_7=form.is_7.data,
            is_8=form.is_8.data,
            is_9=form.is_9.data,
            is_10=form.is_10.data,
            is_11=form.is_11.data,
            is_12=form.is_12.data,
            is_13=form.is_13.data,
            is_14=form.is_14.data,
            is_15=form.is_15.data,
            is_16=form.is_16.data,
            is_17=form.is_17.data,
            is_18=form.is_18.data,
            ps_1=form.ps_1.data,
            ps_2=form.ps_2.data,
            ps_3=form.ps_3.data,
            ps_4=form.ps_4.data,
            ps_5=form.ps_5.data,
            ps_6=form.ps_6.data,
            ps_7=form.ps_7.data,
            ps_8=form.ps_8.data,
            ps_9=form.ps_9.data,
            overall_rating=overall,
            comment=comment,
            sentiment_label="neutral",
            is_anonymous=True,
        )

        db.session.add(evaluation)
        db.session.commit()

        prediction = predict_sentiment(comment)

        # prediction should be a dict from ml.predict.predict_sentiment():
        # { label: positive|negative|neutral, confidence: float, probabilities: {...}}
        # If something unexpected comes back, normalize_prediction_to_label() will handle it,
        # but we also guard against common cases where label/probabilities keys are missing.
        evaluation.sentiment_label = normalize_prediction_to_label(prediction)

        # If your model/confidence isn't used elsewhere, this is still safe to keep.
        # (The Evaluation model defines confidence_score as well.)
        evaluation.confidence_score = normalize_prediction_to_confidence(prediction)

        # Strong safety: if normalization returned neutral but the model provided probabilities,
        # pick the top non-neutral class (prevents systematic neutral fallback for negatives).
        if (
            evaluation.sentiment_label == "neutral"
            and isinstance(prediction, dict)
            and isinstance(prediction.get("probabilities"), dict)
        ):
            probs = prediction["probabilities"]
            pos = float(probs.get("positive", 0) or 0)
            neg = float(probs.get("negative", 0) or 0)
            neu = float(probs.get("neutral", 0) or 0)
            # If negative is at least as likely as neutral, treat as negative.
            if neg >= neu and neg > pos:
                evaluation.sentiment_label = "negative"
            # If positive is at least as likely as neutral, treat as positive.
            elif pos >= neu and pos > neg:
                evaluation.sentiment_label = "positive"


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