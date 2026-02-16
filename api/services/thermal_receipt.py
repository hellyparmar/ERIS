"""
Thermal Receipt Generation Service
Generates ESC/POS commands for 58mm thermal printers
Per CLAUDE.md Part 2.2
"""
from datetime import datetime
from decimal import Decimal

class ThermalReceipt:
    """Generate ESC/POS commands for 58mm thermal printer"""
    
    # ESC/POS Commands
    ESC = b'\x1b'
    GS = b'\x1d'
    INIT = ESC + b'@'  # Initialize printer
    ALIGN_CENTER = ESC + b'a\x01'
    ALIGN_LEFT = ESC + b'a\x00'
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    CUT = GS + b'V\x00'  # Full cut
    LINE_FEED = b'\n'
    
    @staticmethod
    def generate(sale_data: dict, store_data: dict) -> bytes:
        """
        Generate complete thermal receipt
        
        Args:
            sale_data: {transaction_id, items, subtotal, tax, total, payment_method}
            store_data: {name, address, gstin, phone}
        
        Returns:
            bytes: ESC/POS commands ready to send to printer
        """
        receipt = ThermalReceipt.INIT
        
        # Header
        receipt += ThermalReceipt.ALIGN_CENTER
        receipt += ThermalReceipt.BOLD_ON
        receipt += store_data['name'].encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += ThermalReceipt.BOLD_OFF
        receipt += store_data.get('address', '').encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += f"GSTIN: {store_data.get('gstin', 'N/A')}".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += f"Ph: {store_data.get('phone', '')}".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += b'-' * 32 + ThermalReceipt.LINE_FEED
        
        # Transaction Info
        receipt += ThermalReceipt.ALIGN_LEFT
        receipt += f"Receipt: {sale_data['receipt_number']}".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += f"Date: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += f"Txn ID: {sale_data['transaction_id']}".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += b'-' * 32 + ThermalReceipt.LINE_FEED
        
        # Items Table Header
        receipt += ThermalReceipt.BOLD_ON
        receipt += "Item         Qty  Price  Total".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += ThermalReceipt.BOLD_OFF
        receipt += b'-' * 32 + ThermalReceipt.LINE_FEED
        
        # Items
        for item in sale_data['items']:
            name = item['name'][:12].ljust(12)  # Truncate to 12 chars
            qty = str(item['quantity']).rjust(3)
            price = f"₹{item['unit_price']:.0f}".rjust(6)
            total = f"₹{item['line_total']:.0f}".rjust(6)
            line = f"{name} {qty} {price} {total}".encode('utf-8') + ThermalReceipt.LINE_FEED
            receipt += line
        
        receipt += b'-' * 32 + ThermalReceipt.LINE_FEED
        
        # Totals
        subtotal = sale_data.get('subtotal', sale_data['total'] - sale_data['tax'])
        receipt += f"Subtotal:        ₹{subtotal:.2f}".rjust(32).encode('utf-8') + ThermalReceipt.LINE_FEED
        
        # GST Breakdown
        tax = sale_data['tax']
        if sale_data.get('is_interstate', False):
            # IGST
            receipt += f"IGST (18%):      ₹{tax:.2f}".rjust(32).encode('utf-8') + ThermalReceipt.LINE_FEED
        else:
            # CGST + SGST
            cgst = tax / 2
            sgst = tax / 2
            receipt += f"CGST (9%):       ₹{cgst:.2f}".rjust(32).encode('utf-8') + ThermalReceipt.LINE_FEED
            receipt += f"SGST (9%):       ₹{sgst:.2f}".rjust(32).encode('utf-8') + ThermalReceipt.LINE_FEED
        
        receipt += ThermalReceipt.BOLD_ON
        receipt += f"TOTAL:           ₹{sale_data['total']:.2f}".rjust(32).encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += ThermalReceipt.BOLD_OFF
        receipt += b'-' * 32 + ThermalReceipt.LINE_FEED
        
        # Payment Method
        receipt += f"Paid via: {sale_data['payment_method']}".encode('utf-8') + ThermalReceipt.LINE_FEED
        receipt += b'-' * 32 + ThermalReceipt.LINE_FEED
        
        # Footer
        receipt += ThermalReceipt.ALIGN_CENTER
        receipt += b"Thank you for shopping!" + ThermalReceipt.LINE_FEED
        receipt += b"Visit again!" + ThermalReceipt.LINE_FEED
        receipt += ThermalReceipt.LINE_FEED * 3
        
        # Cut paper
        receipt += ThermalReceipt.CUT
        
        return receipt
