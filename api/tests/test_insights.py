"""Forecast runs, model comparison, stockout risk, anomaly detection and driver analysis."""


def test_forecast_runs_are_persisted(client, admin):
    fc = client.get("/api/forecast?scope=category&target_id=1&horizon=7", headers=admin).json()
    assert fc["run_id"] and fc["model_version"] and fc["data_range"]["end"]
    runs = client.get("/api/forecast/runs", headers=admin).json()
    assert any(r["id"] == fc["run_id"] for r in runs["items"])
    run = client.get(f"/api/forecast/runs/{fc['run_id']}", headers=admin).json()
    assert run["horizon"] == 7 and len(run["results"]) == 7
    assert run["selected_model"] == fc["model"]
    selected = next(m for m in run["metrics"] if m.get("selected"))
    assert {"wape", "mae", "rmse", "smape"} <= set(selected)


def test_stockout_risk(client, admin):
    r = client.get("/api/forecast/stockout-risk?days=14", headers=admin)
    assert r.status_code == 200, r.text
    for item in r.json()["items"]:
        assert 0 <= item["days_left"] <= 14


def test_anomalies_detect_injected_events(client, admin):
    r = client.get("/api/anomalies?period=180d", headers=admin)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["anomalies"], "the generator injects anomalies, some must be found"
    assert all(a["explanation"] for a in d["anomalies"])
    ev = d["evaluation"]
    assert ev and ev["labelled"] > 0
    assert ev["recall"] >= 0.5 and ev["precision"] >= 0.5


def test_anomalies_respect_outlet_scope(client, manager):
    d = client.get("/api/anomalies?period=180d", headers=manager).json()
    assert {a["outlet"] for a in d["anomalies"]} <= {"Andheri West"}
    assert client.get("/api/anomalies?outlet_id=2", headers=manager).status_code == 403


def test_revenue_drivers_add_up(client, admin):
    r = client.get("/api/analytics/drivers?period=7d", headers=admin)
    assert r.status_code == 200, r.text
    d = r.json()
    assert not d["insufficient_data"]
    dec = d["decomposition"]
    assert abs(dec["traffic"] + dec["basket"] - d["change"]) < 1
    assert abs(sum(o["change"] for o in d["outlets"]) - d["change"]) < 1
    assert d["summary"] and d["summary"][0].startswith("Revenue is")
    r = client.get("/api/analytics/drivers?start=2020-01-01&end=2020-01-07", headers=admin)
    assert r.json()["insufficient_data"]
    assert client.get("/api/analytics/drivers?compare_start=2025-01-01", headers=admin).status_code == 422


def test_viewer_is_read_only(client, viewer):
    assert client.get("/api/dashboard", headers=viewer).status_code == 200
    r = client.post("/api/sales", headers=viewer, json={"outlet_id": 1, "payment_method": "cash",
                                                        "items": [{"product_id": 14, "quantity": 1}]})
    assert r.status_code == 403
    assert client.post("/api/customers", headers=viewer, json={"name": "X"}).status_code == 403


def test_forecast_runs_are_scoped(client, admin, manager):
    org = client.get("/api/forecast?scope=total&horizon=7", headers=admin).json()
    assert client.get(f"/api/forecast/runs/{org['run_id']}", headers=manager).status_code == 403
    own = client.get("/api/forecast?scope=total&horizon=7", headers=manager).json()
    assert client.get(f"/api/forecast/runs/{own['run_id']}", headers=manager).status_code == 200
    ids = {r["id"] for r in client.get("/api/forecast/runs", headers=manager).json()["items"]}
    assert own["run_id"] in ids and org["run_id"] not in ids
