import json
import os
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Ensure output directory exists
output_dir = "evidence_docs"
os.makedirs(output_dir, exist_ok=True)

# Load the generated disputes
with open("synthetic_disputes.json", "r") as f:
    disputes_data = json.load(f)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "TitleStyle",
    parent=styles["Heading1"],
    fontSize=16,
    leading=20,
    textColor=colors.HexColor("#1e293b")
)
body_style = styles["BodyText"]

print(f"Generating PDF evidence documents for {len(disputes_data)} disputes...")

for item in disputes_data:
    dispute = item["payload"]["dispute"]["entity"]
    disp_id = dispute["id"]
    pay_id = dispute["payment_id"]
    amount_inr = dispute["amount"] / 100  # Convert paise to INR
    customer_name = dispute["metadata"]["customer_name"]
    description = dispute["metadata"]["description"]
    unit_no = f"Unit #{random.randint(101, 508)}"

    pdf_path = os.path.join(output_dir, f"{disp_id}_invoice.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    # Header
    story.append(Paragraph("<b>GANGA OSIAN SQUARE PROPERTY MANAGEMENT</b>", title_style))
    story.append(Paragraph("Commercial Space Leasing & Maintenance Division", body_style))
    story.append(Spacer(1, 12))

    # Invoice Details Table
    table_data = [
        ["Invoice Number:", f"INV-{disp_id[5:]}".upper(), "Date:", "2026-08-01"],
        ["Dispute Reference:", disp_id, "Payment ID:", pay_id],
        ["Tenant / Billed To:", customer_name, "Premises:", unit_no],
        ["Description:", description, "Status:", "COMPLETED / PAID"]
    ]

    t = Table(table_data, colWidths=[120, 150, 100, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#334155")),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # Line Items Table
    items_data = [
        ["Line Item Description", "Unit", "Tax Rate", "Total Amount (INR)"],
        [f"Monthly Maintenance & HVAC Allocation ({unit_no})", "1", "18% GST Included", f"INR {amount_inr:,.2f}"],
        ["Total Settled via Razorpay PG", "", "", f"INR {amount_inr:,.2f}"]
    ]

    items_table = Table(items_data, colWidths=[240, 60, 100, 120])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))

    # Evidence Verification Footer
    footer_text = (
        f"<b>Audit & Verification Log:</b> Digital signature verified. Payment transaction <code>{pay_id}</code> "
        f"was authorized successfully with 2-Factor Authentication. Property access logs confirm active occupancy for {unit_no}."
    )
    story.append(Paragraph(footer_text, body_style))

    doc.build(story)

print(f"Successfully generated 50 PDF evidence receipts in './{output_dir}/'")