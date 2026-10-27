"""Concurrency gates for the heaviest work that is not a forecast.

A gate lets at most `slots` requests do the work at once. A request that cannot get a slot within `wait` seconds
gets a quick "busy, try again" (HTTP 503), so a burst of exports cannot slow every other page down.
"""
import threading
from contextlib import contextmanager

from app.config import settings


class Busy(Exception):
    """Raised when a gate cannot be entered in time. Mapped to HTTP 503 with Retry-After."""


class Gate:
    def __init__(self, slots: int, wait: float) -> None:
        self._sem = threading.BoundedSemaphore(slots)
        self._wait = wait

    @contextmanager
    def __call__(self):
        if not self._sem.acquire(timeout=self._wait):
            raise Busy("The server is busy with other exports. Please try again in a moment.")
        try:
            yield
        finally:
            self._sem.release()


EXPORTS = Gate(settings.EXPORT_WORKERS, settings.EXPORT_WAIT_SECONDS)
