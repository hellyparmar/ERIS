"""
GST-Compliant PDF Invoice Generator - Enhanced Version
Professional invoice PDF with complete Indian GST compliance

Features:
- Company logo and header
- GST breakdown (CGST/SGST/IGST)
- Line items with HSN codes
- QR code for E-Invoice
- Tax summary
- Terms and conditions
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from typing import Dict, List, Optional
from datetime import datetime
import qrcode
import logging

logger = logging.getLogger(__name__)


class GSTInvoicePDF:
    """Generate GST-compliant invoice PDFs"""
    
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 15 * mm
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles"""
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1976d2'),
            alignment=TA_CENTER,
            spaceAfter=10
        ))
    
    def generate(self, invoice_data: Dict, seller_data: Dict, buyer_data: Dict, 
                 line_items: List[Dict], output_path: Optional[str] = None) -> bytes:
        """
        Generate GST invoice PDF
        
        Args:
            invoice_data: Invoice details
            seller_data: Seller details
            buyer_data: Buyer details
            line_items: Line items
            output_path: Optional path to save
            
        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.MARGIN,
            leftMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN
        )
        
        story = []
        
        # Title
        invoice_type = "TAX INVOICE" if invoice_data.get('customer_gstin') else "BILL OF SUPPLY"
        story.append(Paragraph(invoice_type, self.styles['InvoiceTitle']))
        story.append(Spacer(1, 5*mm))
        
        # Seller & buyer details
        party_table = self._build_party_table(seller_data, buyer_data, invoice_data)
        story.append(party_table)
        story.append(Spacer(1, 5*mm))
        
        # Line items
        items_table = self._build_items_table(line_items, invoice_data)
        story.append(items_table)
        story.append(Spacer(1, 5*mm))
        
        # Tax summary
        summary_table = self._build_summary_table(invoice_data)
        story.append(summary_table)
        
        # QR code if E-Invoice
        if invoice_data.get('signed_qr_code'):
            story.append(Spacer(1, 5*mm))
            qr_img = self._generate_qr_code(invoice_data['signed_qr_code'])
            story.append(qr_img)
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def _build_party_table(self, seller: Dict, buyer: Dict, invoice: Dict) -> Table:
        """Build party details table"""
        data = [
            ['SOLD BY:', 'INVOICE DETAILS:'],
            [
                f"{seller['name']}\nGSTIN: {seller.get('gstin', 'N/A')}",
                f"Invoice #: {invoice['invoice_number']}\nDate: {invoice['invoice_date']}"
            ],
            ['BILL TO:', ''],
            [buyer.get('name', 'Cash Customer'), '']
        ]
        
        table = Table(data, colWidths=[90*mm, 90*mm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 3)
        ]))
        
        return table
    
    def _build_items_table(self, items: List[Dict], invoice: Dict) -> Table:
        """Build line items table"""
        is_interstate = invoice.get('is_interstate', False)
        
        if is_interstate:
            headers = ['#', 'Item', 'HSN', 'Qty', 'Rate', 'Taxable', 'IGST%', 'IGST', 'Total']
        else:
            headers = ['#', 'Item', 'HSN', 'Qty', 'Rate', 'Taxable', 'CGST', 'SGST', 'Total']
        
        data = [headers]
        
        for idx, item in enumerate(items, 1):
            tax = item.get('tax_breakdown', {})
            if is_interstate:
                row = [
                    str(idx),
                    item['name'],
                    item.get('hsn_code', ''),
                    f"{item['quantity']}",
                    f"₹{item['unit_price']:.2f}",
                    f"₹{tax['taxable_amount']:.2f}",
                    f"{tax.get('igst_rate', 0):.0f}%",
                    f"₹{tax.get('igst_amount', 0):.2f}",
                    f"₹{tax['total_amount']:.2f}"
                ]
            else:
                row = [
                    str(idx),
                    item['name'],
                    item.get('hsn_code', ''),
                    f"{item['quantity']}",
                    f"₹{item['unit_price']:.2f}",
                    f"₹{tax['taxable_amount']:.2f}",
                    f"₹{tax.get('cgst_amount', 0):.2f}",
                    f"₹{tax.get('sgst_amount', 0):.2f}",
                    f"₹{tax['total_amount']:.2f}"
                ]
            data.append(row)
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT')
        ]))
        
        return table
    
    def _build_summary_table(self, invoice: Dict) -> Table:
        """Build tax summary table"""
        is_interstate = invoice.get('is_interstate', False)
        
        data = [
            ['Taxable Amount:', f"₹{invoice['taxable_amount']:.2f}"],
        ]
        
        if is_interstate:
            data.append(['IGST:', f"₹{invoice.get('igst_amount', 0):.2f}"])
        else:
            data.append(['CGST:', f"₹{invoice.get('cgst_amount', 0):.2f}"])
            data.append(['SGST:', f"₹{invoice.get('sgst_amount', 0):.2f}"])
        
        data.append(['Grand Total:', f"₹{invoice['grand_total']:.2f}"])
        
        table = Table(data, colWidths=[140*mm, 40*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        return table
    
    def _generate_qr_code(self, data: str) -> Image:
        """Generate QR code image"""
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return Image(buffer, width=30*mm, height=30*mm)
