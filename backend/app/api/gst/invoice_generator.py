"""
GST PDF Invoice Generator
Creates compliant B2B/B2C Tax Invoices using ReportLab.
"""

from __future__ import annotations
import io
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    _RL_AVAILABLE = True
except ImportError:
    _RL_AVAILABLE = False


class GSTInvoiceGenerator:
    """PDF generation for Indian GST Invoices."""

    def __init__(self, company_config: Dict[str, Any]):
        """
        company_config:
            name, address, gstin, state_code, pan, cin, logo_path
        """
        self.config = company_config
        if not _RL_AVAILABLE:
            raise ImportError("reportlab package is not installed. Run 'pip install reportlab'.")
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='RightHeading', parent=self.styles['Heading3'], alignment=2)) # 2 is TA_RIGHT

    def generate_pdf(self, invoice_data: Dict) -> bytes:
        """
        Generate a PDF invoice in memory and return as bytes.

        invoice_data:
            invoice_number, date, customer: {name, address, gstin, state_code},
            items: [{name, hsn, qty, rate, amount, gst_rate, cgst, sgst, igst, total}],
            totals: {taxable, cgst, sgst, igst, grand_total, amount_in_words}
            is_interstate (bool)
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        elements = []
        is_interstate = invoice_data.get("is_interstate", False)

        # ─── 1. Header & Title ──────────────────────────────────────────────────
        title_str = "TAX INVOICE" if invoice_data.get("customer", {}).get("gstin") else "RETAIL INVOICE"
        elements.append(Paragraph(f"<b>{title_str}</b>", self.styles["Title"]))
        elements.append(Spacer(1, 10))

        # ─── 2. Company & Customer Details ──────────────────────────────────────
        comp = self.config
        cust = invoice_data.get("customer", {})
        
        comp_text = f"""
        <b>{comp.get('name', 'Company Name')}</b><br/>
        {comp.get('address', 'Address Line 1')}<br/>
        <b>GSTIN:</b> {comp.get('gstin', 'Unregistered')}<br/>
        <b>State:</b> {comp.get('state_code', '27')}
        """

        cust_text = f"""
        <b>Billed To:</b><br/>
        <b>{cust.get('name', 'Cash Customer')}</b><br/>
        {cust.get('address', 'Walk-in')}<br/>
        <b>GSTIN:</b> {cust.get('gstin', 'Unregistered')}<br/>
        <b>State:</b> {cust.get('state_code', 'Unknown')}
        """

        inv_text = f"""
        <b>Invoice No:</b> {invoice_data.get('invoice_number')}<br/>
        <b>Date:</b> {invoice_data.get('date', datetime.today().strftime('%d-%b-%Y'))}<br/>
        <b>Place of Supply:</b> {cust.get('state_code', comp.get('state_code', '27'))}
        """

        header_table_data = [
            [Paragraph(comp_text, self.styles["Normal"]), Paragraph(cust_text, self.styles["Normal"]), Paragraph(inv_text, self.styles["Normal"])]
        ]
        
        ht = Table(header_table_data, colWidths=[6.5*cm, 6.5*cm, 5.5*cm])
        ht.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(ht)
        elements.append(Spacer(1, 20))

        # ─── 3. Line Items Table ────────────────────────────────────────────────
        if is_interstate:
            headers = ["S.No", "Description / HSN", "Qty", "Rate", "Taxable", "IGST %", "IGST Amt", "Total"]
            col_widths = [1*cm, 6*cm, 1.5*cm, 2*cm, 2.5*cm, 1.5*cm, 2*cm, 2.5*cm]
        else:
            headers = ["S.No", "Description / HSN", "Qty", "Rate", "Taxable", "CGST", "SGST", "Total"]
            col_widths = [1*cm, 6*cm, 1.2*cm, 1.8*cm, 2*cm, 2*cm, 2*cm, 2.5*cm]

        item_data = [headers]
        
        for idx, item in enumerate(invoice_data.get("items", [])):
            desc = f"{item.get('name')}\nHSN: {item.get('hsn', '')}"
            
            if is_interstate:
                row = [
                    str(idx + 1),
                    desc,
                    str(item.get("qty", 1)),
                    f"{float(item.get('rate', 0)):.2f}",
                    f"{float(item.get('amount', 0)):.2f}", # Taxable
                    f"{float(item.get('gst_rate', 0)):.1f}%",
                    f"{float(item.get('igst', 0)):.2f}",
                    f"{float(item.get('total', 0)):.2f}"
                ]
            else:
                row = [
                    str(idx + 1),
                    desc,
                    str(item.get("qty", 1)),
                    f"{float(item.get('rate', 0)):.2f}",
                    f"{float(item.get('amount', 0)):.2f}", # Taxable
                    f"{float(item.get('cgst', 0)):.2f} ({(float(item.get('gst_rate', 0))/2):.1f}%)",
                    f"{float(item.get('sgst', 0)):.2f} ({(float(item.get('gst_rate', 0))/2):.1f}%)",
                    f"{float(item.get('total', 0)):.2f}"
                ]
            item_data.append(row)

        items_table = Table(item_data, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),   # Description left-aligned
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'), # Numbers right-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 10))

        # ─── 4. Totals & Footer ─────────────────────────────────────────────────
        totals = invoice_data.get("totals", {})
        
        tot_data = [
            ["Total Taxable Value:", f"₹ {float(totals.get('taxable', 0)):.2f}"]
        ]
        
        if is_interstate:
            tot_data.append(["Total IGST:", f"₹ {float(totals.get('igst', 0)):.2f}"])
        else:
            tot_data.append(["Total CGST:", f"₹ {float(totals.get('cgst', 0)):.2f}"])
            tot_data.append(["Total SGST:", f"₹ {float(totals.get('sgst', 0)):.2f}"])
            
        tot_data.append(["Grand Total:", f"₹ {float(totals.get('grand_total', 0)):.2f}"])

        # Create a 2x1 grid for bottom section (Left: Words/Bank, Right: Totals)
        left_footer = f"""
        <b>Amount in Words:</b><br/>
        {totals.get('amount_in_words', 'Rupees ... Only')}<br/><br/>
        <b>Bank Details:</b><br/>
        Bank: {comp.get('bank_name', 'HDFC Bank')}<br/>
        A/C: {comp.get('bank_ac', 'XXXX XXXX XXXX')}<br/>
        IFSC: {comp.get('bank_ifsc', 'HDFC0001234')}
        """
        
        totals_t = Table(tot_data, colWidths=[3.5*cm, 3*cm])
        totals_t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Bold the last row (Grand Total)
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
            ('PADDING', (0, 0), (-1, -1), 4)
        ]))

        footer_table = Table([[Paragraph(left_footer, self.styles["Normal"]), self._get_qr_code(invoice_data), totals_t]], colWidths=[9*cm, 3.5*cm, 6*cm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        elements.append(footer_table)
        
        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

    def _get_qr_code(self, invoice_data: Dict) -> Any:
        """Generate a QR code image for the invoice."""
        try:
            import qrcode
            from reportlab.platypus import Image
            
            qr_data = f"Invoice: {invoice_data.get('invoice_number')}\n" \
                      f"GSTIN: {self.config.get('gstin')}\n" \
                      f"Total: {invoice_data.get('totals', {}).get('grand_total')}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            img.save(img_buffer)
            img_buffer.seek(0)
            
            return Image(img_buffer, width=2.5*cm, height=2.5*cm)
        except ImportError:
            return Paragraph("<b>[QR Code]</b><br/>Install 'qrcode' to view", self.styles["Normal"])
        except Exception as e:
            return Paragraph(f"Error: {str(e)}", self.styles["Normal"])
