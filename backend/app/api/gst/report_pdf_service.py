"""
GST PDF Report Service
Generates GSTR-1 and GSTR-3B Summary PDFs using ReportLab.
"""

from __future__ import annotations
import io
import os
from datetime import datetime
from typing import Dict, Any
from app.api.gst.gstr1_generator import GSTR1Generator
from app.api.gst.gstr3b_generator import GSTR3BGenerator

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    _RL_AVAILABLE = True
except ImportError:
    _RL_AVAILABLE = False

class GSTReportPDFService:
    """PDF generation for official GST Reports (Summary form)."""

    def __init__(self):
        if not _RL_AVAILABLE:
            raise ImportError("reportlab not found")
        self.styles = getSampleStyleSheet()

    def generate_gstr1_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """Render GSTR-1 JSON data into a readable PDF summary."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        elements.append(Paragraph(f"GSTR-1 Summary Report", self.styles["Title"]))
        elements.append(Paragraph(f"GSTIN: {report_data.get('gstin')} | Period: {report_data.get('fp')}", self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # B2B Summary Table
        elements.append(Paragraph("<b>1. B2B Supplies</b>", self.styles["Heading2"]))
        b2b_data = [["Counterparty GSTIN", "Invoice Count", "Total Taxable Value", "Total Tax Status"]]
        for entry in report_data.get("b2b", []):
            taxable = sum(inv.get("val", 0) for inv in entry.get("inv", [])) # Simplified
            b2b_data.append([str(entry["ctin"]), str(len(entry["inv"])), f"₹{taxable:,.2f}", "Included"])
        
        t = Table(b2b_data, colWidths=[5*cm, 3*cm, 5*cm, 4*cm])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t)
        
        doc.build(elements)
        return buffer.getvalue()

    def generate_gstr3b_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """Render GSTR-3B JSON data into a readable PDF summary."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        elements.append(Paragraph(f"GSTR-3B Summary Return", self.styles["Title"]))
        elements.append(Paragraph(f"Legal Name: {report_data.get('legal_name')}", self.styles["Normal"]))
        elements.append(Paragraph(f"GSTIN: {report_data.get('gstin')} | Period: {report_data.get('ret_period')}", self.styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Section 3.1
        elements.append(Paragraph("<b>3.1 Details of Outward Supplies</b>", self.styles["Heading2"]))
        sup = report_data.get("sup_details", {}).get("osup_det", {})
        sup_data = [
            ["Nature of Supplies", "Total Taxable Value", "Integrated Tax", "Central Tax", "State Tax"],
            ["(a) Outward Taxable Supplies", f"₹{sup.get('txval',0):,.2f}", f"₹{sup.get('iamt',0):,.2f}", f"₹{sup.get('camt',0):,.2f}", f"₹{sup.get('samt',0):,.2f}"]
        ]
        t = Table(sup_data, colWidths=[5*cm, 3.5*cm, 3*cm, 3*cm, 3*cm])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        elements.append(t)

        doc.build(elements)
        return buffer.getvalue()

gst_report_pdf_service = GSTReportPDFService()
