import asyncio
from app.integrations.tally.export_service import TallyExportService
from app.integrations.gst.report_service import GSTReportService
from datetime import date
import os

async def run_tests():
    print("Testing Tally CSV Export...")
    tally = TallyExportService()
    csv_str = tally.export_sales_to_csv([], date.today(), date.today())
    if "Date,Voucher Type" in csv_str:
        print("✓ CSV Export OK")
    else:
        print("✗ CSV Export Failed")
        
    print("Testing GST PDF Generation...")
    gst = GSTReportService()
    # Test GSTR1 PDF
    pdf_bytes = gst.generate_gstr1_summary("27AADCB2230M1Z2", date.today(), date.today(), 1000, 180)
    if len(pdf_bytes) > 0:
        print("✓ GST PDF Generation OK")
    else:
        print("✗ GST PDF Generation Failed")

if __name__ == "__main__":
    asyncio.run(run_tests())
