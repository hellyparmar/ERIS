"""Demo data generator and the stale-demo refresh, on a separate small database."""
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import AnomalyLabel, DatasetInfo, Outlet, Sale
from app.seed.generator import generate_demo_data
from app.seed.refresh import shift_demo_dates


@pytest.fixture()
def small_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'demo.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_generator_is_deterministic_and_documented(small_db):
    end = date(2025, 12, 31)
    counts = generate_demo_data(small_db, days=90, seed=42, end_date=end, n_outlets=2, log=lambda *_: None)
    assert counts["outlets"] == 2 and counts["sales"] > 1000
    ds = small_db.scalar(select(DatasetInfo))
    assert (ds.random_seed, ds.period_end, ds.parameters["fixed_end_date"]) == (42, end, True)
    assert small_db.scalar(select(func.max(Sale.sale_date))) == end
    assert small_db.scalar(select(func.count()).select_from(Sale).where(Sale.dataset_id.is_(None))) == 0
    assert small_db.scalar(select(func.count(AnomalyLabel.id))) > 0
    first_total = small_db.scalar(select(func.sum(Sale.total)))
    generate_demo_data(small_db, days=90, seed=42, end_date=end, n_outlets=2, log=lambda *_: None)
    assert small_db.scalar(select(func.sum(Sale.total))) == pytest.approx(first_total)


def test_fixed_end_date_is_not_shifted_but_rolling_demo_is(small_db):
    generate_demo_data(small_db, days=90, seed=1, end_date=date(2025, 6, 30), n_outlets=1, log=lambda *_: None)
    assert shift_demo_dates(small_db) == 0  # generated to end on a chosen date: stays there
    ds = small_db.scalar(select(DatasetInfo))
    ds.parameters = {**ds.parameters, "fixed_end_date": False}
    small_db.commit()
    shifted = shift_demo_dates(small_db)
    assert shifted > 0 and shifted % 7 == 0  # whole weeks keep weekday patterns aligned
    latest = small_db.scalar(select(func.max(Sale.sale_date)))
    assert date.today() - timedelta(days=8) <= latest <= date.today()


def test_generator_rejects_too_short_history(small_db):
    with pytest.raises(ValueError, match="at least 90 days"):
        generate_demo_data(small_db, days=30, log=lambda *_: None)
    assert small_db.scalar(select(func.count(Outlet.id))) == 0
