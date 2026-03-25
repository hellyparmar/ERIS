"""
Reporting Service
Handles generation of Excel (XLSX) and PDF reports.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from typing import List, Dict, Any
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.set_fill_color(79, 70, 229)  # Indigo
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'R-DIOS | Enterprise Report', 0, 1, 'C', fill=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

class ReportingService:
    @staticmethod
    def generate_pdf_report(data: List[Dict[str, Any]], title: str = "Report") -> BytesIO:
        """
        Generate a styled PDF report from a list of dictionaries.
        """
        pdf = PDFReport()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(33, 33, 33)
        pdf.cell(0, 10, title, 0, 1, 'L')
        pdf.set_font('Helvetica', 'I', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'L')
        pdf.ln(5)

        if not data:
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, "No data available for this report.", 0, 1)
            output = BytesIO()
            output.write(pdf.output(dest='S'))
            output.seek(0)
            return output

        # Table Header
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0)
        
        headers = list(data[0].keys())
        col_width = pdf.w / (len(headers) + 0.5) # Dynamic column width

        for header in headers:
            pdf.cell(col_width, 10, header.replace('_', ' ').upper(), 1, 0, 'C', fill=True)
        pdf.ln()

        # Table Data
        pdf.set_font('Helvetica', '', 9)
        fill = False
        
        for item in data:
            for key in headers:
                value = str(item.get(key, ""))
                pdf.cell(col_width, 10, value, 1, 0, 'C', fill=fill)
            pdf.ln()
            fill = not fill  # Zebra striping (optional, need to implement color toggle if desired)

        output = BytesIO()
        # FPDF.output() returns bytearray in new versions
        pdf_bytes = pdf.output()
        output.write(pdf_bytes)
        output.seek(0)
        return output

    @staticmethod
    def generate_excel_report(data: List[Dict[str, Any]], title: str = "Report") -> BytesIO:
        """
        Generate a styled Excel report from a list of dictionaries.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Data"

        # 1. Report Header
        ws.merge_cells('A1:F1')
        header_cell = ws['A1']
        header_cell.value = f"R-DIOS | {title}"
        header_cell.font = Font(size=16, bold=True, color="FFFFFF")
        header_cell.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
        header_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        ws['A2'] = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws.merge_cells('A2:F2')
        ws['A2'].alignment = Alignment(horizontal="center")
        ws['A2'].font = Font(italic=True, color="555555")

        if not data:
            ws['A4'] = "No data available for this report."
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            return output

        # 2. Column Headers (from first dict keys)
        headers = list(data[0].keys())
        header_row = 4
        
        thin_border = Border(left=Side(style='thin'), 
                             right=Side(style='thin'), 
                             top=Side(style='thin'), 
                             bottom=Side(style='thin'))

        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=header.replace('_', ' ').upper())
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

        # 3. Data Rows
        for row_idx, item in enumerate(data, start=header_row + 1):
            for col_idx, key in enumerate(headers, 1):
                value = item.get(key)
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                
                # Format numbers/dates if needed
                if isinstance(value, float):
                    cell.number_format = '#,##0.00'
                elif isinstance(value, int):
                    cell.number_format = '#,##0'

        # 4. Auto-size columns
        for col_idx, _ in enumerate(headers, 1):
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = 20

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def generate_sales_report(start_date: datetime, end_date: datetime, db_session) -> BytesIO:
        """
        Specialized report for Sales (Mock implementation for now)
        """
        # In a real scenario, query DB here. 
        # For now, we return mock data structure to prove the concept.
        mock_data = [
            {"order_id": "ORD-001", "date": "2023-10-01", "customer": "John Doe", "amount": 1500.00, "status": "Completed"},
            {"order_id": "ORD-002", "date": "2023-10-02", "customer": "Jane Smith", "amount": 2300.50, "status": "Completed"},
            {"order_id": "ORD-003", "date": "2023-10-02", "customer": "Bob Brown", "amount": 450.00, "status": "Pending"},
        ]
        return ReportingService.generate_excel_report(mock_data, title=f"Sales Report ({start_date.date()} to {end_date.date()})")

    @staticmethod
    def generate_inventory_report(db_session) -> BytesIO:
        """
        Specialized report for Inventory
        """
        mock_data = [
            {"product_name": "Premium T-Shirt", "sku": "TSH-001", "stock_qty": 45, "price": 499.00, "status": "In Stock"},
            {"product_name": "Slim Fit Jeans", "sku": "JNS-002", "stock_qty": 12, "price": 1299.00, "status": "Low Stock"},
            {"product_name": "Cotton Socks", "sku": "SOC-005", "stock_qty": 0, "price": 99.00, "status": "Out of Stock"},
        ]
        return ReportingService.generate_excel_report(mock_data, title="Inventory Status Report")

    @staticmethod
    def generate_purchase_order(data: List[Dict[str, Any]], title: str = "Purchase Order") -> BytesIO:
        """
        Generate a PDF Purchase Order
        """
        return ReportingService.generate_pdf_report(data, title)
