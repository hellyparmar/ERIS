"""Grounding evaluation of the ERIS assistant.

    python -m app.assistant_eval [--out ../docs]

Each case asks the assistant a question as a real user and checks the answer against the database with an
independent SQL query (not the analytics functions the assistant itself uses), plus the expected intent and
the provenance block. Out-of-scope and access-controlled questions check that nothing is invented or leaked.
Writes docs/ASSISTANT_EVALUATION.md.
"""
from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ForecastRun, Outlet, Product, Sale, SaleItem, User
from app.services.assistant.engine import answer
from app.services.assistant.tools import Fmt

F = Fmt("₹")


@dataclass
class Case:
    question: str
    intent: str
    check: Callable[[Session, dict], tuple[bool, str]] | None = None
    user: str = "admin@eris.demo"


# ------------------------------------------------------------------------------------------ independent SQL
def _revenue(db: Session, start: date, end: date, outlet_ids: list[int] | None = None) -> float:
    q = select(func.coalesce(func.sum(Sale.total), 0)).where(Sale.status == "completed", Sale.sale_date >= start,
                                                             Sale.sale_date <= end)
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    return float(db.scalar(q))


def _last_day(db: Session) -> date:
    return db.scalar(select(func.max(Sale.sale_date)).where(Sale.status == "completed"))


def _last_month(db: Session) -> tuple[date, date]:
    end = _last_day(db).replace(day=1) - timedelta(days=1)
    return end.replace(day=1), end


def _outlet(db: Session, name: str) -> Outlet:
    return db.scalar(select(Outlet).where(Outlet.name == name))


def _contains(text: str, needle: str) -> tuple[bool, str]:
    return needle in text, f"expects '{needle}'"


# ------------------------------------------------------------------------------------------ checks
def top_outlet_last_month(db: Session, r: dict):
    start, end = _last_month(db)
    oid = db.execute(select(Sale.outlet_id).where(Sale.status == "completed", Sale.sale_date >= start,
                                                  Sale.sale_date <= end).group_by(Sale.outlet_id)
                     .order_by(func.sum(Sale.total).desc()).limit(1)).scalar()
    o = db.get(Outlet, oid)
    rev = _revenue(db, start, end, [oid])
    ok = r["answer"].split("\n")[1].startswith(f"1. **{o.name}**") and F.money(rev) in r["answer"]
    return ok, f"top outlet {o.name} with {F.money(rev)}"


def outlet_revenue_last_month(name: str):
    def check(db: Session, r: dict):
        start, end = _last_month(db)
        rev = _revenue(db, start, end, [_outlet(db, name).id])
        return _contains(r["answer"], F.money(rev))
    return check


def yesterday_revenue(db: Session, r: dict):
    period = r["provenance"]["filters"]["periods"][0].split(": ")[1].split(" to ")
    d = date.fromisoformat(period[0])
    return _contains(r["answer"], F.money(_revenue(db, d, d)))


def top_product_week(db: Session, r: dict):
    start, end = [date.fromisoformat(x) for x in r["provenance"]["filters"]["periods"][0].split(": ")[1].split(" to ")]
    name, rev = db.execute(select(Product.name, func.sum(SaleItem.line_total)).join(Product, Product.id == SaleItem.product_id)
                           .join(Sale, Sale.id == SaleItem.sale_id).where(Sale.status == "completed",
                                                                         SaleItem.sale_date >= start,
                                                                         SaleItem.sale_date <= end)
                           .group_by(Product.name).order_by(func.sum(SaleItem.line_total).desc()).limit(1)).one()
    ok = f"1. **{name}** - {F.money(rev)}" in r["answer"]
    return ok, f"top product {name} {F.money(rev)}"


def growth_first_product(db: Session, r: dict):
    first = r["answer"].split("\n")[1]
    name = first.split("**")[1]
    start, end = [date.fromisoformat(x) for x in r["provenance"]["filters"]["periods"][0].split(": ")[1].split(" to ")]
    rev = db.scalar(select(func.sum(SaleItem.line_total)).join(Product, Product.id == SaleItem.product_id)
                    .join(Sale, Sale.id == SaleItem.sale_id).where(Sale.status == "completed", Product.name == name,
                                                                  SaleItem.sale_date >= start, SaleItem.sale_date <= end))
    return F.money(rev) in first, f"{name}: {F.money(rev)} in the current period"


def why_outlet3(db: Session, r: dict):
    third = db.scalars(select(Outlet).order_by(Outlet.id)).all()[2]
    p = r["provenance"]["filters"]
    cur, cmp = [[date.fromisoformat(x) for x in s.split(": ")[1].split(" to ")] for s in p["periods"]]
    r1, r0 = _revenue(db, *cur, [third.id]), _revenue(db, *cmp, [third.id])
    ok = p["outlets"] == third.name and F.money(r1) in r["answer"] and F.money(r0) in r["answer"]
    return ok, f"{third.name}: {F.money(r1)} vs {F.money(r0)}"


def weekend_andheri(db: Session, r: dict):
    o = _outlet(db, "Andheri West")
    start, end = [date.fromisoformat(x) for x in r["provenance"]["filters"]["periods"][0].split(": ")[1].split(" to ")]
    rows = db.execute(select(Sale.sale_date, func.sum(Sale.total)).where(
        Sale.status == "completed", Sale.outlet_id == o.id, Sale.sale_date >= start, Sale.sale_date <= end)
        .group_by(Sale.sale_date)).all()
    we = [float(v) for d, v in rows if d.weekday() >= 5]
    avg = sum(we) / len(we)
    return _contains(r["answer"], f"weekend {F.money(avg)}")


def best_model_beverages(db: Session, r: dict):
    run = db.get(ForecastRun, r["provenance"]["forecast_run_id"])
    best = min((m for m in run.metrics if m.get("wape") is not None), key=lambda m: m["wape"])
    return f"**{best['label']}** with **{best['wape']:.1f}% WAPE**" in r["answer"], f"{best['label']} {best['wape']:.1f}%"


def knowledge_source(doc: str):
    def check(db: Session, r: dict):
        srcs = r["provenance"]["sources"]
        return bool(srcs) and srcs[0].startswith(f"docs/knowledge/{doc}"), f"first source {doc}"
    return check


def no_numbers(db: Session, r: dict):
    return "₹" not in r["answer"], "no figures in a fallback answer"


def outside_data(db: Session, r: dict):
    notes = " ".join(r["provenance"]["notes"])
    return "outside the recorded data" in notes, "insufficient-data note shown"


def manager_scoped(db: Session, r: dict):
    start, end = _last_month(db)
    other = _revenue(db, start, end, [_outlet(db, "Koregaon Park").id])
    own = _revenue(db, start, end, [_outlet(db, "Andheri West").id])
    ok = F.money(other) not in r["answer"] and F.money(own) in r["answer"]
    return ok, "answers for own outlet (Andheri West) only"


CASES = [
    Case("Which outlet had the highest revenue last month?", "outlet_ranking", top_outlet_last_month),
    Case("Show the five fastest-growing products.", "growth_products", growth_first_product),
    Case("Why was Outlet 3 revenue lower this week?", "why_change", why_outlet3),
    Case("Which items may go out of stock in the next 14 days?", "stockout_risk"),
    Case("Compare weekend sales between outlets.", "weekend_compare", weekend_andheri),
    Case("What forecast model performed best for beverages?", "model_performance", best_model_beverages),
    Case("Summarize the major anomalies this month.", "anomalies"),
    Case("How much did we sell yesterday?", "sales_summary", yesterday_revenue),
    Case("Revenue at Indiranagar last month", "sales_summary", outlet_revenue_last_month("Indiranagar")),
    Case("Top 5 products this week", "top_products", top_product_week),
    Case("Compare this month with last month", "compare_periods"),
    Case("Forecast sales for next week", "forecast"),
    Case("What should I reorder?", "reorder"),
    Case("Which customers are at risk?", "customers"),
    Case("Which products are bought together?", "basket_analysis"),
    Case("What is WAPE?", "knowledge", knowledge_source("glossary.md")),
    Case("How do I import sales?", "knowledge", knowledge_source("imports.md")),
    Case("Is the GSTIN real?", "knowledge", knowledge_source("invoices.md")),
    Case("How is the forecast model chosen?", "knowledge", knowledge_source("forecasting.md")),
    Case("How are anomalies detected?", "knowledge", knowledge_source("anomalies-and-drivers.md")),
    Case("Who will win the cricket world cup?", "general", no_numbers),
    Case("Sales in January 2019", "sales_summary", outside_data),
    Case("Revenue at Koregaon Park last month", "sales_summary", manager_scoped, user="priya.and@eris.demo"),
]


def run(db: Session) -> list[dict]:
    rows = []
    for c in CASES:
        user = db.scalar(select(User).where(User.email == c.user))
        t0 = time.perf_counter()
        r = answer(db, user, c.question)
        ms = (time.perf_counter() - t0) * 1000
        prov = r.get("provenance") or {}
        has_prov = bool(prov.get("method")) and (prov.get("data_source") is not None or c.intent == "general")
        grounded, detail = (None, "intent and provenance only")
        if c.check:
            try:
                grounded, detail = c.check(db, r)
            except Exception as exc:  # a failing check is a failed case, not a crash
                grounded, detail = False, f"check error: {exc}"
        rows.append({"question": c.question, "user": c.user.split("@")[0], "expected": c.intent, "intent": r["intent"],
                     "intent_ok": r["intent"] == c.intent, "grounded": grounded, "detail": detail,
                     "provenance": has_prov, "ms": round(ms)})
    return rows


def write_report(rows: list[dict], out: Path, db: Session) -> Path:
    n = len(rows)
    intent_ok = sum(r["intent_ok"] for r in rows)
    checked = [r for r in rows if r["grounded"] is not None]
    grounded = sum(bool(r["grounded"]) for r in checked)
    prov = sum(r["provenance"] for r in rows)
    ms = sorted(r["ms"] for r in rows)
    lines = [
        "# Assistant grounding evaluation", "",
        f"Generated by `python -m app.assistant_eval` on {date.today().isoformat()} against the synthetic demo "
        f"dataset (data to {_last_day(db)}), with the optional LLM switched off (structured mode).", "",
        "Each question is asked through the same code path as the chat API. Numbers in the answer are checked "
        "against independent SQL queries written for this evaluation (not the analytics functions the assistant "
        "uses). Documentation questions are checked for the right source file; the out-of-scope question must "
        "not produce figures; the manager question must not reveal another outlet's numbers.", "",
        "| Metric | Result |", "|---|---|",
        f"| Intent recognised | {intent_ok}/{n} ({intent_ok / n * 100:.0f}%) |",
        f"| Numbers / sources match the database | {grounded}/{len(checked)} ({grounded / max(len(checked), 1) * 100:.0f}%) |",
        f"| Answers with a provenance block | {prov}/{n} |",
        f"| Median / max response time | {ms[n // 2]} ms / {ms[-1]} ms |", "",
        "| Question | User | Intent | Grounding check | Result | ms |", "|---|---|---|---|---|---|",
    ]
    for r in rows:
        res = "n/a" if r["grounded"] is None else ("pass" if r["grounded"] else "**FAIL**")
        intent = r["intent"] if r["intent_ok"] else f"**{r['intent']}** (expected {r['expected']})"
        lines.append(f"| {r['question']} | {r['user']} | {intent} | {r['detail']} | {res} | {r['ms']} |")
    lines += ["", "## Limitations", "",
              "- The questions are written by the developer; real users phrase things in more ways than the rule-based "
              "parser covers. Unrecognised questions fall back to a help message (or to the local LLM when installed).",
              "- Checks verify that reported figures equal the database; they do not judge whether the explanation "
              "of a change is the true business cause (driver effects other than bills and average bill are estimates).",
              "- Results are on synthetic data."]
    path = out / "ASSISTANT_EVALUATION.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    from app.db import SessionLocal

    p = argparse.ArgumentParser(description="Grounding evaluation of the ERIS assistant")
    p.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "docs"))
    a = p.parse_args()
    with SessionLocal() as db:
        rows = run(db)
        path = write_report(rows, Path(a.out), db)
    for r in rows:
        print(f"{'OK ' if r['intent_ok'] and r['grounded'] is not False else 'BAD'} {r['question']} -> {r['intent']} "
              f"{r['detail']} {r['grounded']}")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
