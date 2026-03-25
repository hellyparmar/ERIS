"""
PDF Invoice Generator
Generates professional invoices with GST breakdown
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class InvoicePDFGenerator:
    """Generate PDF invoices with GST details"""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    def generate_invoice_pdf(
        self,
        invoice_data: Dict,
        company_info: Optional[Dict] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate invoice PDF
        
        Args:
            invoice_data: Invoice details from InvoiceService.get_invoice_summary()
            company_info: Company/store information
company_info: Optional company details (name, address, GSTIN, logo)
            output_path: Path to save PDF (if None, returns bytes)
        
        Returns:
            PDF as bytes
        """
        # Default company info
        if not company_info:
            company_info = {
                "name": "R-DIOS Retail Store",
                "address": "123 Market Street, Mumbai, Maharashtra 400001",
                "phone": "+91-98765-43210",
                "email": "billing@rdios.com",
                "gstin": "27AABCU9603R1ZX",
                "pan": "AABCU9603R"
            }
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer if not output_path else output_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=6
        )
        
        # Invoice title
        elements.append(Paragraph("<b>TAX INVOICE</b>", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Company and customer info table
        info_data = [
            [
                Paragraph(f"<b>{company_info['name']}</b><br/>{company_info['address']}<br/>GSTIN: {company_info['gstin']}<br/>Phone: {company_info['phone']}", styles['Normal']),
                Paragraph(f"<b>Invoice Details</b><br/>Invoice #: {invoice_data['invoice']['invoice_number']}<br/>Date: {datetime.fromisoformat(invoice_data['invoice']['invoice_date']).strftime('%d-%b-%Y')}<br/>Due Date: {datetime.fromisoformat(invoice_data['invoice']['due_date']).strftime('%d-%b-%Y') if invoice_data['invoice']['due_date'] else 'N/A'}", styles['Normal'])
            ]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Invoice items header
        elements.append(Paragraph("<b>Invoice Details</b>", header_style))
        
        # Invoice line items
        item_data = [
            ['HSN Code', 'Taxable Amount', 'GST Rate', 'GST Amount', 'Total Amount']
        ]
        
        inv = invoice_data['invoice']
        item_data.append([
            inv['hsn_code'],
            f"₹{inv['taxable_amount']:,.2f}",
            f"{inv['tax_rate']}%",
            f"₹{inv['tax_amount']:,.2f}",
            f"₹{inv['total_amount']:,.2f}"
        ])
        
        item_table = Table(item_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Payment summary
        payment_summary = [
            ['Taxable Amount:', f"₹{inv['taxable_amount']:,.2f}"],
            [f"GST @ {inv['tax_rate']}%:", f"₹{inv['tax_amount']:,.2f}"],
            ['<b>Total Amount:</b>', f"<b>₹{inv['total_amount']:,.2f}</b>"],
            ['Amount Paid:', f"₹{inv['amount_paid']:,.2f}"],
            ['<b>Amount Due:</b>', f"<b>₹{inv['amount_due']:,.2f}</b>"],
        ]
        
        summary_data = [[Paragraph(item[0], styles['Normal']), Paragraph(item[1], styles['Normal'])] for item in payment_summary]
        summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
            ('LINEABOVE', (0, 4), (-1, 4), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        
        # Payment history if available
        if invoice_data['payments']:
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph("<b>Payment History</b>", header_style))
            
            payment_data = [['Date', 'Amount', 'Method', 'Reference']]
            for payment in invoice_data['payments']:
                payment_data.append([
                    datetime.fromisoformat(payment['date']).strftime('%d-%b-%Y'),
                    f"₹{payment['amount']:,.2f}",
                    payment['method'].upper(),
                    payment['reference'] or '-'
                ])
            
            payment_table = Table(payment_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2*inch])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(payment_table)
        
        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        footer_text = f"This is a computer-generated invoice. For queries, contact {company_info['email']}"
        elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
        
        # Payment status stamp
        if inv['payment_status'] == 'paid':
            elements.append(Spacer(1, 0.2 * inch))
            paid_style = ParagraphStyle('Paid', parent=styles['Normal'], fontSize=16, textColor=colors.green, alignment=TA_CENTER)
            elements.append(Paragraph("<b>✓ PAID</b>", paid_style))
        elif inv['payment_status'] == 'overdue':
            elements.append(Spacer(1, 0.2 * inch))
            overdue_style = ParagraphStyle('Overdue', parent=styles['Normal'], fontSize=16, textColor=colors.red, alignment=TA_CENTER)
            elements.append(Paragraph("<b>⚠ OVERDUE</b>", overdue_style))
        
        # Build PDF
        doc.build(elements)
        
        # Return bytes
        if not output_path:
            buffer.seek(0)
            return buffer.read()
        
        return None
    
    def save_invoice_pdf(self, invoice_data: Dict, output_path: str, company_info: Optional[Dict] = None):
        """Save invoice PDF to file"""
        self.generate_invoice_pdf(invoice_data, company_info, output_path)
        return output_path
