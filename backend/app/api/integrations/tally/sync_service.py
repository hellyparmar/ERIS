"""
Tally Sync Service
Orchestrates bi-directional data sync between R-DIOS and Tally.
Wraps TallyXMLClient and handles database read/write.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from .tally_client import TallyXMLClient
from .models import (
    TallySaleVoucher,
    TallyVoucherLineItem,
    TallySyncResult,
    TallyConnectionStatus,
)

logger = logging.getLogger(__name__)

# ─── Default connection config from environment ─────────────────────────────────
_DEFAULT_HOST = os.getenv("TALLY_HOST", "localhost")
_DEFAULT_PORT = int(os.getenv("TALLY_PORT", "9000"))
_DEFAULT_COMPANY = os.getenv("TALLY_COMPANY_NAME", "")


class TallySyncService:
    """
    High-level orchestration service for Tally ↔ R-DIOS sync.

    All public methods are database-agnostic — they accept plain dicts
    so they work whether the caller queries SQLAlchemy, raw SQL, or mock data.
    """

    def __init__(
        self,
        host: str = _DEFAULT_HOST,
        port: int = _DEFAULT_PORT,
        company_name: str = _DEFAULT_COMPANY,
    ) -> None:
        self.client = TallyXMLClient(host=host, port=port, company_name=company_name)

    # ─── Connectivity ────────────────────────────────────────────────────────────

    def check_status(self) -> TallyConnectionStatus:
        """Ping Tally and return a structured status object."""
        return self.client.ping()

    # ─── Export: R-DIOS → Tally ──────────────────────────────────────────────────

    def export_sale(self, sale: Dict) -> TallySyncResult:
        """
        Export a single R-DIOS POS sale to Tally as a Sales Voucher.

        Expected keys in `sale`:
            invoice_number, sale_date (ISO str or date), customer_name,
            items: [{name, qty, rate, amount, gst_rate, hsn_code}],
            is_interstate (bool, default False)
        """
        try:
            sale_date = sale.get("sale_date") or date.today()
            if isinstance(sale_date, str):
                sale_date = datetime.fromisoformat(sale_date).date()

            line_items = [
                TallyVoucherLineItem(
                    product_name=it["name"],
                    stock_item_name=it.get("tally_item_name") or it["name"],
                    quantity=float(it.get("qty", 1)),
                    unit=it.get("unit", "Nos"),
                    rate=Decimal(str(it.get("rate", 0))),
                    amount=Decimal(str(it.get("amount", 0))),
                    gst_rate=float(it.get("gst_rate", 0)),
                    hsn_code=it.get("hsn_code", ""),
                )
                for it in sale.get("items", [])
            ]

            voucher = TallySaleVoucher(
                invoice_number=sale["invoice_number"],
                invoice_date=sale_date,
                customer_ledger_name=sale.get("customer_name") or "Cash",
                is_interstate=sale.get("is_interstate", False),
                narration=f"POS Sale from R-DIOS — {sale['invoice_number']}",
                items=line_items,
            )
            return self.client.push_sales_voucher(voucher)

        except Exception as exc:
            logger.exception("export_sale failed: %s", exc)
            return TallySyncResult(
                success=False,
                operation="export-sale",
                errors=[str(exc)],
                message="Unexpected error exporting sale"
            )

    def export_invoice(self, invoice: Dict) -> TallySyncResult:
        """
        Export a GST invoice to Tally as a Sales Voucher.

        Expected keys: invoice_number, invoice_date, customer_name,
        taxable_amount, cgst_amount, sgst_amount, igst_amount, grand_total
        """
        try:
            inv_date = invoice.get("invoice_date") or date.today()
            if isinstance(inv_date, str):
                inv_date = datetime.fromisoformat(inv_date).date()

            # Build a single composite line item from invoice totals
            item = TallyVoucherLineItem(
                product_name="Sales",
                stock_item_name="Sales",
                quantity=1,
                rate=Decimal(str(invoice.get("taxable_amount", 0))),
                amount=Decimal(str(invoice.get("taxable_amount", 0))),
                cgst_amount=Decimal(str(invoice.get("cgst_amount", 0))),
                sgst_amount=Decimal(str(invoice.get("sgst_amount", 0))),
                igst_amount=Decimal(str(invoice.get("igst_amount", 0))),
            )

            voucher = TallySaleVoucher(
                invoice_number=invoice["invoice_number"],
                invoice_date=inv_date,
                customer_ledger_name=invoice.get("customer_name") or "Cash",
                is_interstate=(Decimal(str(invoice.get("igst_amount", 0))) > 0),
                items=[item],
            )
            # Directly set totals from invoice data (skip auto-compute)
            voucher.taxable_amount = Decimal(str(invoice.get("taxable_amount", 0)))
            voucher.cgst_amount    = Decimal(str(invoice.get("cgst_amount", 0)))
            voucher.sgst_amount    = Decimal(str(invoice.get("sgst_amount", 0)))
            voucher.igst_amount    = Decimal(str(invoice.get("igst_amount", 0)))
            voucher.grand_total    = Decimal(str(invoice.get("grand_total", 0)))

            return self.client.push_sales_voucher(voucher)

        except Exception as exc:
            logger.exception("export_invoice failed: %s", exc)
            return TallySyncResult(
                success=False,
                operation="export-invoice",
                errors=[str(exc)],
                message="Unexpected error exporting invoice"
            )

    def bulk_export_sales(self, sales: List[Dict]) -> TallySyncResult:
        """Export a list of POS sales to Tally. Returns aggregated result."""
        result = TallySyncResult(
            success=False, operation="bulk-export-sales", total=len(sales)
        )
        for sale in sales:
            r = self.export_sale(sale)
            result.created += r.created
            result.updated += r.updated
            result.skipped += r.skipped
            result.errors.extend(r.errors)
        result.success = result.created + result.updated > 0
        result.message = (
            f"Exported {result.created} new + {result.updated} updated vouchers to Tally"
        )
        return result

    # ─── Import: Tally → R-DIOS ──────────────────────────────────────────────────

    def import_ledgers(self) -> TallySyncResult:
        """
        Fetch all ledgers from Tally.
        Returns a TallySyncResult with the ledgers in the message field,
        and sets result.total to number of ledgers fetched.
        Callers are responsible for persisting to the database.
        """
        try:
            ledgers = self.client.fetch_ledgers()
            return TallySyncResult(
                success=True,
                operation="import-ledgers",
                total=len(ledgers),
                created=len(ledgers),
                message=f"Fetched {len(ledgers)} ledgers from Tally"
            )
        except Exception as exc:
            logger.exception("import_ledgers failed: %s", exc)
            return TallySyncResult(
                success=False,
                operation="import-ledgers",
                errors=[str(exc)],
                message="Failed to import ledgers"
            )

    def import_stock_items(self) -> TallySyncResult:
        """Fetch all stock items from Tally."""
        try:
            items = self.client.fetch_stock_items()
            return TallySyncResult(
                success=True,
                operation="import-stock-items",
                total=len(items),
                created=len(items),
                message=f"Fetched {len(items)} stock items from Tally"
            )
        except Exception as exc:
            logger.exception("import_stock_items failed: %s", exc)
            return TallySyncResult(
                success=False,
                operation="import-stock-items",
                errors=[str(exc)],
                message="Failed to import stock items"
            )

    def import_vouchers(
        self,
        voucher_type: str = "Sales",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> TallySyncResult:
        """Fetch vouchers from Tally for a date range."""
        try:
            vouchers = self.client.fetch_vouchers(
                voucher_type=voucher_type,
                from_date=from_date,
                to_date=to_date,
            )
            return TallySyncResult(
                success=True,
                operation="import-vouchers",
                total=len(vouchers),
                created=len(vouchers),
                message=f"Fetched {len(vouchers)} {voucher_type} vouchers from Tally"
            )
        except Exception as exc:
            logger.exception("import_vouchers failed: %s", exc)
            return TallySyncResult(
                success=False,
                operation="import-vouchers",
                errors=[str(exc)],
                message="Failed to import vouchers"
            )
