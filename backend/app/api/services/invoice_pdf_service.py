"""
Invoice PDF Generation Service
Generates professional PDF invoices with branding and tax details
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import os
import logging

logger = logging.getLogger(__name__)


class InvoicePDFGenerator:
    """Generate professional PDF invoices"""
    
    def __init__(self):
        self.page_size = A4
        self.width, self.height = self.page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceValue',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica'
        ))
    
    def generate_pdf(self, invoice_data):
        """
        Generate PDF from invoice data
        
        Args:
            invoice_data: Dict with invoice details
            
        Returns:
            BytesIO: PDF file in memory
        """
        try:
            pdf_buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=self.page_size,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build content
            story = []
            
            # Header with company info
            story.append(self._build_header(invoice_data))
            story.append(Spacer(1, 0.3*inch))
            
            # Invoice title and details
            story.append(self._build_invoice_header(invoice_data))
            story.append(Spacer(1, 0.2*inch))
            
            # Customer and invoice info
            story.append(self._build_customer_info(invoice_data))
            story.append(Spacer(1, 0.3*inch))
            
            # Line items table
            story.append(self._build_line_items_table(invoice_data))
            story.append(Spacer(1, 0.2*inch))
            
            # Totals section
            story.append(self._build_totals_section(invoice_data))
            story.append(Spacer(1, 0.3*inch))
            
            # Payment terms and notes
            if invoice_data.get('notes'):
                story.append(self._build_notes_section(invoice_data))
                story.append(Spacer(1, 0.2*inch))
            
            # Footer
            story.append(self._build_footer())
            
            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            
            logger.info(f"PDF generated successfully for invoice {invoice_data.get('invoice_number')}")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise
    
    def _build_header(self, invoice_data):
        """Build document header with company info"""
        header_data = [
            [
                Paragraph("<b>ENTERPRISE RETAIL SYSTEM</b>", self.styles['Heading2']),
                Paragraph(f"<b>{invoice_data.get('invoice_number', 'INVOICE')}</b>", 
                         ParagraphStyle('Right', parent=self.styles['Heading2'], 
                                      alignment=2, textColor=colors.HexColor('#3b82f6')))
            ],
            [
                Paragraph("Professional Invoicing & Billing Solution", self.styles['Normal']),
                Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", 
                         self.styles['Normal'])
            ]
        ]
        
        table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
        ]))
        
        return table
    
    def _build_invoice_header(self, invoice_data):
        """Build invoice title and key info"""
        data = [
            [
                Paragraph("<b>INVOICE</b>", self.styles['CustomTitle']),
                self._build_invoice_meta(invoice_data)
            ]
        ]
        
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return table
    
    def _build_invoice_meta(self, invoice_data):
        """Build invoice metadata box"""
        meta_data = [
            [
                Paragraph("<b>Invoice #:</b>", self.styles['InvoiceLabel']),
                Paragraph(invoice_data.get('invoice_number', 'N/A'), self.styles['InvoiceValue'])
            ],
            [
                Paragraph("<b>Date:</b>", self.styles['InvoiceLabel']),
                Paragraph(invoice_data.get('invoice_date', datetime.now().isoformat()), 
                         self.styles['InvoiceValue'])
            ],
            [
                Paragraph("<b>Due Date:</b>", self.styles['InvoiceLabel']),
                Paragraph(invoice_data.get('due_date', 'N/A'), self.styles['InvoiceValue'])
            ],
            [
                Paragraph("<b>Status:</b>", self.styles['InvoiceLabel']),
                Paragraph(f"<font color='{self._get_status_color(invoice_data.get('status'))}'"
                         f">{invoice_data.get('status', 'N/A').upper()}</font>", 
                         self.styles['InvoiceValue'])
            ]
        ]
        
        table = Table(meta_data, colWidths=[1.2*inch, 1.3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (1, 0), (1, -1), 10),
        ]))
        
        return table
    
    def _get_status_color(self, status):
        """Get color for status"""
        colors_map = {
            'draft': '#6b7280',
            'sent': '#3b82f6',
            'paid': '#10b981',
            'cancelled': '#ef4444',
            'overdue': '#f97316'
        }
        return colors_map.get(status, '#6b7280')
    
    def _build_customer_info(self, invoice_data):
        """Build customer and company info"""
        data = [
            [
                Paragraph("<b>Bill To</b>", self.styles['Heading3']),
                Paragraph("<b>Ship To</b>", self.styles['Heading3'])
            ],
            [
                self._format_address(invoice_data, 'bill'),
                self._format_address(invoice_data, 'ship')
            ]
        ]
        
        table = Table(data, colWidths=[3.25*inch, 3.25*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
        ]))
        
        return table
    
    def _format_address(self, invoice_data, address_type):
        """Format address block"""
        customer_name = invoice_data.get('customer_name', 'N/A')
        customer_email = invoice_data.get('customer_email', '')
        customer_phone = invoice_data.get('customer_phone', '')
        
        address_text = f"""
<b>{customer_name}</b><br/>
{customer_email}<br/>
{customer_phone}
        """.strip()
        
        return Paragraph(address_text, self.styles['Normal'])
    
    def _build_line_items_table(self, invoice_data):
        """Build line items table"""
        line_items = invoice_data.get('line_items', [])
        
        # Header row
        data = [[
            Paragraph("<b>Description</b>", self.styles['Heading4']),
            Paragraph("<b>Qty</b>", self.styles['Heading4']),
            Paragraph("<b>Unit Price</b>", self.styles['Heading4']),
            Paragraph("<b>GST %</b>", self.styles['Heading4']),
            Paragraph("<b>Amount</b>", self.styles['Heading4'])
        ]]
        
        # Data rows
        total_line = 0
        for item in line_items:
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            gst_rate = item.get('gst_rate', 18)
            line_total = quantity * unit_price
            total_line += line_total
            
            data.append([
                Paragraph(item.get('product_name', 'N/A'), self.styles['Normal']),
                Paragraph(str(quantity), self.styles['Normal']),
                Paragraph(f"₹{unit_price:,.2f}", self.styles['Normal']),
                Paragraph(f"{gst_rate}%", self.styles['Normal']),
                Paragraph(f"₹{line_total:,.2f}", self.styles['Normal'])
            ])
        
        table = Table(data, colWidths=[2.2*inch, 0.6*inch, 1*inch, 0.7*inch, 1.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        
        return table
    
    def _build_totals_section(self, invoice_data):
        """Build totals section"""
        subtotal = invoice_data.get('subtotal', 0)
        gst_amount = invoice_data.get('gst_amount', 0)
        tds_amount = invoice_data.get('tds_amount', 0)
        total_amount = invoice_data.get('total_amount', 0)
        amount_paid = invoice_data.get('amount_paid', 0)
        balance_amount = invoice_data.get('balance_amount', 0)
        
        # Spacer
        data = [
            [Paragraph("", self.styles['Normal']), Paragraph("", self.styles['Normal'])],
        ]
        
        # Subtotal
        data.append([
            Paragraph("<b>Subtotal</b>", self.styles['Normal']),
            Paragraph(f"<b>₹{subtotal:,.2f}</b>", self.styles['Normal'])
        ])
        
        # GST
        if gst_amount > 0:
            gst_rate = invoice_data.get('gst_rate', 18)
            data.append([
                Paragraph(f"GST ({gst_rate}%)", self.styles['Normal']),
                Paragraph(f"₹{gst_amount:,.2f}", self.styles['Normal'])
            ])
        
        # TDS
        if tds_amount > 0:
            tds_rate = invoice_data.get('tds_rate', 0)
            data.append([
                Paragraph(f"TDS ({tds_rate}%)", self.styles['Normal']),
                Paragraph(f"- ₹{tds_amount:,.2f}", self.styles['Normal'])
            ])
        
        # Total
        data.append([
            Paragraph("<b>Total Amount</b>", ParagraphStyle('Bold', parent=self.styles['Normal'], 
                                                          fontName='Helvetica-Bold', fontSize=12)),
            Paragraph(f"<b>₹{total_amount:,.2f}</b>", ParagraphStyle('Bold', parent=self.styles['Normal'],
                                                                    fontName='Helvetica-Bold', fontSize=12,
                                                                    textColor=colors.HexColor('#3b82f6')))
        ])
        
        # Amount Paid
        if amount_paid > 0:
            data.append([
                Paragraph("Amount Paid", self.styles['Normal']),
                Paragraph(f"₹{amount_paid:,.2f}", self.styles['Normal'])
            ])
        
        # Balance Due
        data.append([
            Paragraph("<b>Balance Due</b>", ParagraphStyle('Bold', parent=self.styles['Normal'],
                                                         fontName='Helvetica-Bold')),
            Paragraph(f"<b>₹{balance_amount:,.2f}</b>", ParagraphStyle('Bold', parent=self.styles['Normal'],
                                                                      fontName='Helvetica-Bold',
                                                                      textColor=colors.HexColor('#ef4444')))
        ])
        
        table = Table(data, colWidths=[4.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return table
    
    def _build_notes_section(self, invoice_data):
        """Build notes section"""
        notes = invoice_data.get('notes', '')
        
        data = [
            [Paragraph("<b>Notes & Terms</b>", self.styles['Heading3'])],
            [Paragraph(notes, self.styles['Normal'])]
        ]
        
        table = Table(data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ]))
        
        return table
    
    def _build_footer(self):
        """Build footer"""
        footer_text = """
        <font size="8" color="#6b7280">
        Thank you for your business! | Enterprise Retail Intelligence System | Confidential
        </font>
        """
        
        return Paragraph(footer_text, ParagraphStyle('Footer', parent=self.styles['Normal'],
                                                    alignment=1, fontSize=8))


# Export service
pdf_generator = InvoicePDFGenerator()

def generate_invoice_pdf(invoice_data):
    """Generate invoice PDF"""
    return pdf_generator.generate_pdf(invoice_data)
