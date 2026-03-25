"""
Tally XML Client
Low-level HTTP/XML communication with Tally Prime / Tally ERP 9.

Tally exposes a built-in HTTP server on port 9000 (ODBC/XML mode).
All data exchange uses Tally's proprietary XML envelope format.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

import requests

from .models import (
    TallyConnectionStatus,
    TallyLedger,
    TallyStockItem,
    TallySaleVoucher,
    TallyVoucher,
    TallySyncResult,
)

logger = logging.getLogger(__name__)


class TallyXMLClient:
    """
    Low-level XML client for Tally ERP.

    Usage:
        client = TallyXMLClient(host="localhost", port=9000)
        status = client.ping()
        ledgers = client.fetch_ledgers()
        client.push_sales_voucher(voucher)
    """

    DEFAULT_TIMEOUT = 30          # seconds
    DATE_FMT = "%Y%m%d"           # Tally date format

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        company_name: str = "",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.company_name = company_name
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"

    # ─── Connectivity ───────────────────────────────────────────────────────────

    def ping(self) -> TallyConnectionStatus:
        """Test Tally connectivity and retrieve company info."""
        try:
            xml = self._build_export_xml("CompanyCollection", [
                "NAME", "GUID", "CURRENCY"
            ])
            resp = self._post(xml)
            if resp is None:
                return TallyConnectionStatus(
                    connected=False, host=self.host, port=self.port,
                    error="No response from Tally"
                )
            root = ET.fromstring(resp)
            company = root.find(".//COMPANY")
            if company is not None:
                name = company.findtext("NAME", "")
                guid = company.findtext("GUID", "")
                if not self.company_name:
                    self.company_name = name
                return TallyConnectionStatus(
                    connected=True, host=self.host, port=self.port,
                    company_name=name, company_guid=guid
                )
            return TallyConnectionStatus(
                connected=True, host=self.host, port=self.port
            )
        except Exception as exc:
            return TallyConnectionStatus(
                connected=False, host=self.host, port=self.port,
                error=str(exc)
            )

    # ─── Import from Tally ──────────────────────────────────────────────────────

    def fetch_ledgers(self) -> List[TallyLedger]:
        """Fetch all ledgers from Tally."""
        xml = self._build_export_xml(
            "Ledger",
            ["NAME", "GUID", "PARENT", "PARTYGSTIN",
             "GSTREGISTRATIONTYPE", "OPENINGBALANCE"]
        )
        resp = self._post(xml)
        if not resp:
            return []

        ledgers: List[TallyLedger] = []
        try:
            root = ET.fromstring(resp)
            for elem in root.findall(".//LEDGER"):
                ledger = TallyLedger(
                    name=elem.findtext("NAME", ""),
                    guid=elem.findtext("GUID", ""),
                    group=elem.findtext("PARENT", ""),
                    gstin=elem.findtext("PARTYGSTIN", ""),
                    gst_registration_type=elem.findtext("GSTREGISTRATIONTYPE", ""),
                    opening_balance=float(elem.findtext("OPENINGBALANCE", "0") or 0),
                )
                ledger.classify()
                ledgers.append(ledger)
        except ET.ParseError as exc:
            logger.error("Failed to parse ledger XML: %s", exc)

        logger.info("Fetched %d ledgers from Tally", len(ledgers))
        return ledgers

    def fetch_stock_items(self) -> List[TallyStockItem]:
        """Fetch all stock items from Tally."""
        xml = self._build_export_xml(
            "Stock Item",
            ["NAME", "GUID", "PARENT", "BASEUNITS",
             "HSNCODE", "GSTAPPLICABLE", "GSTRATE"]
        )
        resp = self._post(xml)
        if not resp:
            return []

        items: List[TallyStockItem] = []
        try:
            root = ET.fromstring(resp)
            for elem in root.findall(".//STOCKITEM"):
                item = TallyStockItem(
                    name=elem.findtext("NAME", ""),
                    guid=elem.findtext("GUID", ""),
                    category=elem.findtext("PARENT", ""),
                    unit=elem.findtext("BASEUNITS", "Nos"),
                    hsn_code=elem.findtext("HSNCODE", ""),
                    gst_applicable=elem.findtext("GSTAPPLICABLE", "No") == "Yes",
                    gst_rate=float(elem.findtext("GSTRATE", "0") or 0),
                )
                items.append(item)
        except ET.ParseError as exc:
            logger.error("Failed to parse stock items XML: %s", exc)

        logger.info("Fetched %d stock items from Tally", len(items))
        return items

    def fetch_vouchers(
        self,
        voucher_type: str = "Sales",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[TallyVoucher]:
        """Fetch vouchers from Tally with optional date range."""
        date_filter = ""
        if from_date and to_date:
            date_filter = f"""
                <SVFROMDATE>{from_date.strftime(self.DATE_FMT)}</SVFROMDATE>
                <SVTODATE>{to_date.strftime(self.DATE_FMT)}</SVTODATE>"""

        xml = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>Vouchers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVVOUCHERTYPE>{voucher_type}</SVVOUCHERTYPE>
        {date_filter}
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="VouchersCollection">
            <TYPE>Voucher</TYPE>
            <FETCH>DATE,VOUCHERNUMBER,VOUCHERTYPENAME,PARTYLEDGERNAME,AMOUNT,NARRATION,GUID</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""

        resp = self._post(xml)
        if not resp:
            return []

        vouchers: List[TallyVoucher] = []
        try:
            root = ET.fromstring(resp)
            for elem in root.findall(".//VOUCHER"):
                raw_date = elem.findtext("DATE") or ""
                try:
                    v_date = date(int(raw_date[0:4]), int(raw_date[4:6]), int(raw_date[6:8]))
                except (ValueError, TypeError, IndexError):
                    v_date = date.today()
                vouchers.append(TallyVoucher(
                    voucher_number=elem.findtext("VOUCHERNUMBER", ""),
                    voucher_type=elem.findtext("VOUCHERTYPENAME", voucher_type),
                    date=v_date,
                    party_ledger=elem.findtext("PARTYLEDGERNAME", ""),
                    amount=float(elem.findtext("AMOUNT", "0") or 0),
                    narration=elem.findtext("NARRATION", ""),
                    guid=elem.findtext("GUID", ""),
                ))
        except ET.ParseError as exc:
            logger.error("Failed to parse vouchers XML: %s", exc)

        logger.info("Fetched %d vouchers from Tally", len(vouchers))
        return vouchers

    # ─── Export to Tally ────────────────────────────────────────────────────────

    def push_sales_voucher(self, voucher: TallySaleVoucher) -> TallySyncResult:
        """
        Push a single R-DIOS sales invoice to Tally as a Sales Voucher.
        Builds a proper GST-compliant XML envelope.
        """
        # Ensure tax totals are computed
        voucher.compute_totals()
        xml = self._build_sales_voucher_xml(voucher)
        resp = self._post(xml)

        if resp is None:
            return TallySyncResult(
                success=False,
                operation="push-sales-voucher",
                errors=["No response from Tally"],
                message="Failed to reach Tally"
            )

        # Parse Tally response
        try:
            root = ET.fromstring(resp)
            created = root.findtext(".//CREATED", "0")
            altered = root.findtext(".//ALTERED", "0")
            errors_raw = root.findall(".//LINEERROR")
            error_msgs = [e.text or "" for e in errors_raw if e.text]

            ok = int(created or 0) > 0 or int(altered or 0) > 0
            return TallySyncResult(
                success=ok,
                operation="push-sales-voucher",
                total=1,
                created=int(created or 0),
                updated=int(altered or 0),
                errors=error_msgs,
                message=(
                    f"Voucher {voucher.invoice_number} exported to Tally"
                    if ok else
                    f"Tally rejected voucher: {'; '.join(error_msgs)}"
                )
            )
        except ET.ParseError:
            return TallySyncResult(
                success=False,
                operation="push-sales-voucher",
                errors=["Unparseable Tally response"],
                message="Could not parse Tally reply"
            )

    # ─── Internal helpers ───────────────────────────────────────────────────────

    def _post(self, xml_body: str) -> Optional[str]:
        """Send XML to Tally and return raw response text."""
        try:
            response = requests.post(
                self.base_url,
                data=xml_body.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.text
            logger.error("Tally HTTP error %s", response.status_code)
            return None
        except requests.ConnectionError:
            logger.error("Cannot connect to Tally at %s (is it running?)", self.base_url)
            return None
        except requests.Timeout:
            logger.error("Tally request timed out (%ss)", self.timeout)
            return None
        except Exception as exc:
            logger.exception("Unexpected Tally request error: %s", exc)
            return None

    def _build_export_xml(self, collection_type: str, fields: List[str]) -> str:
        """Build a generic Tally export XML request."""
        fetch_str = ", ".join(fields)
        return f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>{collection_type}</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="{collection_type}Collection">
            <TYPE>{collection_type}</TYPE>
            <FETCH>{fetch_str}</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""

    def _build_sales_voucher_xml(self, voucher: TallySaleVoucher) -> str:
        """Build Tally XML for a GST sales voucher."""
        root = ET.Element("ENVELOPE")

        # Header
        hdr = ET.SubElement(root, "HEADER")
        ET.SubElement(hdr, "VERSION").text = "1"
        ET.SubElement(hdr, "TALLYREQUEST").text = "Import"
        ET.SubElement(hdr, "TYPE").text = "Data"
        ET.SubElement(hdr, "ID").text = "Vouchers"

        # Body
        body = ET.SubElement(root, "BODY")
        desc = ET.SubElement(body, "DESC")
        sv = ET.SubElement(desc, "STATICVARIABLES")
        ET.SubElement(sv, "SVCURRENTCOMPANY").text = self.company_name or "Default"

        # TallyMessage with voucher
        msg = ET.SubElement(desc, "TALLYMESSAGE")
        msg.set("xmlns:UDF", "TallyUDF")
        vchr = ET.SubElement(msg, "VOUCHER")
        vchr.set("VCHTYPE", "Sales")
        vchr.set("ACTION", "Create")
        vchr.set("OBJVIEW", "Invoice Voucher View")

        ET.SubElement(vchr, "DATE").text = voucher.invoice_date.strftime(self.DATE_FMT)
        ET.SubElement(vchr, "EFFECTIVEDATE").text = voucher.invoice_date.strftime(self.DATE_FMT)
        ET.SubElement(vchr, "VOUCHERTYPENAME").text = "Sales"
        ET.SubElement(vchr, "VOUCHERNUMBER").text = voucher.invoice_number
        ET.SubElement(vchr, "PARTYLEDGERNAME").text = voucher.customer_ledger_name
        ET.SubElement(vchr, "PERSISTEDVIEW").text = "Invoice Voucher View"
        ET.SubElement(vchr, "NARRATION").text = (
            voucher.narration or f"Synced from R-DIOS: {voucher.invoice_number}"
        )
        ET.SubElement(vchr, "ISGSTVOUCH").text = "Yes"

        # ── Ledger entries (party debit, sales/tax credits) ──────────────────
        def add_ledger(parent, name: str, deemed_positive: str, amount: Decimal):
            entry = ET.SubElement(parent, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(entry, "LEDGERNAME").text = name
            ET.SubElement(entry, "ISDEEMEDPOSITIVE").text = deemed_positive
            ET.SubElement(entry, "AMOUNT").text = str(amount)

        # Party ledger — debit (positive in Tally)
        add_ledger(vchr, voucher.customer_ledger_name, "Yes", voucher.grand_total or Decimal("0"))

        # Sales ledger — credit (negative)
        add_ledger(vchr, "Sales", "No", -(voucher.taxable_amount or Decimal("0")))

        # GST ledgers
        if voucher.cgst_amount and voucher.cgst_amount > 0:
            add_ledger(vchr, "CGST", "No", -voucher.cgst_amount)
        if voucher.sgst_amount and voucher.sgst_amount > 0:
            add_ledger(vchr, "SGST", "No", -voucher.sgst_amount)
        if voucher.igst_amount and voucher.igst_amount > 0:
            add_ledger(vchr, "IGST", "No", -voucher.igst_amount)

        # ── Inventory entries ────────────────────────────────────────────────
        for item in voucher.items:
            inv = ET.SubElement(vchr, "ALLINVENTORYENTRIES.LIST")
            ET.SubElement(inv, "STOCKITEMNAME").text = item.stock_item_name
            ET.SubElement(inv, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(inv, "RATE").text = f"{item.rate}/{item.unit}"
            ET.SubElement(inv, "AMOUNT").text = str(item.amount)
            ET.SubElement(inv, "ACTUALQTY").text = f"{item.quantity} {item.unit}"
            ET.SubElement(inv, "BILLEDQTY").text = f"{item.quantity} {item.unit}"
            if item.hsn_code:
                ET.SubElement(inv, "HSNCODE").text = item.hsn_code

            # Accounting allocation per line item
            acct = ET.SubElement(inv, "ACCOUNTINGALLOCATIONS.LIST")
            ET.SubElement(acct, "LEDGERNAME").text = "Sales"
            ET.SubElement(acct, "ISDEEMEDPOSITIVE").text = "No"
            ET.SubElement(acct, "AMOUNT").text = str(item.amount)

        return ET.tostring(root, encoding="unicode")
