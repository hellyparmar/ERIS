"""Load check for the request pipelines: N concurrent workers over the heavy endpoints of a running ERIS API.

Run against a local or staging server (never against production without the owner): ERIS_BASE=http://127.0.0.1:8000 python3 scripts/load_check.py 40 700
Prints status codes per endpoint and latency; a server error (5xx other than 503 busy) or an exception fails the check."""
import concurrent.futures as cf
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict

BASE = os.environ.get("ERIS_BASE", "http://127.0.0.1:8000")
CONC = int(sys.argv[1]); TOTAL = int(sys.argv[2])

def call(method, path, token=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    if token: req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        data = json.dumps(body).encode(); req.add_header("content-type", "application/json")
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            r.read(); return r.status, time.perf_counter() - t
    except urllib.error.HTTPError as e:
        e.read(); return e.code, time.perf_counter() - t
    except OSError as e:  # connection refused, reset or timed out
        return f"EXC:{type(e).__name__}", time.perf_counter() - t

accounts = json.loads(urllib.request.urlopen(BASE + "/api/auth/demo-accounts").read())
admin = next(a for a in accounts if a["email"] == "admin@eris.demo")
tok = json.loads(urllib.request.urlopen(urllib.request.Request(BASE + "/api/auth/login", data=json.dumps({"email": admin["email"], "password": admin["password"]}).encode(), headers={"content-type": "application/json"})).read())["access_token"]

paths = [
    ("GET", "/api/dashboard?period=30d"),
    ("GET", "/api/analytics/sales?period=30d"),
    ("GET", "/api/sales?page=1&page_size=50"),
    ("GET", "/api/products?fields=basic"),
    ("GET", "/api/forecast?scope=category&target_id=2&horizon=21&model=holt_winters"),
    ("GET", "/api/sales/export?period=30d"),
    ("POST", "/api/assistant/chat"),
]
jobs = []
for i in range(TOTAL):
    m, p = paths[i % len(paths)]
    body = {"message": "What were the top selling dishes last month?"} if p.endswith("chat") else None
    jobs.append((m, p, body))

t0 = time.perf_counter()
results = []
with cf.ThreadPoolExecutor(max_workers=CONC) as ex:
    futs = {ex.submit(call, m, p, tok, b): (m, p) for m, p, b in jobs}
    for f in cf.as_completed(futs):
        c, dt = f.result()
        results.append((futs[f][1].split("?")[0], c, dt))
wall = time.perf_counter() - t0
codes = Counter(str(c) for _, c, _ in results)
print(f"concurrency={CONC} requests={TOTAL} wall={wall:.1f}s throughput={TOTAL/wall:.1f}/s")
print("status codes:", dict(codes))
by = defaultdict(list)
for name, c, dt in results:
    by[name].append((c, dt))
for name, rows in by.items():
    ok = [dt for c, dt in rows if c == 200]
    cs = Counter(str(c) for c, _ in rows)
    p95 = sorted(ok)[int(0.95 * (len(ok) - 1))] if ok else float("nan")
    p50 = statistics.median(ok) if ok else float("nan")
    print(f"{name:28s} {dict(cs)}  ok_p50={p50:.2f}s ok_p95={p95:.2f}s")
server_errors = [c for _, c, _ in results if (isinstance(c, str)) or (isinstance(c, int) and c >= 500 and c != 503)]
print("server errors (5xx other than 503, or exceptions):", len(server_errors), server_errors[:5])

sys.exit(1 if server_errors else 0)
