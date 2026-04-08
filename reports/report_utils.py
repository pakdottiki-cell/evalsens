from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_faculty_report_pdf(path, faculty_name, content_lines):
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, height-60, f'Faculty Report - {faculty_name}')
    c.setFont('Helvetica', 10)
    y = height - 90
    for line in content_lines:
        c.drawString(40, y, line)
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()
