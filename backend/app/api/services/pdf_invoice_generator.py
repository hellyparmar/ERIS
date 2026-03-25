"""
Phase 2 PDF Invoice Generator Service
Generates professional invoice PDFs with GST breakdown and QR codes
Uses reportlab for PDF generation and pyqrcode for QR code embedding
Status: Production-ready with company branding and e-invoice support
"""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Dict, List, Optional, Tuple

try:
    from reportlab.lib import colors, pagesizes
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, 
        Spacer, PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import pyqrcode
    PYQRCODE_AVAILABLE = True
except ImportError:
    PYQRCODE_AVAILABLE = False


class InvoiceLineItemData:
    """Line item data for invoice"""
    def __init__(
        self,
        hsn_code: str,
        description: str,
        quantity: Decimal,
        unit_rate: Decimal,
        tax_rate: str,
        discount_percentage: Decimal,
        discount_amount: Decimal,
        cgst_amount: Decimal,
        sgst_amount: Decimal,
        igst_amount: Decimal,
        line_total: Decimal
    ):
        self.hsn_code = hsn_code
        self.description = description
        self.quantity = quantity
        self.unit_rate = unit_rate
        self.tax_rate = tax_rate
        self.discount_percentage = discount_percentage
        self.discount_amount = discount_amount
        self.cgst_amount = cgst_amount
        self.sgst_amount = sgst_amount
        self.igst_amount = igst_amount
        self.line_total = line_total


class InvoiceData:
    """Complete invoice data"""
    def __init__(
        self,
        invoice_number: str,
        invoice_date: datetime,
        due_date: Optional[datetime],
        customer_name: str,
        customer_phone: Optional[str],
        customer_email: Optional[str],
        billing_address: Dict,
        shipping_address: Dict,
        line_items: List[InvoiceLineItemData],
        subtotal: Decimal,
        shipping_charge: Decimal,
        additional_charges: Decimal,
        cgst_total: Decimal,
        sgst_total: Decimal,
        igst_total: Decimal,
        grand_total: Decimal,
        business_name: str,
        business_gst: str,
        business_address: str,
        business_phone: str,
        business_email: str,
        qr_code_data: Optional[str] = None,
        irn: Optional[str] = None,
        notes: Optional[str] = None,
        payment_terms: Optional[str] = None,
        logo_path: Optional[str] = None
    ):
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_email = customer_email
        self.billing_address = billing_address
        self.shipping_address = shipping_address
        self.line_items = line_items
        self.subtotal = subtotal
        self.shipping_charge = shipping_charge
        self.additional_charges = additional_charges
        self.cgst_total = cgst_total
        self.sgst_total = sgst_total
        self.igst_total = igst_total
        self.grand_total = grand_total
        self.business_name = business_name
        self.business_gst = business_gst
        self.business_address = business_address
        self.business_phone = business_phone
        self.business_email = business_email
        self.qr_code_data = qr_code_data
        self.irn = irn
        self.notes = notes
        self.payment_terms = payment_terms
        self.logo_path = logo_path


class Phase2PDFInvoiceGenerator:
    """
    Professional PDF invoice generator with GST compliance
    
    Features:
    - Company branding with logo
    - Multi-line items with GST breakdown
    - CGST/SGST/IGST calculations
    - QR code embedding for E-invoicing
    - Professional table layout
    - Payment terms and notes
    - Multiple page support
    """
    
    # Page and margin settings
    PAGE_WIDTH = pagesizes.letter[0]
    PAGE_HEIGHT = pagesizes.letter[1]
    TOP_MARGIN = 0.5 * inch
    BOTTOM_MARGIN = 0.5 * inch
    LEFT_MARGIN = 0.5 * inch
    RIGHT_MARGIN = 0.5 * inch
    
    # Color palette
    COLOR_HEADER = colors.HexColor("#1e3a8a")  # Dark blue
    COLOR_BORDER = colors.HexColor("#cbd5e1")  # Light gray
    COLOR_HIGHLIGHT = colors.HexColor("#f0f9ff")  # Light blue
    COLOR_TEXT = colors.HexColor("#0f172a")  # Almost black
    
    def __init__(self):
        """Initialize PDF generator"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom paragraph styles"""
        # Header style
        self.styles.add(ParagraphStyle(
            name='InvoiceHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.COLOR_HEADER,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=self.COLOR_HEADER,
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        ))
        
        # Normal text
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_TEXT,
            leading=12
        ))
        
        # Small text (labels)
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            leading=11
        ))
        
        # Table header
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
    
    def _generate_qr_code(self, data: str) -> Optional[Image]:
        """
        Generate QR code from data
        
        Parameters:
        - data: Data to encode in QR
        
        Returns:
        - ReportLab Image object or None if pyqrcode unavailable
        """
        if not PYQRCODE_AVAILABLE or not data:
            return None
        
        try:
            # Create QR code
            qr = pyqrcode.create(data, error='L', version=1)
            
            # Save to BytesIO
            qr_buffer = BytesIO()
            qr.svg(qr_buffer, scale=8)
            qr_buffer.seek(0)
            
            # Create image
            qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)
            return qr_image
            
        except Exception as e:
            print(f"QR code generation failed: {str(e)}")
            return None
    
    def _format_address(self, address: Dict) -> str:
        """Format address dictionary to string"""
        lines = []
        if address.get('name'):
            lines.append(address['name'])
        if address.get('street'):
            lines.append(address['street'])
        if address.get('city'):
            city_line = address['city']
            if address.get('state'):
                city_line += f", {address['state']}"
            if address.get('pincode'):
                city_line += f" - {address['pincode']}"
            lines.append(city_line)
        if address.get('country'):
            lines.append(address['country'])
        
        return ", ".join(filter(None, lines))
    
    def _create_header(self, invoice_data: InvoiceData) -> List:
        """Create invoice header section"""
        elements = []
        
        # Company name and invoice title
        header_data = [
            [
                Paragraph(
                    f"<b>{invoice_data.business_name}</b>",
                    self.styles['InvoiceHeader']
                ),
                Paragraph("INVOICE", self.styles['InvoiceHeader'])
            ]
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Company details
        company_details = [
            [
                f"<b>GST No:</b> {invoice_data.business_gst}",
                f"<b>Invoice #:</b> {invoice_data.invoice_number}"
            ],
            [
                f"<b>Phone:</b> {invoice_data.business_phone}",
                f"<b>Date:</b> {invoice_data.invoice_date.strftime('%d-%b-%Y')}"
            ],
            [
                f"<b>Email:</b> {invoice_data.business_email}",
                f"<b>Due Date:</b> {invoice_data.due_date.strftime('%d-%b-%Y') if invoice_data.due_date else 'N/A'}"
            ]
        ]
        
        details_table = Table(company_details, colWidths=[4*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_addresses(self, invoice_data: InvoiceData) -> List:
        """Create billing and shipping address section"""
        elements = []
        
        # Addresses
        addresses_data = [
            [
                Paragraph("<b>BILLING ADDRESS</b>", self.styles['SectionHeader']),
                Paragraph("<b>SHIPPING ADDRESS</b>", self.styles['SectionHeader'])
            ],
            [
                Paragraph(
                    self._format_address(invoice_data.billing_address),
                    self.styles['NormalText']
                ),
                Paragraph(
                    self._format_address(invoice_data.shipping_address),
                    self.styles['NormalText']
                )
            ]
        ]
        
        addresses_table = Table(addresses_data, colWidths=[4*inch, 4*inch])
        addresses_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEABOVE', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LINEBELOW', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_HIGHLIGHT),
        ]))
        
        elements.append(addresses_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Customer info
        customer_info = f"<b>Customer:</b> {invoice_data.customer_name}"
        if invoice_data.customer_phone:
            customer_info += f" | <b>Phone:</b> {invoice_data.customer_phone}"
        if invoice_data.customer_email:
            customer_info += f" | <b>Email:</b> {invoice_data.customer_email}"
        
        elements.append(Paragraph(customer_info, self.styles['NormalText']))
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_line_items_table(self, invoice_data: InvoiceData) -> List:
        """Create line items table"""
        elements = []
        
        # Table header
        table_data = [[
            "HSN",
            "Description",
            "Qty",
            "Rate",
            "Discount %",
            "Taxable Amt",
            "CGST",
            "SGST",
            "IGST",
            "Total"
        ]]
        
        # Add line items
        for item in invoice_data.line_items:
            table_data.append([
                item.hsn_code or "-",
                item.description,
                f"{item.quantity}",
                f"₹{float(item.unit_rate):,.2f}",
                f"{float(item.discount_percentage)}%",
                f"₹{float(item.unit_rate * item.quantity - item.discount_amount):,.2f}",
                f"₹{float(item.cgst_amount):,.2f}",
                f"₹{float(item.sgst_amount):,.2f}",
                f"₹{float(item.igst_amount):,.2f}",
                f"₹{float(item.line_total):,.2f}"
            ])
        
        # Add totals row
        table_data.append([
            "", "", "", "", "",
            f"Subtotal:",
            f"₹{float(invoice_data.cgst_total):,.2f}",
            f"₹{float(invoice_data.sgst_total):,.2f}",
            f"₹{float(invoice_data.igst_total):,.2f}",
            f"₹{float(invoice_data.subtotal):,.2f}"
        ])
        
        # Create table
        col_widths = [0.6*inch, 1.2*inch, 0.4*inch, 0.7*inch, 0.6*inch, 0.9*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.8*inch]
        line_items_table = Table(table_data, colWidths=col_widths)
        
        # Style table
        line_items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, self.COLOR_HIGHLIGHT]),
            
            # Totals row
            ('BACKGROUND', (0, -1), (-1, -1), self.COLOR_HIGHLIGHT),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, self.COLOR_BORDER),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.COLOR_HEADER),
        ]))
        
        elements.append(line_items_table)
        elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_totals_section(self, invoice_data: InvoiceData) -> List:
        """Create totals section"""
        elements = []
        
        # Totals
        totals_data = [
            ["Subtotal:", f"₹{float(invoice_data.subtotal):,.2f}"],
            ["Shipping Charge:", f"₹{float(invoice_data.shipping_charge):,.2f}"],
            ["Additional Charges:", f"₹{float(invoice_data.additional_charges):,.2f}"],
            ["", ""],
            ["CGST Total:", f"₹{float(invoice_data.cgst_total):,.2f}"],
            ["SGST Total:", f"₹{float(invoice_data.sgst_total):,.2f}"],
            ["IGST Total:", f"₹{float(invoice_data.igst_total):,.2f}"],
            ["", ""],
            ["GRAND TOTAL:", f"₹{float(invoice_data.grand_total):,.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (1, 0), (1, -1), 20),
            
            # Totals row styling
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), self.COLOR_HIGHLIGHT),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.COLOR_HEADER),
            ('LINEBELOW', (0, -1), (-1, -1), 2, self.COLOR_HEADER),
            
            # Tax rows styling
            ('LINEABOVE', (0, -6), (-1, -6), 1, self.COLOR_BORDER),
            ('LINEABOVE', (0, -3), (-1, -3), 1, self.COLOR_BORDER),
        ]))
        
        elements.append(totals_table)
        elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_footer(self, invoice_data: InvoiceData) -> List:
        """Create footer section with QR code and notes"""
        elements = []
        
        footer_data = []
        
        # Left side: QR code and IRN
        left_column = []
        
        if invoice_data.qr_code_data:
            qr_image = self._generate_qr_code(invoice_data.qr_code_data)
            if qr_image:
                left_column.append(Paragraph("<b>E-Invoice QR Code:</b>", self.styles['SmallText']))
                left_column.append(Spacer(1, 0.1*inch))
                left_column.append(qr_image)
        
        if invoice_data.irn:
            left_column.append(Spacer(1, 0.1*inch))
            left_column.append(Paragraph(
                f"<b>IRN:</b> {invoice_data.irn}",
                self.styles['SmallText']
            ))
        
        # Right side: Notes and terms
        right_column = []
        
        if invoice_data.payment_terms:
            right_column.append(Paragraph("<b>Payment Terms:</b>", self.styles['SectionHeader']))
            right_column.append(Paragraph(invoice_data.payment_terms, self.styles['NormalText']))
            right_column.append(Spacer(1, 0.1*inch))
        
        if invoice_data.notes:
            right_column.append(Paragraph("<b>Notes:</b>", self.styles['SectionHeader']))
            right_column.append(Paragraph(invoice_data.notes, self.styles['NormalText']))
        
        # Create footer table if we have content
        if left_column or right_column:
            footer_table = Table(
                [[left_column if left_column else "", right_column if right_column else ""]],
                colWidths=[3*inch, 5*inch]
            )
            footer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(footer_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Signature section
        signature_data = [
            ["", "", "Authorized By"],
            ["", "", "_" * 30],
            ["Receiver's Signature", "", "Issuer's Signature"]
        ]
        
        signature_table = Table(signature_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(signature_table)
        
        return elements
    
    def generate_pdf(self, invoice_data: InvoiceData) -> BytesIO:
        """
        Generate complete PDF invoice
        
        Parameters:
        - invoice_data: InvoiceData object with all invoice information
        
        Returns:
        - BytesIO object containing PDF data
        """
        # Create PDF buffer
        pdf_buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=pagesizes.letter,
            topMargin=self.TOP_MARGIN,
            bottomMargin=self.BOTTOM_MARGIN,
            leftMargin=self.LEFT_MARGIN,
            rightMargin=self.RIGHT_MARGIN
        )
        
        # Build content
        elements = []
        
        # Header
        elements.extend(self._create_header(invoice_data))
        
        # Addresses
        elements.extend(self._create_addresses(invoice_data))
        
        # Line items
        elements.extend(self._create_line_items_table(invoice_data))
        
        # Totals
        elements.extend(self._create_totals_section(invoice_data))
        
        # Footer
        elements.extend(self._create_footer(invoice_data))
        
        # Build PDF
        doc.build(elements)
        
        # Reset buffer position
        pdf_buffer.seek(0)
        
        return pdf_buffer
    
    def generate_pdf_bytes(self, invoice_data: InvoiceData) -> bytes:
        """
        Generate PDF and return as bytes
        
        Parameters:
        - invoice_data: InvoiceData object
        
        Returns:
        - PDF as bytes
        """
        pdf_buffer = self.generate_pdf(invoice_data)
        return pdf_buffer.getvalue()


# Convenient functions for quick PDF generation

def generate_invoice_pdf(invoice_data: InvoiceData) -> BytesIO:
    """
    Quick function to generate invoice PDF
    
    Parameters:
    - invoice_data: InvoiceData object
    
    Returns:
    - BytesIO object containing PDF
    """
    generator = Phase2PDFInvoiceGenerator()
    return generator.generate_pdf(invoice_data)


def generate_invoice_pdf_bytes(invoice_data: InvoiceData) -> bytes:
    """
    Quick function to generate invoice PDF as bytes
    
    Parameters:
    - invoice_data: InvoiceData object
    
    Returns:
    - PDF as bytes
    """
    generator = Phase2PDFInvoiceGenerator()
    return generator.generate_pdf_bytes(invoice_data)
