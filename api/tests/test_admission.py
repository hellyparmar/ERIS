"""Admission control: at most MAX_INFLIGHT_REQUESTS are answered at once; a request that cannot get a slot within
INFLIGHT_WAIT_SECONDS is refused with 503 and Retry-After. Health checks skip the queue."""
import asyncio

from app.config import settings
from app.hardening import HEALTH_PATH, HardeningMiddleware


def _scope(path):
    return {"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b"",
            "client": ("10.0.0.1", 1234), "server": ("test", 80), "scheme": "http"}


async def _call(mw, path, sent):
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    await mw(_scope(path), receive, send)


def _statuses(sent):
    return [m["status"] for m in sent if m["type"] == "http.response.start"]


def _holding_app(gate):
    async def inner(scope, receive, send):
        await gate.wait()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})
    return inner


def test_a_request_beyond_the_cap_is_refused_after_its_wait_and_capacity_returns(monkeypatch):
    monkeypatch.setattr(settings, "MAX_INFLIGHT_REQUESTS", 1)
    monkeypatch.setattr(settings, "INFLIGHT_WAIT_SECONDS", 0.05)

    async def scenario():
        gate = asyncio.Event()
        mw = HardeningMiddleware(_holding_app(gate))
        a, b, c = [], [], []
        task_a = asyncio.create_task(_call(mw, "/api/dashboard", a))
        await asyncio.sleep(0)  # request A starts and takes the one slot
        await _call(mw, "/api/dashboard", b)  # B: over the cap; waits its turn, then is refused
        gate.set()
        await task_a
        await _call(mw, "/api/dashboard", c)  # the slot is free again
        return a, b, c

    a, b, c = asyncio.run(scenario())
    assert _statuses(a) == [200] and _statuses(c) == [200]
    assert _statuses(b) == [503]
    retry = next(v for k, v in next(m for m in b if m["type"] == "http.response.start")["headers"] if k == b"retry-after")
    assert retry == b"2"


def test_health_checks_are_not_refused_when_the_server_is_busy(monkeypatch):
    monkeypatch.setattr(settings, "MAX_INFLIGHT_REQUESTS", 1)
    monkeypatch.setattr(settings, "INFLIGHT_WAIT_SECONDS", 0.05)

    async def scenario():
        gate = asyncio.Event()
        mw = HardeningMiddleware(_holding_app(gate))
        task_a = asyncio.create_task(_call(mw, "/api/dashboard", []))
        await asyncio.sleep(0)
        health = []
        gate.set()  # the health check itself does not wait on the gate once it is open
        await _call(mw, HEALTH_PATH, health)
        await task_a
        return health

    assert _statuses(asyncio.run(scenario())) == [200]


def test_zero_disables_the_cap(monkeypatch):
    monkeypatch.setattr(settings, "MAX_INFLIGHT_REQUESTS", 0)

    async def scenario():
        async def inner(scope, receive, send):
            await asyncio.sleep(0.05)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})
        mw = HardeningMiddleware(inner)
        sent = [[] for _ in range(5)]
        await asyncio.gather(*(_call(mw, "/api/dashboard", s) for s in sent))
        return sent

    assert all(_statuses(s) == [200] for s in asyncio.run(scenario()))
