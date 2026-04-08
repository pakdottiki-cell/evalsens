from collections import Counter
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models.evaluation import Evaluation, Keyword
from models.faculty import Faculty
from models.semester import Semester
from models.user import User
from utils.keyword_extractor import extract_keywords

api_bp = Blueprint("api", __name__, url_prefix="/api")


def admin_api_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        return view_func(*args, **kwargs)
    return wrapper


def selected_semester(semester_id):
    if semester_id:
        return Semester.query.get(semester_id)
    return Semester.query.filter_by(is_active=True).first() or Semester.query.order_by(Semester.id.desc()).first()


def calc_percentages(evaluations):
    total = len(evaluations)
    if total == 0:
        return {"positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}

    counts = Counter([e.sentiment_label for e in evaluations])
    return {
        "positive_pct": round((counts.get("positive", 0) / total) * 100, 2),
        "negative_pct": round((counts.get("negative", 0) / total) * 100, 2),
        "neutral_pct": round((counts.get("neutral", 0) / total) * 100, 2),
    }


def build_trend(faculty_id=None):
    semesters = Semester.query.order_by(Semester.id.desc()).limit(4).all()
    semesters.reverse()

    trend = []
    for semester in semesters:
        query = Evaluation.query.filter_by(semester_id=semester.id)
        if faculty_id:
            query = query.filter_by(faculty_id=faculty_id)
        rows = query.all()
        pct = calc_percentages(rows)
        trend.append({
            "semester_id": semester.id,
            "label": f"{semester.label} {semester.school_year}",
            "positive_pct": pct["positive_pct"],
            "negative_pct": pct["negative_pct"],
            "neutral_pct": pct["neutral_pct"],
            "total": len(rows),
        })
    return trend


@api_bp.route("/dashboard-stats")
@admin_api_required
def dashboard_stats():
    semester_id = request.args.get("semester_id", type=int)
    semester = selected_semester(semester_id)

    query = Evaluation.query
    if semester:
        query = query.filter_by(semester_id=semester.id)

    evaluations = query.all()
    pct = calc_percentages(evaluations)

    total_students = User.query.filter_by(role="student", is_active=True).count()
    total_faculty = Faculty.query.filter_by(is_active=True).count()
    pending_count = max((total_students * total_faculty) - len(evaluations), 0)

    return jsonify({
        "total_evaluations": len(evaluations),
        "faculty_evaluated": len({e.faculty_id for e in evaluations}),
        "positive_pct": pct["positive_pct"],
        "negative_pct": pct["negative_pct"],
        "neutral_pct": pct["neutral_pct"],
        "pending_count": pending_count,
    })


@api_bp.route("/sentiment-summary")
@admin_api_required
def sentiment_summary():
    faculty_id = request.args.get("faculty_id", type=int)
    semester_id = request.args.get("semester_id", type=int)

    query = Evaluation.query
    if faculty_id:
        query = query.filter_by(faculty_id=faculty_id)
    if semester_id:
        query = query.filter_by(semester_id=semester_id)

    evaluations = query.order_by(Evaluation.submitted_at.desc()).all()
    pct = calc_percentages(evaluations)

    sample_comments = []
    for item in evaluations[:10]:
        sample_comments.append({
            "comment": item.comment,
            "sentiment": item.sentiment_label,
            "confidence_score": float(item.confidence_score),
            "submitted_at": item.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return jsonify({
        "positive_pct": pct["positive_pct"],
        "negative_pct": pct["negative_pct"],
        "neutral_pct": pct["neutral_pct"],
        "sample_comments": sample_comments,
        "trend_data": build_trend(faculty_id=faculty_id),
    })


@api_bp.route("/faculty-performance")
@admin_api_required
def faculty_performance():
    semester_id = request.args.get("semester_id", type=int)
    semester = selected_semester(semester_id)

    results = []
    for faculty in Faculty.query.order_by(Faculty.full_name.asc()).all():
        query = Evaluation.query.filter_by(faculty_id=faculty.id)
        if semester:
            query = query.filter_by(semester_id=semester.id)
        evaluations = query.all()
        pct = calc_percentages(evaluations)

        results.append({
            "faculty_id": faculty.id,
            "faculty_name": faculty.full_name,
            "department": faculty.department,
            "average_rating": round(sum(float(e.overall_rating) for e in evaluations) / len(evaluations), 2) if evaluations else 0,
            "positive_pct": pct["positive_pct"],
            "negative_pct": pct["negative_pct"],
            "neutral_pct": pct["neutral_pct"],
            "total_comments": len([e for e in evaluations if e.comment]),
        })

    return jsonify(results)


@api_bp.route("/keywords")
@admin_api_required
def keywords():
    faculty_id = request.args.get("faculty_id", type=int)
    semester_id = request.args.get("semester_id", type=int)

    if not faculty_id or not semester_id:
        return jsonify({"error": "faculty_id and semester_id are required"}), 400

    if not Keyword.query.filter_by(faculty_id=faculty_id, semester_id=semester_id).first():
        extract_keywords(faculty_id, semester_id)

    rows = Keyword.query.filter_by(faculty_id=faculty_id, semester_id=semester_id).all()
    data = {"positive_keywords": [], "negative_keywords": [], "neutral_keywords": []}

    for row in rows:
        bucket = f"{row.sentiment_category}_keywords"
        data[bucket].append({"keyword": row.keyword, "frequency": row.frequency})

    data["positive_keywords"] = sorted(data["positive_keywords"], key=lambda x: x["frequency"], reverse=True)[:10]
    data["negative_keywords"] = sorted(data["negative_keywords"], key=lambda x: x["frequency"], reverse=True)[:10]
    data["neutral_keywords"] = sorted(data["neutral_keywords"], key=lambda x: x["frequency"], reverse=True)[:10]

    return jsonify(data)


@api_bp.route("/refresh-keywords", methods=["POST"])
@admin_api_required
def refresh_keywords():
    payload = request.get_json(silent=True) or {}
    faculty_id = payload.get("faculty_id")
    semester_id = payload.get("semester_id")

    if not faculty_id or not semester_id:
        return jsonify({"error": "faculty_id and semester_id are required"}), 400

    result = extract_keywords(int(faculty_id), int(semester_id))
    return jsonify({
        "message": "Keywords refreshed successfully.",
        "results": result
    })


@api_bp.route("/trend")
@admin_api_required
def trend():
    faculty_id = request.args.get("faculty_id", type=int)
    return jsonify(build_trend(faculty_id=faculty_id))