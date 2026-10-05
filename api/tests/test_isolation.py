"""Heavy or risky work is kept apart from everything else: model fitting has bounded capacity, and a CSV import
never changes live data unless it is committed in full."""
import threading

from sqlalchemy import func, select

from app.config import settings
from app.db import SessionLocal
from app.models import ImportJob, Sale
from app.services import forecasting as F


def _hold_every_fit_slot():
    held = 0
    while F._fit_slots.acquire(blocking=False):
        held += 1
    return held


def _release(held):
    for _ in range(held):
        F._fit_slots.release()


def test_busy_forecasting_answers_quickly_and_other_pages_keep_working(client, admin, monkeypatch):
    monkeypatch.setattr(settings, "FORECAST_WAIT_SECONDS", 0.2)
    F.clear_cache()
    held = _hold_every_fit_slot()
    try:
        # an uncached fit cannot start: a fast 503 that says to retry, not a request stuck behind the fits
        r = client.get("/api/forecast?scope=category&target_id=2&horizon=21&model=holt_winters", headers=admin)
        assert r.status_code == 503 and r.headers["retry-after"] == "5" and "try again" in r.json()["detail"]
        # pages that do not fit models are unaffected
        assert client.get("/api/analytics/sales?period=30d", headers=admin).status_code == 200
        # the dashboard still answers (without its forecast) and that partial answer is not kept in the cache
        dash = client.get("/api/dashboard?period=14d", headers=admin)
        assert dash.status_code == 200 and dash.json()["forecast"] is None
        assert client.get("/api/dashboard?period=14d", headers=admin).headers.get("x-cache") != "hit"
        # the assistant explains instead of failing
        chat = client.post("/api/assistant/chat", headers=admin, json={"message": "Forecast sales for the next 3 weeks"})
        assert chat.status_code == 200
    finally:
        _release(held)
    r = client.get("/api/forecast?scope=category&target_id=2&horizon=21&model=holt_winters", headers=admin)
    assert r.status_code == 200 and r.json()["forecast"]
    dash = client.get("/api/dashboard?period=14d", headers=admin)
    assert dash.json()["forecast"] is not None


def test_fits_never_exceed_the_configured_capacity(monkeypatch):
    running, peak, lock = 0, 0, threading.Lock()
    real = F.run_forecast

    def counting(*a, **k):
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        try:
            return real(*a, **k)
        finally:
            with lock:
                running -= 1

    monkeypatch.setattr(F, "run_forecast", counting)
    F.clear_cache()

    def work(cat):
        with SessionLocal() as db:
            F.forecast_series(db, F.build_spec(db, "category", cat, None), horizon=17, model="seasonal_naive",
                              persist=False)

    threads = [threading.Thread(target=work, args=(c,)) for c in (1, 2, 3, 4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert peak <= settings.FORECAST_WORKERS


def _sales_csv(rows):
    head = "invoice_no,date,outlet_code,sku,quantity\n"
    return head + "".join(f"{r}\n" for r in rows)


def _sample_row(db, invoice):
    from app.models import Outlet, Product

    o = db.scalar(select(Outlet).order_by(Outlet.id))
    p = db.scalar(select(Product).order_by(Product.id))
    day = db.scalar(select(func.max(Sale.sale_date)))
    return f"{invoice},{day.isoformat()},{o.code},{p.sku},1"


def test_a_dry_run_import_leaves_no_trace_in_live_data(client, admin):
    with SessionLocal() as db:
        before = db.scalar(select(func.count(Sale.id)))
        row = _sample_row(db, "ISO-DRY-1")
    files = {"file": ("dry.csv", _sales_csv([row]).encode(), "text/csv")}
    r = client.post("/api/imports/sales?dry_run=true", headers=admin, files=files)
    assert r.status_code == 200 and r.json()["created"] == 1 and not r.json()["committed"]
    with SessionLocal() as db:
        assert db.scalar(select(func.count(Sale.id))) == before
        assert db.scalar(select(Sale).where(Sale.invoice_no == "ISO-DRY-1")) is None
        assert db.get(ImportJob, r.json()["job_id"]).status == "validated"


def test_imports_run_one_at_a_time_so_a_file_cannot_be_imported_twice(client, admin, monkeypatch):
    import time

    from app.services import importer

    real = importer.create_sale

    def slow_create_sale(*a, **k):  # widen the gap between the duplicate check and the insert
        time.sleep(0.5)
        return real(*a, **k)

    monkeypatch.setattr(importer, "create_sale", slow_create_sale)
    with SessionLocal() as db:
        row = _sample_row(db, "ISO-TWICE-1")
    body = _sales_csv([row]).encode()
    results = []

    def upload():
        files = {"file": ("twice.csv", body, "text/csv")}
        results.append(client.post("/api/imports/sales?dry_run=false&skip_duplicates=true", headers=admin, files=files))

    threads = [threading.Thread(target=upload) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(r.status_code == 200 for r in results), [r.text for r in results]
    assert sorted(r.json()["created"] for r in results) == [0, 0, 1]
    # the later uploads saw the first one's bill and skipped it cleanly (no clash on the invoice number)
    assert sorted(r.json()["skipped_duplicates"] for r in results) == [0, 1, 1]
    assert all(r.json()["error_count"] == 0 for r in results), [r.json()["errors"] for r in results]
    with SessionLocal() as db:
        assert db.scalar(select(func.count(Sale.id)).where(Sale.invoice_no == "ISO-TWICE-1")) == 1


def test_a_failing_import_keeps_live_data_and_records_the_failure(client, admin, monkeypatch):
    from app.services import importer

    with SessionLocal() as db:
        before = db.scalar(select(func.count(Sale.id)))
        row = _sample_row(db, "ISO-FAIL-1")

    real = importer._import_sales

    def explode(db, rows, user, result, opts):
        real(db, rows, user, result, opts)  # the rows are written, then the server fails before the commit
        raise RuntimeError("disk full")

    monkeypatch.setattr(importer, "_import_sales", explode)
    files = {"file": ("fail.csv", _sales_csv([row]).encode(), "text/csv")}
    from fastapi.testclient import TestClient

    from app.main import app

    r = TestClient(app, raise_server_exceptions=False).post("/api/imports/sales?dry_run=false", headers=admin,
                                                            files=files)
    assert r.status_code == 500
    with SessionLocal() as db:
        assert db.scalar(select(func.count(Sale.id))) == before
        job = db.scalar(select(ImportJob).order_by(ImportJob.id.desc()))
        assert job.filename == "fail.csv" and job.status == "failed"
