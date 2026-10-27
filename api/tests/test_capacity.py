"""Concurrency gates for exports and single-flight answers for the response cache."""
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.capacity import Busy, Gate


def test_gate_admits_up_to_its_slots_then_reports_busy():
    gate = Gate(slots=1, wait=0.05)
    entered = threading.Event()
    release = threading.Event()

    def holder():
        with gate():
            entered.set()
            release.wait(2)

    t = threading.Thread(target=holder)
    t.start()
    entered.wait(2)
    with pytest.raises(Busy):
        with gate():
            pass
    release.set()
    t.join()
    with gate():  # free again once the holder leaves
        pass


def test_export_answers_busy_with_503_when_gate_is_full(client, admin, monkeypatch):
    from app.services import capacity

    gate = Gate(slots=1, wait=0.05)
    monkeypatch.setattr(capacity, "EXPORTS", gate)
    import app.routers.sales as sales_router
    monkeypatch.setattr(sales_router, "EXPORTS", gate)
    release = threading.Event()
    holding = threading.Event()

    def hold():
        with gate():
            holding.set()
            release.wait(3)

    t = threading.Thread(target=hold)
    t.start()
    holding.wait(2)
    try:
        r = client.get("/api/sales/export?format=csv", headers=admin)
        assert r.status_code == 503
        assert r.headers["retry-after"] == "2"
        assert "busy" in r.json()["detail"]
    finally:
        release.set()
        t.join()


def test_identical_requests_at_once_compute_the_answer_once(monkeypatch):
    """Single flight: concurrent cache misses for one answer share one computation."""
    calls = {"n": 0}

    import app.services.response_cache as rc

    original_compute = rc._compute_and_store

    async def counting(request, call_next, key, version):
        calls["n"] += 1
        time.sleep(0.2)  # make the first request slow enough that the others arrive while it runs
        return await original_compute(request, call_next, key, version)

    monkeypatch.setattr(rc, "_compute_and_store", counting)
    settings_before = settings.RATE_LIMIT_ENABLED
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    try:
        with TestClient(app) as c:
            token = c.post("/api/auth/login", json={"email": "admin@eris.demo", "password": "Admin@123"}).json()["access_token"]
            # a fresh key: an unusual period nobody has asked for before
            url = "/api/dashboard?period=7d&outlet_id=1"
            headers = {"authorization": f"Bearer {token}"}
            results: list[int] = []

            def ask():
                results.append(c.get(url, headers=headers).status_code)

            threads = [threading.Thread(target=ask) for _ in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(30)
        assert results and all(code == 200 for code in results)
        assert calls["n"] == 1  # six concurrent misses, one computation
    finally:
        monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", settings_before)
