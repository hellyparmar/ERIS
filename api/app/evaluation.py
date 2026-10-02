"""Rolling-origin evaluation of the forecasting models.

    python -m app.evaluation [--origins 3] [--horizon 28] [--products 10] [--out ../docs]

For every series (total, each outlet, each category and the top-N products) and several forecast origins,
each model is trained on data before the origin and scored on the following `horizon` days. "ERIS auto" is the
production pipeline itself: inner back-test on the training data, pick the best model, forecast — so its
score is what users actually get. Writes a Markdown report, a CSV of all scores and charts.
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, Outlet
from app.services import analytics as A
from app.services import forecasting as F

log = logging.getLogger(__name__)
MODEL_ORDER = ["seasonal_naive", "holt_winters", "xgboost", "prophet", "auto"]
LABELS = {**{k: v.split(" (")[0] for k, v in F.MODEL_LABELS.items()}, "auto": "ERIS auto-selection"}


def series_specs(db: Session, products: int) -> list[F.SeriesSpec]:
    specs = [F.build_spec(db, "total", None, None)]
    specs += [F.build_spec(db, "outlet", o.id, None) for o in db.scalars(select(Outlet).order_by(Outlet.id))]
    specs += [F.build_spec(db, "category", c.id, None) for c in db.scalars(select(Category).order_by(Category.name))]
    anchor = A.anchor_date(db)
    top = A.top_products(db, A.DateRange(anchor - pd.Timedelta(days=89).to_pytimedelta(), anchor), None, products, sort="units")
    specs += [F.build_spec(db, "product", p["product_id"], None) for p in top]
    return specs


def evaluate(db: Session, origins: int = 3, horizon: int = 28, products: int = 10, progress=print) -> pd.DataFrame:
    anchor = A.anchor_date(db)
    models = F.available_models()
    rows = []
    specs = series_specs(db, products)
    for i, spec in enumerate(specs, 1):
        series = F.load_series(db, spec, anchor)
        exog = F.load_exog(db, spec, series, horizon)
        progress(f"[{i}/{len(specs)}] {spec.label} ({len(series)} days)")
        for k in range(origins, 0, -1):
            cut = len(series) - k * horizon
            if cut < 120:
                continue
            train, test = series.iloc[:cut], series.iloc[cut:cut + horizon]
            ex = exog.loc[:test.index[-1]] if exog is not None else None
            for name in models:
                try:
                    t0 = time.time()
                    pred = F.MODEL_FUNCS[name](train, horizon, ex)
                    rows.append({"series": spec.label, "scope": spec.scope, "origin": test.index[0].date(), "model": name,
                                 "seconds": round(time.time() - t0, 2), **F._metrics(test.values, pred)})
                except Exception as exc:  # keep evaluating other models
                    log.warning("%s failed on %s: %s", name, spec.label, exc)
            t0 = time.time()
            res = F.run_forecast(train, horizon, "auto", ex)
            pred = np.array([f["yhat"] for f in res["forecast"]])
            lo = np.array([f["lower"] for f in res["forecast"]])
            hi = np.array([f["upper"] for f in res["forecast"]])
            rows.append({"series": spec.label, "scope": spec.scope, "origin": test.index[0].date(), "model": "auto",
                         "chosen": res["model"], "seconds": round(time.time() - t0, 2),
                         "interval_coverage": round(float(np.mean((test.values >= lo) & (test.values <= hi)) * 100), 1),
                         **F._metrics(test.values, pred)})
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    by_scope = df.pivot_table(index="model", columns="scope", values="wape", aggfunc="mean")
    by_scope["all series"] = df.groupby("model")["wape"].mean()
    by_scope = by_scope.reindex([m for m in MODEL_ORDER if m in by_scope.index])
    single = df[df["model"] != "auto"]
    wins = single.loc[single.groupby(["series", "origin"])["wape"].idxmin(), "model"].value_counts()
    chosen = df.loc[df["model"] == "auto", "chosen"].value_counts()
    overall = df.groupby("model").agg(wape=("wape", "mean"), smape=("smape", "mean"), mae=("mae", "mean"),
                                      rmse=("rmse", "mean"), bias_pct=("bias_pct", "mean"),
                                      seconds=("seconds", "mean")).reindex(by_scope.index)
    coverage = df.loc[df["model"] == "auto", "interval_coverage"].mean() if "interval_coverage" in df else None
    return {"wape": by_scope.round(2), "wins": wins, "chosen": chosen, "overall": overall.round(2),
            "coverage": round(float(coverage), 1) if coverage is not None and not np.isnan(coverage) else None}


def save_run(db: Session, df: pd.DataFrame, origins: int, horizon: int, seconds: float, user_id: int | None = None) -> int:
    """Persist an evaluation as a ForecastRun(run_type="evaluation") so the app can show it."""
    from app.models import ForecastRun

    s = summarise(df)
    overall = [{"model": m, "label": LABELS.get(m, m), **{k: (None if pd.isna(v) else float(v)) for k, v in r.items()}}
               for m, r in s["overall"].iterrows()]
    by_scope = {m: {k: (None if pd.isna(v) else float(v)) for k, v in r.items()} for m, r in s["wape"].iterrows()}
    run = ForecastRun(
        run_type="evaluation", scope="all", target="mixed", series_label=f"{df['series'].nunique()} series",
        horizon=horizon, data_start=min(df["origin"]), data_end=max(df["origin"]) + pd.Timedelta(days=horizon - 1),
        selected_model="auto", model_version=F.MODEL_VERSION, features=F.feature_names(),
        parameters={"origins": origins, "horizon": horizon, "series": int(df["series"].nunique()),
                    "runs": int(len(df)), "wape_by_scope": by_scope,
                    "wins": {k: int(v) for k, v in s["wins"].items()},
                    "chosen": {k: int(v) for k, v in s["chosen"].items()},
                    "auto_interval_coverage": s["coverage"]},
        metrics=overall, status="ok", duration_seconds=round(seconds, 1), created_by=user_id)
    db.add(run)
    db.commit()
    return run.id


def _plots(df: pd.DataFrame, s: dict, out: Path, db: Session) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
    files = []
    w = s["wape"].drop(columns="all series")
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(w.columns))
    width = 0.8 / len(w.index)
    for i, (model, row) in enumerate(w.iterrows()):
        ax.bar(x + i * width - 0.4 + width / 2, row.values, width * 0.92, label=LABELS[model], color=colors[i % 5])
    ax.set_xticks(x, [c.title() for c in w.columns])
    ax.set_ylabel("Mean WAPE % (lower is better)")
    ax.set_title("Forecast error by model and series type (rolling-origin back-test)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e1e0d9")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "images" / "eval_wape_by_model.png", dpi=130)
    plt.close(fig)
    files.append("images/eval_wape_by_model.png")

    spec = F.build_spec(db, "total", None, None)
    series = F.load_series(db, spec, A.anchor_date(db))
    train, test = series.iloc[:-28], series.iloc[-28:]
    res = F.run_forecast(train, 28, "auto")
    fc = pd.Series([f["yhat"] for f in res["forecast"]], index=test.index)
    lo = pd.Series([f["lower"] for f in res["forecast"]], index=test.index)
    hi = pd.Series([f["upper"] for f in res["forecast"]], index=test.index)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    hist = series.iloc[-118:-28]
    ax.plot(hist.index, hist.values / 1e5, color=colors[0], lw=1.6, label="Actual (training)")
    ax.plot(test.index, test.values / 1e5, color="#52514e", lw=1.6, label="Actual (held out)")
    ax.plot(fc.index, fc.values / 1e5, color=colors[1], lw=2, label=f"Forecast - {res['model_label']}")
    ax.fill_between(fc.index, lo.values / 1e5, hi.values / 1e5, color=colors[1], alpha=0.15, label="80% range")
    ax.set_ylabel("Daily revenue (₹ lakh)")
    ax.set_title("Hold-out check: total revenue, last 28 days")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e1e0d9")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out / "images" / "eval_holdout_total.png", dpi=130)
    plt.close(fig)
    files.append("images/eval_holdout_total.png")
    return files


def write_report(df: pd.DataFrame, out: Path, db: Session, origins: int, horizon: int) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    s = summarise(df)
    df.to_csv(out / "forecast_evaluation.csv", index=False)
    images = _plots(df, s, out, db)
    w = s["wape"].rename(index=LABELS)
    naive = s["wape"].loc["seasonal_naive", "all series"]
    auto = s["wape"].loc["auto", "all series"]
    best_single = s["wape"].drop(index=["auto"])["all series"].idxmin()
    lines = [
        "# Forecast model evaluation",
        "",
        f"Generated with `python -m app.evaluation` on the demo dataset: {df['series'].nunique()} series "
        f"(total, outlets, categories, top products), {origins} forecast origins each, {horizon}-day horizon - "
        f"{len(df)} model runs. Every model is trained only on data before each origin.",
        "",
        "## Mean WAPE (%) by series type",
        "",
        w.to_markdown(),
        "",
        f"- **ERIS auto-selection: {auto:.1f}% WAPE** vs {naive:.1f}% for the seasonal-naive baseline "
        f"({(naive - auto) / naive * 100:.0f}% lower error).",
        f"- Best single model overall: **{LABELS[best_single]}** ({s['wape'].loc[best_single, 'all series']:.1f}%).",
        f"- 80% prediction-interval coverage of ERIS auto on the held-out windows: **{s['coverage']}%** "
        "(target 80%).",
        "- Product-level series are noisier (small daily counts), so their errors are naturally higher than revenue "
        "series that aggregate many products.",
        "",
        "## All metrics (mean over series and origins)",
        "",
        s["overall"].rename(index=LABELS).to_markdown(),
        "",
        "sMAPE is symmetric MAPE; `seconds` is training + inference time per series and origin.",
        "",
        "## How often each model was the most accurate",
        "",
        s["wins"].rename(index=LABELS).to_frame("wins").to_markdown(),
        "",
        "## What auto-selection picked",
        "",
        s["chosen"].rename(index=lambda m: F.MODEL_LABELS.get(m, m).split(" (")[0]).to_frame("times chosen").to_markdown(),
        "",
        *[f"![chart]({img})\n" for img in images],
        "## Method",
        "",
        "- **WAPE** = Σ|actual − forecast| ÷ Σ actual. Unlike MAPE it is stable when some days have tiny sales.",
        "- **Rolling origin**: origins are spaced one horizon apart, ending at the last day of data, so each "
        "test window is unseen by the model.",
        "- **Auto-selection** reproduces production exactly: it back-tests candidates on the last 4 weeks of "
        "its own training data and refits the winner (or an ensemble of the best two).",
    ]
    path = out / "FORECAST_EVALUATION.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    from app.db import SessionLocal

    logging.basicConfig(level=logging.WARNING)
    p = argparse.ArgumentParser(description="Rolling-origin evaluation of ERIS forecasting models")
    p.add_argument("--origins", type=int, default=3)
    p.add_argument("--horizon", type=int, default=28)
    p.add_argument("--products", type=int, default=10)
    p.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "docs"))
    a = p.parse_args()
    t0 = time.time()
    with SessionLocal() as db:
        df = evaluate(db, a.origins, a.horizon, a.products)
        path = write_report(df, Path(a.out), db, a.origins, a.horizon)
        save_run(db, df, a.origins, a.horizon, time.time() - t0)
    print(f"\nWrote {path} in {time.time() - t0:.0f}s")
    print(summarise(df)["wape"].to_string())


if __name__ == "__main__":
    main()
