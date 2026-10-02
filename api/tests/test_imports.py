"""Import v2: inspection and column mapping, file checks, job history, error reports, samples, traceability."""
import json
from datetime import date, timedelta

from app.db import SessionLocal
from app.models import AuditLog, Sale


def test_inspect_suggests_mapping_from_pos_headers(client, admin):
    day = (date.today() - timedelta(days=1)).isoformat()
    csv = f"Bill No,Bill Date,Store,Item Code,Qty,Mode\nPOS-77,{day},MUM-AND,DAI-001,2,upi\n"
    r = client.post("/api/imports/sales/inspect", headers=admin, files={"file": ("pos.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    m = r.json()["mapping"]
    assert m["invoice_no"] == "Bill No" and m["date"] == "Bill Date" and m["outlet_code"] == "Store"
    assert m["sku"] == "Item Code" and m["quantity"] == "Qty" and m["payment_method"] == "Mode"
    assert r.json()["missing_required"] == [] and r.json()["sample"][0]["qty"] == "2"

    # the confirmed mapping is applied to the upload; the committed bill is traceable to its import job
    r = client.post("/api/imports/sales?dry_run=false", headers=admin, data={"mapping": json.dumps(m)},
                    files={"file": ("pos.csv", csv, "text/csv")})
    res = r.json()
    assert res["committed"] and res["created"] == 1, res
    with SessionLocal() as db:
        sale = db.query(Sale).filter_by(invoice_no="POS-77").one()
        assert sale.import_id == res["job_id"] and sale.source == "import"
        entries = db.query(AuditLog).filter_by(entity="import", entity_id=str(res["job_id"])).all()
        assert len(entries) == 1 and db.query(AuditLog).filter_by(entity="sale", entity_id=str(sale.id)).count() == 0


def test_rejects_non_csv_files(client, admin):
    r = client.post("/api/imports/sales", headers=admin,
                    files={"file": ("book.xlsx", b"PK\x03\x04binary", "application/octet-stream")})
    assert r.status_code == 400 and "CSV" in r.json()["detail"]
    r = client.post("/api/imports/sales", headers=admin, files={"file": ("x.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 400
    r = client.post("/api/imports/sales", headers=admin, data={"mapping": "not json"},
                    files={"file": ("s.csv", "date,outlet_code,sku,quantity\n", "text/csv")})
    assert r.status_code == 422


def test_sample_with_errors_history_and_error_report(client, admin, manager):
    good = client.get("/api/imports/samples/sales", headers=admin)
    assert good.status_code == 200
    res = client.post("/api/imports/sales", headers=admin, files={"file": ("ok.csv", good.text, "text/csv")}).json()
    assert res["error_count"] == 0 and res["created"] == 6

    bad = client.get("/api/imports/samples/sales?with_errors=true", headers=admin).text
    res = client.post("/api/imports/sales", headers=admin, files={"file": ("bad.csv", bad, "text/csv")}).json()
    assert res["error_count"] == 5 and res["created"] == 6 and not res["committed"]

    hist = client.get("/api/imports/history", headers=admin).json()["items"]
    job = next(j for j in hist if j["id"] == res["job_id"])
    assert job["status"] == "rejected" and job["dry_run"] and job["errors"] == 5
    report = client.get(f"/api/imports/history/{res['job_id']}/errors.csv", headers=admin)
    assert report.status_code == 200 and report.text.count("\n") == 6 and "NO-SUCH-SKU" in report.text
    # managers only see their own imports
    assert client.get(f"/api/imports/history/{res['job_id']}/errors.csv", headers=manager).status_code == 403
    assert all(j["id"] != res["job_id"] for j in client.get("/api/imports/history", headers=manager).json()["items"])


def test_import_edge_cases(client, admin):
    y = (date.today() - timedelta(days=1)).isoformat()

    def check(name, content):
        return client.post("/api/imports/sales", headers=admin, files={"file": (name, content, "text/csv")}).json()

    head = "date,outlet_code,sku,quantity\n"
    assert check("u16.csv", (head + f"{y},MUM-AND,DAI-001,1\n").encode("utf-16"))["error_count"] == 0
    assert "not a number" in check("nan.csv", head + f"{y},MUM-AND,DAI-001,nan\n")["errors"][0]["message"]
    assert "too large" in check("big.csv", head + f"{y},MUM-AND,DAI-001,1e9\n")["errors"][0]["message"]
    assert "before Andheri West opened" in check("old.csv", head + "1990-01-01,MUM-AND,DAI-001,1\n")["errors"][0]["message"]


def test_exports_neutralise_spreadsheet_formulas(client, admin):
    r = client.post("/api/customers", headers=admin, json={"name": "=HYPERLINK(\"http://x\")", "phone": "9811155555"})
    assert r.status_code == 201
    text = client.get("/api/customers/export", headers=admin).text
    assert "'=HYPERLINK" in text and "\n=HYPERLINK" not in text
