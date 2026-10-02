"""Assistant v3: the evaluation's example questions, provenance on every answer, documentation lookups,
outlet scoping and independent checks of the numbers it reports."""
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Outlet, Sale
from app.services import analytics as A

EXAMPLES = {
    "Which outlet had the highest revenue last month?": "outlet_ranking",
    "Show the five fastest-growing products.": "growth_products",
    "Why was Outlet 3 revenue lower this week?": "why_change",
    "Which items may go out of stock in the next 14 days?": "stockout_risk",
    "Compare weekend sales between outlets.": "weekend_compare",
    "What forecast model performed best for beverages?": "model_performance",
    "Summarize the major anomalies this month.": "anomalies",
    "What is WAPE?": "knowledge",
    "How do I import sales?": "knowledge",
    "Is the GSTIN real?": "knowledge",
}


def ask(client, headers, q):
    r = client.post("/api/assistant/chat", headers=headers, json={"message": q})
    assert r.status_code == 200, (q, r.text)
    return r.json()


@pytest.mark.parametrize("question,intent", EXAMPLES.items())
def test_example_questions(client, admin, question, intent):
    body = ask(client, admin, question)
    assert body["intent"] == intent, (question, body["intent"])
    assert "something went wrong" not in body["answer"]
    prov = body["provenance"]
    assert prov["query_ms"] >= 0 and prov["method"].startswith("intent template")
    if intent == "knowledge":
        assert prov["sources"] and all(s.startswith("docs/knowledge/") for s in prov["sources"])
    else:
        assert "synthetic demo data" in prov["data_source"]
        assert prov["filters"]["outlets"]


def test_highest_revenue_outlet_matches_database(client, admin):
    body = ask(client, admin, "Which outlet had the highest revenue last month?")
    with SessionLocal() as db:
        anchor = A.anchor_date(db)
        last_end = anchor.replace(day=1) - timedelta(days=1)
        oid = db.execute(select(Sale.outlet_id).where(
            Sale.status == "completed", Sale.sale_date >= last_end.replace(day=1), Sale.sale_date <= last_end)
            .group_by(Sale.outlet_id).order_by(func.sum(Sale.total).desc()).limit(1)).scalar()
        name = db.get(Outlet, oid).name
    assert body["answer"].split("\n")[1].startswith(f"1. **{name}**")
    assert f"{last_end:%B %Y}" in " ".join(body["provenance"]["filters"]["periods"])


def test_outlet_ordinal_resolves_to_third_outlet(client, admin):
    body = ask(client, admin, "Why was Outlet 3 revenue lower this week?")
    with SessionLocal() as db:
        third = db.scalars(select(Outlet).order_by(Outlet.id)).all()[2].name
    assert body["provenance"]["filters"]["outlets"] == third
    assert len(body["provenance"]["filters"]["periods"]) == 2


def test_model_performance_reports_version_and_run(client, admin):
    body = ask(client, admin, "What forecast model performed best for beverages?")
    assert body["provenance"]["model_version"] == "3.0" and body["provenance"]["forecast_run_id"]
    assert "WAPE" in body["answer"] and "Beverages" in body["answer"]


def test_manager_answers_stay_in_scope(client, manager):
    body = ask(client, manager, "Compare weekend sales between outlets.")
    assert body["provenance"]["filters"]["outlets"] == "Andheri West"
    assert "Koregaon" not in body["answer"]


def test_unknown_question_falls_back_without_inventing(client, admin):
    body = ask(client, admin, "tell me a joke about elephants")
    assert body["intent"] == "general"
    assert "not sure" in body["answer"]


def test_period_before_data_is_flagged(client, admin):
    body = ask(client, admin, "Sales in January 2019")
    notes = " ".join(body["provenance"]["notes"])
    assert body["intent"] == "sales_summary"
    assert "outside the recorded data" in notes or "No sales" in body["answer"]


def test_history_keeps_provenance(client, admin):
    ask(client, admin, "Compare weekend sales between outlets.")
    last = client.get("/api/assistant/history?limit=2", headers=admin).json()[-1]
    assert last["role"] == "assistant" and last["provenance"]["filters"]
