"""Process-wide state for background jobs (demo data generation)."""
import threading

_lock = threading.Lock()
_seeding = {"running": False, "message": None}


def set_seeding(running: bool, message: str | None = None) -> None:
    with _lock:
        _seeding.update(running=running, message=message)


def seeding_state() -> dict:
    with _lock:
        return dict(_seeding)


_jobs: dict[str, dict] = {}


def set_job(name: str, **fields) -> None:
    with _lock:
        _jobs.setdefault(name, {"running": False, "message": None}).update(fields)


def job_state(name: str) -> dict:
    with _lock:
        return dict(_jobs.get(name, {"running": False, "message": None}))
