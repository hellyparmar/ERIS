"""Start-up in production: the port answers at once, API calls wait for the background work, failures are reported."""
import threading

from fastapi.testclient import TestClient

from app import main
from app.main import app


def _fresh_state(monkeypatch, ready: bool, error: str | None = None):
    event = threading.Event()
    if ready:
        event.set()
    monkeypatch.setattr(main, "_ready", event)
    monkeypatch.setattr(main, "_startup_error", error)


def test_background_start_up_records_a_failure_and_still_marks_the_work_done(monkeypatch):
    _fresh_state(monkeypatch, ready=False)

    def broken():
        raise RuntimeError("boom")

    monkeypatch.setattr(main, "_bootstrap", broken)
    main._bootstrap_in_background()
    assert main._ready.is_set()
    assert main._startup_error and "boom" in main._startup_error


def test_while_starting_health_is_200_and_api_calls_wait(monkeypatch):
    _fresh_state(monkeypatch, ready=False)
    client = TestClient(app)  # no lifespan: the state above is the state under test
    health = client.get("/api/health")
    assert health.status_code == 200 and health.json()["status"] == "starting"
    waiting = client.get("/api/auth/me")
    assert waiting.status_code == 503 and waiting.headers["retry-after"] == "3"
    assert "starting up" in waiting.json()["detail"]


def test_a_failed_start_up_keeps_the_instance_out_of_service(monkeypatch):
    _fresh_state(monkeypatch, ready=True, error="RuntimeError: no database")
    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 503 and health.json()["status"] == "error"
    assert "no database" in health.json()["detail"]
    assert client.get("/api/auth/me").status_code == 503


def test_once_ready_health_is_ok(monkeypatch):
    _fresh_state(monkeypatch, ready=True)
    health = TestClient(app).get("/api/health")
    assert health.status_code == 200 and health.json()["status"] == "ok"
