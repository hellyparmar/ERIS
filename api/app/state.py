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
