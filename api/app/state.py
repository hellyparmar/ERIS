"""Process-wide state for background jobs (demo data generation)."""
import os
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


def lower_thread_priority(niceness: int = 10) -> None:
    """Run the calling background thread behind the request threads, so a long job uses spare CPU instead of
    slowing the pages people are waiting on. Only for jobs that do not hold the database write lock while they
    work (a starved lock holder would stall every writer). Linux only; a no-op elsewhere."""
    try:
        os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), niceness)
    except (AttributeError, OSError):
        pass
