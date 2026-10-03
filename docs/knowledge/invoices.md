# Demo GST invoices

## What they are (is the GSTIN real?)
ERIS can issue a printable GST-style tax invoice for any completed sale. These invoices are for demonstration only: the company GSTIN is synthetic, the invoice is not registered on the Invoice Registration Portal (there is no IRN or QR code) and every PDF carries the watermark "DEMO - NOT FOR TAX FILING".

## Tax rules applied
GST registration is per state, so each outlet uses the company PAN with its own state code as its GSTIN. The place of supply is the buyer's GSTIN state when the buyer gives a GSTIN, otherwise the customer's state, otherwise the outlet's state for a counter sale. When the place of supply is in the outlet's state the tax is split equally into CGST and SGST; otherwise the full amount is IGST. Each line shows the product's HSN code and GST rate.

## Numbering and history
Invoice numbers have the form outlet code / financial year / sequence, for example MUMAND/2627/0001, and run consecutively per outlet and financial year (16 characters, the GST limit). An invoice is created once per sale; asking again returns the same invoice. All issued invoices are listed in the invoice history, and an invoice for a sale that was later voided is shown as cancelled.
