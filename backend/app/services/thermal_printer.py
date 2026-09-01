"""
ESC/POS Thermal Receipt Printer Support
For 58mm and 80mm thermal printers (common in Indian retail)
"""

import socket
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EscPosReceiptPrinter:
    """ESC/POS commands for thermal receipt printers"""
    
    # ESC/POS Commands
    ESC = b"\x1b"
    GS = b"\x1d"
    INIT = ESC + b"@"  # Initialize printer
    RESET = ESC + b"c"  # Reset
    
    # Text formatting
    BOLD_ON = ESC + b"E\x01"
    BOLD_OFF = ESC + b"E\x00"
    DOUBLE_HEIGHT = ESC + b"d\x01"
    DOUBLE_WIDTH = ESC + b"w\x01"
    RESET_FORMAT = ESC + b"!\x00"
    
    # Alignment
    ALIGN_LEFT = ESC + b"a\x00"
    ALIGN_CENTER = ESC + b"a\x01"
    ALIGN_RIGHT = ESC + b"a\x02"
    
    # Paper
    CUT_PAPER = GS + b"V\x00"  # Full cut
    
    @staticmethod
    def FEED_LINES(n):
        """Generate ESC/POS feed lines command"""
        return b"\x1b" + b"d" + bytes([n])
    
    def __init__(self, host: str = "localhost", port: int = 9100, paper_width: int = 58):
        """
        Initialize printer connection
        
        Args:
            host: Printer IP/hostname
            port: Printer port (default 9100 for network printers)
            paper_width: 58 for 58mm, 80 for 80mm
        """
        self.host = host
        self.port = port
        self.paper_width = paper_width
        self.chars_per_line = 32 if paper_width == 58 else 48
        self.socket = None
    
    def connect(self):
        """Connect to thermal printer"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self._send(self.INIT)  # Initialize printer
            logger.info(f"Connected to printer at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to printer: {e}")
            raise
    
    def disconnect(self):
        """Close printer connection"""
        if self.socket:
            self.socket.close()
            logger.info("Printer disconnected")
    
    def _send(self, data: bytes):
        """Send bytes to printer"""
        if not self.socket:
            raise RuntimeError("Not connected to printer")
        self.socket.send(data)
    
    def _send_text(self, text: str):
        """Send text to printer (with UTF-8 encoding)"""
        self._send(text.encode('utf-8'))
    
    def print_receipt(self, receipt_data: dict) -> bool:
        """
        Print complete receipt
        
        Args:
            receipt_data: {
                sale_id, transaction_id, timestamp,
                store_name, cashier_name,
                items: [{name, qty, price, line_total}, ...],
                subtotal, discount, gst, total,
                payment_method, customer_name (optional)
            }
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.connect()
            
            # Header
            self._print_header(receipt_data)
            
            # Items
            self._print_items(receipt_data["items"])
            
            # Totals
            self._print_totals(receipt_data)
            
            # Footer
            self._print_footer(receipt_data)
            
            # Cut paper
            self._send(self.CUT_PAPER)
            self._send(self.FEED_LINES(5))
            
            self.disconnect()
            logger.info(f"Receipt {receipt_data['transaction_id']} printed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to print receipt: {e}")
            return False
    
    def _print_header(self, receipt: dict):
        """Print receipt header"""
        self._send(self.RESET_FORMAT)
        self._send(self.ALIGN_CENTER)
        
        # Store name
        self._send(self.BOLD_ON)
        self._send(self.DOUBLE_HEIGHT)
        self._send(self.DOUBLE_WIDTH)
        self._print_centered(receipt.get("store_name", "PETPOOJA"))
        self._send(self.RESET_FORMAT)
        
        # Divider
        self._send(self.ALIGN_CENTER)
        self._print_centered("=" * self.chars_per_line)
        
        # Receipt number and date
        self._send(self.ALIGN_CENTER)
        self._print_centered(f"Receipt: {receipt.get('transaction_id', 'N/A')}")
        timestamp = receipt.get("timestamp", datetime.now().isoformat())
        self._print_centered(timestamp[:19])  # YYYY-MM-DD HH:MM:SS
        
        # Cashier
        if receipt.get("cashier_name"):
            self._print_centered(f"Cashier: {receipt['cashier_name']}")
        
        # Customer
        if receipt.get("customer_name"):
            self._print_centered(f"Customer: {receipt['customer_name']}")
        
        self._send(self.ALIGN_CENTER)
        self._print_centered("=" * self.chars_per_line)
        self._send(self.FEED_LINES(1))
    
    def _print_items(self, items: List[dict]):
        """Print itemized list"""
        self._send(self.ALIGN_LEFT)
        self._send(self.RESET_FORMAT)
        
        # Header
        self._send(self.BOLD_ON)
        header = f"{'Item':<16} {'Qty':>4} {'Price':>8} {'Total':>6}"
        self._print_left(header[:self.chars_per_line])
        self._send(self.RESET_FORMAT)
        
        self._print_left("-" * self.chars_per_line)
        
        # Items
        for item in items:
            name = item["name"][:14]
            qty = item.get("quantity", 1)
            price = item.get("unit_price", 0)
            total = item.get("line_total", 0)
            
            # Line 1: Name
            self._print_left(f"{name:<32}")
            
            # Line 2: Qty, Price, Total
            qty_str = f"{qty}"
            price_str = f"₹{price:>7.2f}"
            total_str = f"₹{total:>6.2f}"
            
            line = f"{qty_str:>4} {price_str:>10} {total_str:>8}"
            self._print_left(line)
            self._send(self.FEED_LINES(1))
        
        self._print_left("-" * self.chars_per_line)
        self._send(self.FEED_LINES(1))
    
    def _print_totals(self, receipt: dict):
        """Print price breakdown"""
        self._send(self.ALIGN_RIGHT)
        
        # Subtotal
        subtotal = receipt.get("subtotal", 0)
        self._print_right(f"Subtotal:  ₹{subtotal:>10.2f}")
        
        # Discount
        discount = receipt.get("discount", 0)
        if discount > 0:
            self._print_right(f"Discount:  -₹{discount:>9.2f}")
        
        # Tax/GST
        gst = receipt.get("gst", 0)
        self._print_right(f"GST (5%):  ₹{gst:>10.2f}")
        
        # Total (emphasized)
        self._send(self.BOLD_ON)
        self._send(self.DOUBLE_HEIGHT)
        total = receipt.get("total", 0)
        self._print_right(f"TOTAL:     ₹{total:>10.2f}")
        self._send(self.RESET_FORMAT)
        
        # Payment method
        payment = receipt.get("payment_method", "CASH")
        self._send(self.ALIGN_CENTER)
        self._print_centered(f"Payment: {payment.upper()}")
        
        self._send(self.FEED_LINES(2))
    
    def _print_footer(self, receipt: dict):
        """Print receipt footer with QR code or message"""
        self._send(self.ALIGN_CENTER)
        
        # Thank you message
        self._send(self.BOLD_ON)
        self._print_centered("Thank You!")
        self._send(self.RESET_FORMAT)
        
        self._print_centered("Please visit us again")
        self._print_centered(f"Invoice #: {receipt.get('sale_id', 'N/A')}")
        
        # GST info
        self._print_centered("GST: 18AABCT1234H1Z5")
        
        self._send(self.FEED_LINES(3))
    
    def _print_centered(self, text: str):
        """Print centered text"""
        padding = max(0, (self.chars_per_line - len(text)) // 2)
        self._send(self.ALIGN_CENTER)
        self._send_text(text)
        self._send(b"\n")
    
    def _print_left(self, text: str):
        """Print left-aligned text"""
        self._send(self.ALIGN_LEFT)
        self._send_text(text[:self.chars_per_line])
        self._send(b"\n")
    
    def _print_right(self, text: str):
        """Print right-aligned text"""
        self._send(self.ALIGN_RIGHT)
        self._send_text(text)
        self._send(b"\n")
    
    def test_print(self):
        """Print test page (for printer setup)"""
        try:
            self.connect()
            
            self._send(self.RESET_FORMAT)
            self._send(self.ALIGN_CENTER)
            self._send(self.BOLD_ON)
            self._print_centered("ESC/POS Printer Test")
            self._send(self.RESET_FORMAT)
            
            self._print_centered("=" * self.chars_per_line)
            self._print_centered(f"Paper Width: {self.paper_width}mm")
            self._print_centered(f"Characters per line: {self.chars_per_line}")
            self._print_centered(f"Status: OK")
            self._print_centered("=" * self.chars_per_line)
            
            self._send(self.CUT_PAPER)
            self._send(self.FEED_LINES(5))
            
            self.disconnect()
            logger.info("Test print completed")
            return True
        
        except Exception as e:
            logger.error(f"Test print failed: {e}")
            return False


class MockReceiptPrinter(EscPosReceiptPrinter):
    """Mock printer for testing (outputs to log instead of device)"""
    
    def __init__(self, paper_width: int = 58):
        super().__init__(paper_width=paper_width)
        self.output = []
    
    def connect(self):
        self.output = []
        logger.info("Mock printer connected")
    
    def disconnect(self):
        logger.info("Mock printer disconnected")
        # Print captured output
        print("\n" + "="*self.chars_per_line)
        print("MOCK RECEIPT OUTPUT:")
        print("="*self.chars_per_line)
        for line in self.output:
            print(line)
        print("="*self.chars_per_line + "\n")
    
    def _send(self, data: bytes):
        pass  # No-op
    
    def _send_text(self, text: str):
        self.output.append(text)
    
    def _print_centered(self, text: str):
        padding = max(0, (self.chars_per_line - len(text)) // 2)
        self.output.append(" " * padding + text)
    
    def _print_left(self, text: str):
        self.output.append(text[:self.chars_per_line])
    
    def _print_right(self, text: str):
        padding = max(0, self.chars_per_line - len(text))
        self.output.append(" " * padding + text)
