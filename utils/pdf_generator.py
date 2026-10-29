from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.evaluation import Evaluation
from models.evaluation import visible_evaluations
from models.faculty import Faculty
from models.semester import Semester
from utils.keyword_extractor import build_keyword_summary
from utils.recommendations import generate_recommendations
from utils.timezone_utils import format_ph, now_ph_aware


def _avg_18(eval_obj):
    vals = [getattr(eval_obj, f"is_{i}") for i in range(1, 19)]
    return round(sum(vals) / len(vals), 2) if vals else 0


def _avg_9(eval_obj):
    vals = [getattr(eval_obj, f"ps_{i}") for i in range(1, 10)]
    return round(sum(vals) / len(vals), 2) if vals else 0


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


def _score_label(value):
    label_map = {
        1: "Poor",
        2: "Fair",
        3: "Satisfactory",
        4: "Very Satisfactory",
        5: "Outstanding",
    }
    return label_map.get(value, "N/A")


def _draw_page_header(canvas, doc):
    base_dir = Path(__file__).resolve().parent.parent
    header_path = base_dir / "header.jpg"
    if not header_path.exists():
        return

    page_width, page_height = doc.pagesize
    draw_width = page_width - doc.leftMargin - doc.rightMargin
    draw_height = draw_width * (141 / 815)
    canvas.drawImage(
        str(header_path),
        doc.leftMargin,
        page_height - 30 - draw_height,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )


def _table_paragraphs(rows, body_style, header_style=None):
    """Use wrapping Paragraphs in table cells so long labels stay inside columns."""
    return [
        [
            Paragraph(escape(str(value)), header_style if row_index == 0 and header_style else body_style)
            if isinstance(value, str)
            else value
            for value in row
        ]
        for row_index, row in enumerate(rows)
    ]


def _faculty_report_story(faculty_id, semester_id, styles):
    faculty = Faculty.query.get_or_404(faculty_id)
    semester = Semester.query.get_or_404(semester_id)

    evaluations = visible_evaluations(Evaluation.query).filter_by(faculty_id=faculty_id, semester_id=semester_id).all()
    keywords = build_keyword_summary(faculty_id, semester_id, limit=10)
    sentiment = sentiment_percentages(evaluations)

    avg_instructional = (
        round(sum(_avg_18(e) for e in evaluations) / len(evaluations), 2) if evaluations else 0
    )
    avg_personal_social = (
        round(sum(_avg_9(e) for e in evaluations) / len(evaluations), 2) if evaluations else 0
    )

    avg_overall = round(sum(float(e.overall_rating) for e in evaluations) / len(evaluations), 2) if evaluations else 0
    total_students_evaluated = len(evaluations)

    # Keep the hierarchy readable while reserving a little more room for long values.
    styles["Heading1"].fontSize = 15
    styles["Heading1"].leading = 18
    styles["Heading1"].spaceAfter = 6
    styles["Heading2"].fontSize = 11
    styles["Heading2"].leading = 13
    styles["Heading2"].spaceBefore = 8
    styles["Heading2"].spaceAfter = 4
    styles["Normal"].fontSize = 9
    styles["Normal"].leading = 12
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12

    table_body = styles["BodyText"].clone("ReportTableBody")
    table_body.fontSize = 7.5
    table_body.leading = 9
    table_header = table_body.clone("ReportTableHeader")
    table_header.textColor = colors.white
    table_header.fontName = "Helvetica-Bold"

    story = []
    story.append(Paragraph("<b>Faculty Evaluation Report</b>", styles["Heading1"]))
    story.append(Paragraph(f"<b>Semester:</b> {escape(str(semester.label))} • {escape(str(semester.school_year))}", styles["Normal"]))
    story.append(Paragraph(f"<b>Generated Date:</b> {format_ph(now_ph_aware())}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Faculty Name:</b> {escape(str(faculty.full_name))}", styles["Normal"]))
    story.append(Paragraph(f"<b>Department:</b> {escape(str(faculty.department))}", styles["Normal"]))
    story.append(Spacer(1, 12))

    rating_data = [
        ["Criterion", "Average"],
        ["Instructional Skills (A)", avg_instructional],
        ["Personal and Social Qualities (B)", avg_personal_social],
        ["Overall Rating", avg_overall],
        ["Total Students Evaluated", total_students_evaluated],
    ]

    rating_table = Table(_table_paragraphs(rating_data, table_body, table_header), colWidths=[300, 150])
    rating_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2044")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(rating_table)
    story.append(Spacer(1, 12))

    sentiment_data = [
        ["Sentiment", "Percentage"],
        ["Positive", f"{sentiment['positive']}%"],
        ["Negative", f"{sentiment['negative']}%"],
        ["Neutral", f"{sentiment['neutral']}%"],
    ]
    sentiment_table = Table(_table_paragraphs(sentiment_data, table_body, table_header), colWidths=[300, 150])
    sentiment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D9488")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(sentiment_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Per-Question Score Distribution (for this instructor only)</b>", styles["Heading2"]))

    question_rows = [["Question", "Poor", "Fair", "Satisfactory", "Very Satisfactory", "Outstanding"]]
    for i in range(1, 19):
        field_name = f"is_{i}"
        counts = {j: 0 for j in range(1, 6)}
        for e in evaluations:
            value = getattr(e, field_name, None)
            if value in counts:
                counts[value] += 1
        question_rows.append(
            [f"A{i}", counts[1], counts[2], counts[3], counts[4], counts[5]]
        )

    for i in range(1, 10):
        field_name = f"ps_{i}"
        counts = {j: 0 for j in range(1, 6)}
        for e in evaluations:
            value = getattr(e, field_name, None)
            if value in counts:
                counts[value] += 1
        question_rows.append(
            [f"B{i}", counts[1], counts[2], counts[3], counts[4], counts[5]]
        )

    distribution_table = Table(
        _table_paragraphs(question_rows, table_body, table_header),
        colWidths=[70, 52, 52, 82, 113, 100],
        repeatRows=1,
    )
    distribution_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(distribution_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Top 10 Most Repeated Keywords</b>", styles["Heading2"]))
    if keywords:
        keyword_data = [["Keyword", "Frequency", "Sentiment"]]
        for keyword in keywords:
            keyword_data.append([keyword.keyword, keyword.frequency, keyword.sentiment_category.title()])
        keyword_table = Table(_table_paragraphs(keyword_data, table_body, table_header), colWidths=[220, 90, 140])
        keyword_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A3461")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(keyword_table)
    else:
        story.append(Paragraph("No keyword entries found.", styles["Normal"]))

    story.append(Spacer(1, 12))

    recs = generate_recommendations(
        positive_pct=sentiment["positive"],
        negative_pct=sentiment["negative"],
        neutral_pct=sentiment["neutral"],
        avg_instructional=avg_instructional,
        avg_personal_social=avg_personal_social,
        keywords=[
            {"keyword": k.keyword, "frequency": k.frequency, "sentiment_category": k.sentiment_category}
            for k in keywords
        ],
    )

    story.append(Paragraph("<b>Recommendations</b>", styles["Heading2"]))
    for section_title, items in [
        ("Strengths", recs.get("strengths", [])),
        ("Improvements", recs.get("improvements", [])),
        ("Actions", recs.get("actions", [])),
        ("Focus Areas", recs.get("focus_areas", [])),
    ]:
        story.append(Paragraph(f"<b>{section_title}:</b>", styles["BodyText"]))
        if items:
            for entry in items:
                story.append(Paragraph(f"• {escape(str(entry))}", styles["BodyText"]))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("• N/A", styles["BodyText"]))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 6))

    negative_comments = [e for e in evaluations if e.sentiment_label == "negative" and e.comment and e.comment.strip()]
    other_comments = [e for e in evaluations if e.sentiment_label != "negative" and e.comment and e.comment.strip()]
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Negative Comments ({len(negative_comments)})</b>", styles["Heading2"]))
    if negative_comments:
        for item in negative_comments:
            story.append(
                Paragraph(
                    f"• {escape(str(item.comment))}",
                    styles["BodyText"],
                )
            )
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No negative comments available.", styles["Normal"]))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Other Instructor Comments</b>", styles["Heading2"]))
    if other_comments:
        for item in other_comments:
            story.append(
                Paragraph(
                    f"• <b>{escape(str(item.sentiment_label).title())}</b> - {escape(str(item.comment))}",
                    styles["BodyText"],
                )
            )
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No other comments available.", styles["Normal"]))


    story.append(Spacer(1, 24))
    story.append(Paragraph("______________________________", styles["Normal"]))
    story.append(Paragraph("Department Head", styles["Normal"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph("______________________________", styles["Normal"]))
    story.append(Paragraph("Date", styles["Normal"]))

    return story


def build_faculty_report_pdf(faculty_id, semester_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=110, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = _faculty_report_story(faculty_id, semester_id, styles)
    doc.build(story, onFirstPage=_draw_page_header, onLaterPages=_draw_page_header)
    buffer.seek(0)
    return buffer, f"faculty_report_{faculty_id}_{semester_id}.pdf"


def build_all_reports_pdf(semester_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=110, bottomMargin=30)
    styles = getSampleStyleSheet()

    story = []
    faculties = Faculty.query.filter_by(is_active=True).order_by(Faculty.full_name.asc()).all()
    added = 0

    for faculty in faculties:
        evaluations = visible_evaluations(Evaluation.query).filter_by(faculty_id=faculty.id, semester_id=semester_id).all()
        if not evaluations:
            continue
        if added > 0:
            story.append(PageBreak())
        story.extend(_faculty_report_story(faculty.id, semester_id, styles))
        added += 1

    doc.build(story, onFirstPage=_draw_page_header, onLaterPages=_draw_page_header)
    buffer.seek(0)
    return buffer, f"all_faculty_reports_semester_{semester_id}.pdf"

