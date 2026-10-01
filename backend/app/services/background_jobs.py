"""Small in-process background-job registry for portfolio deployments.

ERIS runs as a single web process. Long-running forecast work is executed through
Starlette's thread-backed ``BackgroundTasks`` support, avoiding a separate broker and
worker service. Completed forecast data remains durable in PostgreSQL; this registry
only tracks short-lived request status and is intentionally process-local.
"""

from copy import deepcopy
from datetime import datetime, timezone
import logging
from threading import Lock
from typing import Any, Callable
from uuid import uuid4


_jobs: dict[str, dict[str, Any]] = {}
_lock = Lock()
_MAX_JOBS = 200
logger = logging.getLogger(__name__)


def create_job(*, owner_user_id: int, outlet_id: int) -> str:
    job_id = str(uuid4())
    with _lock:
        if len(_jobs) >= _MAX_JOBS:
            oldest = min(_jobs, key=lambda key: _jobs[key]["created_at"])
            _jobs.pop(oldest, None)
        _jobs[job_id] = {
            "status": "pending",
            "result": None,
            "owner_user_id": owner_user_id,
            "outlet_id": outlet_id,
            "created_at": datetime.now(timezone.utc),
        }
    return job_id


def run_job(job_id: str, function: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    with _lock:
        _jobs[job_id]["status"] = "running"
    try:
        result = function(*args, **kwargs)
        failed = isinstance(result, dict) and result.get("status") == "failed"
        with _lock:
            _jobs[job_id]["status"] = "failed" if failed else "complete"
            _jobs[job_id]["result"] = result
    except Exception:
        logger.exception("Background job %s failed", job_id)
        with _lock:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["result"] = {"status": "failed", "message": "Background job failed"}


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        return deepcopy(job) if job else None
