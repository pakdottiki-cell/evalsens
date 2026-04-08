from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models.evaluation import Evaluation
from models.faculty import Faculty
from models.semester import Semester
from utils.keyword_extractor import build_keyword_summary


def sentiment_percentages(evaluations):
    total = len(evaluations)
    if total == 0:
        return {"positive": 0, "negative": 0, "neutral": 0}
    positive = len([e for e in evaluations if e.sentiment_label == "positive"])
    negative = len([e for e in evaluations if e.sentiment_label == "negative"])
    neutral = len([e for e in evaluations if e.sentiment_label == "neutral"])
    return {
        "positive": round((positive / total) * 100, 2),
        "negative": round((negative / total) * 100, 2),
        "neutral": round((neutral / total) * 100, 2),
    }


def _header_story(styles):
    story = []
    base_dir = Path(__file__).resolve().parent.parent
    logo_path = base_dir / "static" / "img" / "logo.png"
    if logo_path.exists():
        story.append(Image(str(logo_path), width=48, height=48))
    story.append(Paragraph("<b>Buenavista Community College</b>", styles["Title"]))
    story.append(Paragraph("Buenavista, Bohol, Philippines", styles["Normal"]))
    story.append(Spacer(1, 8))
    return story


def _faculty_report_story(faculty_id, semester_id, styles):
    faculty = Faculty.query.get_or_404(faculty_id)
    semester = Semester.query.get_or_404(semester_id)
    evaluations = Evaluation.query.filter_by(faculty_id=faculty_id, semester_id=semester_id).all()
    keywords = build_keyword_summary(faculty_id, semester_id, limit=10)
    sentiment = sentiment_percentages(evaluations)

    avg_effectiveness = round(sum(e.rating_effectiveness for e in evaluations) / len(evaluations), 2) if evaluations else 0
    avg_mastery = round(sum(e.rating_mastery for e in evaluations) / len(evaluations), 2) if evaluations else 0
    avg_communication = round(sum(e.rating_communication for e in evaluations) / len(evaluations), 2) if evaluations else 0
    avg_punctuality = round(sum(e.rating_punctuality for e in evaluations) / len(evaluations), 2) if evaluations else 0
    avg_overall = round(sum(float(e.overall_rating) for e in evaluations) / len(evaluations), 2) if evaluations else 0

    story = []
    story.extend(_header_story(styles))
    story.append(Paragraph("<b>Faculty Evaluation Report</b>", styles["Heading1"]))
    story.append(Paragraph(f"<b>Semester:</b> {semester.label} • {semester.school_year}", styles["Normal"]))
    story.append(Paragraph(f"<b>Generated Date:</b> {datetime.now().strftime('%B %d, %Y %I:%M %p')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Faculty Name:</b> {faculty.full_name}", styles["Normal"]))
    story.append(Paragraph(f"<b>Department:</b> {faculty.department}", styles["Normal"]))
    story.append(Spacer(1, 12))

    rating_data = [
        ["Criterion", "Average"],
        ["Teaching Effectiveness", avg_effectiveness],
        ["Subject Mastery", avg_mastery],
        ["Communication Skills", avg_communication],
        ["Punctuality and Attendance", avg_punctuality],
        ["Overall Rating", avg_overall],
    ]
    rating_table = Table(rating_data, colWidths=[300, 150])
    rating_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2044")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(rating_table)
    story.append(Spacer(1, 12))

    sentiment_data = [
        ["Sentiment", "Percentage"],
        ["Positive", f"{sentiment['positive']}%"],
        ["Negative", f"{sentiment['negative']}%"],
        ["Neutral", f"{sentiment['neutral']}%"],
    ]
    sentiment_table = Table(sentiment_data, colWidths=[300, 150])
    sentiment_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D9488")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(sentiment_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Top 10 Most Repeated Keywords</b>", styles["Heading2"]))
    if keywords:
        keyword_data = [["Keyword", "Frequency", "Sentiment"]]
        for keyword in keywords:
            keyword_data.append([keyword.keyword, keyword.frequency, keyword.sentiment_category.title()])
        keyword_table = Table(keyword_data, colWidths=[220, 90, 140])
        keyword_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A3461")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(keyword_table)
    else:
        story.append(Paragraph("No keyword entries found.", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Sample Classified Comments</b>", styles["Heading2"]))
    samples = evaluations[:5]
    if samples:
        for item in samples:
            story.append(
                Paragraph(
                    f"• <b>{item.sentiment_label.title()}</b> "
                    f"(Confidence: {item.confidence_score}) - {item.comment}",
                    styles["BodyText"]
                )
            )
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No comments available.", styles["Normal"]))

    story.append(Spacer(1, 24))
    story.append(Paragraph("______________________________", styles["Normal"]))
    story.append(Paragraph("Department Head", styles["Normal"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("______________________________", styles["Normal"]))
    story.append(Paragraph("Date", styles["Normal"]))

    return story


def build_faculty_report_pdf(faculty_id, semester_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = _faculty_report_story(faculty_id, semester_id, styles)
    doc.build(story)
    buffer.seek(0)
    return buffer, f"faculty_report_{faculty_id}_{semester_id}.pdf"


def build_all_reports_pdf(semester_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()

    story = []
    faculties = Faculty.query.order_by(Faculty.full_name.asc()).all()
    added = 0

    for faculty in faculties:
        evaluations = Evaluation.query.filter_by(faculty_id=faculty.id, semester_id=semester_id).all()
        if not evaluations:
            continue
        if added > 0:
            story.append(PageBreak())
        story.extend(_faculty_report_story(faculty.id, semester_id, styles))
        added += 1

    doc.build(story)
    buffer.seek(0)
    return buffer, f"all_faculty_reports_semester_{semester_id}.pdf"