# Importing data from CSV files

## What can be imported
Sales history (one row per product line, rows that share an invoice number become one bill), products, customers, suppliers and stock counts can be imported from CSV files on the Data Import page. Each type has a downloadable template and sample files, including one with deliberate mistakes that shows what validation catches.

## File requirements
Files must be CSV (comma, semicolon or tab separated), UTF-8 or Windows-1252 encoded, at most 15 MB and 50,000 rows. Excel workbooks must first be saved as CSV. Dates can be YYYY-MM-DD, DD-MM-YYYY or DD/MM/YYYY; times are HH:MM.

## Column mapping
After choosing a file, ERIS reads the header row and suggests which file column feeds each ERIS field. Common point-of-sale names are recognised automatically, for example Bill No for invoice_no, Store for outlet_code, Item Code for sku and Qty for quantity. The mapping can be changed before validation. Required sales fields are date, outlet_code, sku and quantity; outlet and product names are also accepted.

## Validation and dry run
Every import first runs as a dry run: all rows are validated and a preview, a per-row error list and a summary are shown, but nothing is saved. Typical errors are unknown outlets or products, negative quantities, invalid dates, invalid phone numbers and unsupported payment methods. The full error report can be downloaded as a CSV file.

## Duplicates and atomic commit
Bills whose invoice number already exists in ERIS are skipped and reported as warnings, so the same file can be uploaded twice safely; this can be switched off to reject such files instead. A real import is all-or-nothing: if any row has an error, nothing from the file is saved. Imported sales are marked with source "import" and linked to their import job, and do not change stock unless "update stock" is chosen.

## Import history and audit
Every dry run and import is recorded in the import history with the file name, the user, row counts, created and updated records and errors. Each committed import also writes one entry to the audit log.
