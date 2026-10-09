from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas


def generate_certificate(
    output_path: Path,
    recipient_name: str,
    event_name: str,
    issue_date: date,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_width, page_height = landscape(letter)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    pdf.setStrokeColor(colors.HexColor("#19324A"))
    pdf.setLineWidth(3)
    pdf.rect(28, 28, page_width - 56, page_height - 56)
    pdf.setStrokeColor(colors.HexColor("#C89B3C"))
    pdf.setLineWidth(1)
    pdf.rect(38, 38, page_width - 76, page_height - 76)

    pdf.setFillColor(colors.HexColor("#19324A"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(page_width / 2, page_height - 150, "CERTIFICATE OF ACHIEVEMENT")

    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(page_width / 2, page_height - 205, "This certificate is proudly presented to")
    pdf.setFillColor(colors.HexColor("#19324A"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(page_width / 2, page_height - 260, recipient_name)

    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(page_width / 2, page_height - 315, "in recognition of successful participation in")
    pdf.setFillColor(colors.HexColor("#19324A"))
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(page_width / 2, page_height - 350, event_name)
    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(page_width / 2, 105, f"Issued on {issue_date.isoformat()}")

    pdf.showPage()
    pdf.save()
