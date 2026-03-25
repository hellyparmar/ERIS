import csv
import os
import json
from typing import List, Dict, Any
from datetime import datetime
from app.api.db.database import SessionLocal
from sqlalchemy import text

class TallyExportService:
    """Handles data transformation for Tally manual import (CSV/Excel)"""

    def __init__(self, export_dir: str = "exports/tally"):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)

    def export_sales_to_csv(self, start_date: str, end_date: str) -> str:
        """Export sales in a Tally-compatible CSV format"""
        db = SessionLocal()
        query = text("""
            SELECT s.order_id, s.created_at, s.total_amount, c.name as customer_name
            FROM sales s
            JOIN customers c ON s.customer_id = c.id
            WHERE s.created_at BETWEEN :start AND :end
        """)
        
        try:
            results = db.execute(query, {"start": start_date, "end": end_date}).fetchall()
            filename = f"tally_sales_{datetime.now().strftime('%Y%host_%H%M%S')}.csv"
            filepath = os.path.join(self.export_dir, filename)

            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Tally-friendly headers (simplified)
                writer.writerow(['Date', 'Particulars', 'Voucher Type', 'Voucher No', 'Amount'])
                for row in results:
                    writer.writerow([
                        row.created_at.strftime('%Y-%m-%d'),
                        row.customer_name,
                        'Sales',
                        row.order_id,
                        row.total_amount
                    ])
            
            return filepath
        finally:
            db.close()

    def export_products_to_csv(self) -> str:
        """Export product master for Tally import"""
        # Similar logic for products could be implemented here
        filepath = os.path.join(self.export_dir, "product_master_placeholder.csv")
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                f.write("Placeholder Product CSV")
        return filepath

# Singleton Instance
tally_export_service = TallyExportService()
