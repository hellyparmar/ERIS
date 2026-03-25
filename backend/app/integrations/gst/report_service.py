import logging
import os
from typing import Dict, Any, List
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

logger = logging.getLogger(__name__)

class GSTReportService:
    def __init__(self, output_dir: str = "/tmp/gst_reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_gstr1_pdf(self, month: int, year: int, data: List[Dict[str, Any]]) -> bytes:
        """Generate GSTR-1 PDF report summary"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"GSTR-1 Summary Report - {month}/{year}")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"Generated on: {date.today()}")
        
        y = height - 120
        c.drawString(50, y, "Section")
        c.drawString(150, y, "Total Invoices")
        c.drawString(300, y, "Taxable Value")
        c.drawString(450, y, "Total GST")
        
        c.line(50, y-5, 550, y-5)
        
        # Mock data processing
        y -= 25
        for item in data:
            if y < 50:
                c.showPage()
                y = height - 50
            c.drawString(50, y, str(item.get('section', 'B2B')))
            c.drawString(150, y, str(item.get('count', 0)))
            c.drawString(300, y, f"Rs. {item.get('taxable', 0):,.2f}")
            c.drawString(450, y, f"Rs. {item.get('gst', 0):,.2f}")
            y -= 20

        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_gst_invoice_pdf(self, sale_data: Dict[str, Any]) -> bytes:
        """Generate GST-compliant invoice PDF"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Simple Header
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width/2, height - 50, "TAX INVOICE")
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, "Seller: R-DIOS Retail Intelligence System")
        p.drawString(50, height - 95, "GSTIN: 24AAAAAAAAA1Z1")
        
        p.drawString(width - 200, height - 80, f"Invoice No: {sale_data.get('id', 'INV/2026/03/001')}")
        p.drawString(width - 200, height - 95, f"Date: {sale_data.get('date', date.today())}")
        
        # Customer Info
        p.drawString(50, height - 130, f"Bill To: {sale_data.get('customer_name', 'Walk-in Customer')}")
        
        # Table Header
        y = height - 180
        p.line(50, y+15, width-50, y+15)
        p.drawString(55, y, "Description")
        p.drawString(300, y, "Qty")
        p.drawString(350, y, "Rate")
        p.drawString(450, y, "Total")
        p.line(50, y-5, width-50, y-5)
        
        # Items
        y -= 20
        total = 0
        for item in sale_data.get('items', []):
            p.drawString(55, y, str(item.get('name', 'Product')))
            p.drawString(300, y, str(item.get('qty', 1)))
            p.drawString(350, y, str(item.get('rate', 0)))
            line_total = item.get('qty', 1) * item.get('rate', 0)
            p.drawString(450, y, str(line_total))
            total += line_total
            y -= 15
            
        p.line(50, y, width-50, y)
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(350, y, "Grand Total:")
        p.drawString(450, y, f"Rs. {total:,.2f}")
        
        p.setFont("Helvetica", 8)
        p.drawString(50, 50, "This is a computer generated invoice and does not require signature.")

        p.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

# Singleton Instance
gst_report_service = GSTReportService()
