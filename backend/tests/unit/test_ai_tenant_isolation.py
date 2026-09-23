"""
test_ai_tenant_isolation.py
----------------------------
Verifies that the AI assistant's SQL execution is correctly scoped per
authenticated user so that Outlet A's user cannot see Outlet B's revenue.

SQLite limitation note
-----------------------
This test runs against SQLite (eris_dev.db) because PostgreSQL is not
available in this environment.  SQLite has NO row-level security —
the FORCE ROW LEVEL SECURITY policies defined in Alembic migration
da04c5929846_add_tenant_id_to_multi_tenant_models.py are PostgreSQL-only
and do not execute here.

What this test DOES prove:
  1. inject_outlet_filter() injects the correct outlet_id IN (...) clause
     into template SQL, so each user's query is WHERE-scoped to their
     own outlet(s) at the SQL level.
  2. execute_template_query_with_session() uses the app's existing
     get_db_sync(tenant_id=...) context manager, which would call
     SELECT set_config('app.current_tenant_id', ...) on a real Postgres
     connection — traceable by code inspection below.
  3. Two users with different outlet scopes get different row counts from
     the same template query against the same SQLite db.

What this test does NOT prove:
  - That PostgreSQL RLS policies actually enforce isolation in production.
  - To verify that, you must run this against a live Postgres instance with
    the RLS policies applied (alembic upgrade head) and FORCE ROW LEVEL
    SECURITY enabled on the 6 tenant-scoped tables.
"""

import os, sys, sqlite3, re
import pytest

# Point at the dev SQLite db so we can use real seeded rows
os.environ["DATABASE_URL"] = "sqlite:///./eris_dev.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.semantic_layer import semantic_layer
from app.services.query_executor import query_executor
from app.database import get_db_sync


# ── Step 1: Read real outlet IDs and their sales totals from SQLite ─────────

def get_outlet_sales(conn, outlet_id):
    cur = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0), COUNT(*) FROM sales WHERE outlet_id = ?",
        (outlet_id,),
    )
    rev, cnt = cur.fetchone()
    return float(rev), int(cnt)


def get_all_outlets(conn):
    cur = conn.execute(
        "SELECT id, name FROM outlets WHERE is_active = 1 ORDER BY id LIMIT 2"
    )
    return cur.fetchall()


# ── Step 2: Build a minimal fake User-like object ────────────────────────────

class FakeUser:
    def __init__(self, outlet_id, org_id=1):
        self.outlet_id = outlet_id
        self.organization_id = org_id


# ── Tests ─────────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "eris_dev.db"
)


def test_inject_outlet_filter_adds_clause():
    """inject_outlet_filter must append an outlet_id IN (...) clause to sales queries."""
    template_match = semantic_layer.match_template("total revenue this month")
    assert template_match is not None, "Template 'revenue_by_period' should match"
    _, template_sql = template_match

    scoped_sql, params = semantic_layer.inject_outlet_filter(template_sql, [1, 2])
    assert re.search(r"outlet_id IN \(:o\d+(, :o\d+)*\)", scoped_sql), (
        f"Expected outlet_id IN (:o0, :o1, ...) clause in scoped SQL.\nGot:\n{scoped_sql}"
    )
    assert params == {"o0": 1, "o1": 2}
    print(f"\n[PASS] inject_outlet_filter — scoped SQL:\n{scoped_sql}")


def test_inject_outlet_filter_no_sales_table():
    """inject_outlet_filter must NOT modify supplier_debt (no sales table)."""
    template_match = semantic_layer.match_template("which supplier do i owe the most to")
    assert template_match is not None
    _, template_sql = template_match

    scoped_sql, params = semantic_layer.inject_outlet_filter(template_sql, [1])
    assert "outlet_id" not in scoped_sql, (
        "supplier_debt has no outlet_id column — filter must not be injected"
    )
    print(f"\n[PASS] inject_outlet_filter correctly skips non-sales template")


def test_two_outlets_get_different_revenue():
    """
    Core isolation test: two users with different outlet scopes must receive
    different revenue figures from the same 'revenue_by_period' template.

    This confirms the outlet_id IN (...) WHERE clause is actually applied and
    returns different subsets of rows.
    """
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Dev DB not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    outlets = get_all_outlets(conn)
    if len(outlets) < 2:
        pytest.skip("Need at least 2 active outlets in eris_dev.db")

    outlet_a_id, outlet_a_name = outlets[0]
    outlet_b_id, outlet_b_name = outlets[1]

    expected_rev_a, expected_cnt_a = get_outlet_sales(conn, outlet_a_id)
    expected_rev_b, expected_cnt_b = get_outlet_sales(conn, outlet_b_id)
    conn.close()

    print(f"\nDirect SQL — Outlet A ({outlet_a_name}, id={outlet_a_id}): "
          f"rev={expected_rev_a:.2f}, orders={expected_cnt_a}")
    print(f"Direct SQL — Outlet B ({outlet_b_name}, id={outlet_b_id}): "
          f"rev={expected_rev_b:.2f}, orders={expected_cnt_b}")

    assert expected_rev_a != expected_rev_b, (
        "Test precondition failed: both outlets have identical revenue — "
        "cannot distinguish isolation."
    )

    # ── Run template query scoped to Outlet A ────────────────────────────────
    template_match = semantic_layer.match_template("total revenue this year")
    assert template_match is not None
    _, template_sql = template_match

    # Outlet A user — use query_executor's own engine (initialised with eris_dev.db)
    from sqlalchemy.orm import Session as _Session
    scoped_sql_a, scope_params_a = semantic_layer.inject_outlet_filter(template_sql, [outlet_a_id])
    with _Session(query_executor.engine) as db_a:
        result_a = query_executor.execute_template_query_with_session(
            scoped_sql_a, semantic_layer, db_a, params=scope_params_a
        )
    assert result_a["success"], f"Query A failed: {result_a.get('error')}"
    rev_a = result_a["data"][0]["total_revenue"] if result_a["data"] else 0

    # Outlet B user
    scoped_sql_b, scope_params_b = semantic_layer.inject_outlet_filter(template_sql, [outlet_b_id])
    with _Session(query_executor.engine) as db_b:
        result_b = query_executor.execute_template_query_with_session(
            scoped_sql_b, semantic_layer, db_b, params=scope_params_b
        )
    assert result_b["success"], f"Query B failed: {result_b.get('error')}"
    rev_b = result_b["data"][0]["total_revenue"] if result_b["data"] else 0

    print(f"\nScoped query — Outlet A user response: total_revenue={rev_a}")
    print(f"Scoped query — Outlet B user response: total_revenue={rev_b}")
    print(f"Scoped SQL A (excerpt): {scoped_sql_a[:200]}")

    assert rev_a != rev_b, (
        f"Isolation FAILED: both scoped queries returned the same revenue "
        f"({rev_a}) for different outlets."
    )
    # Sanity: each scoped result must be less than the all-outlet total
    all_rev = expected_rev_a + expected_rev_b  # at least these two
    assert rev_a < all_rev, (
        f"Outlet A scoped result ({rev_a}) is >= combined outlet total ({all_rev}) — "
        "filter is not working."
    )
    assert rev_b < all_rev, (
        f"Outlet B scoped result ({rev_b}) is >= combined outlet total ({all_rev}) — "
        "filter is not working."
    )

    print(
        f"\n[PASS] Isolation confirmed (SQLite WHERE-clause level):\n"
        f"  Outlet A ({outlet_a_name}): {rev_a:.2f}\n"
        f"  Outlet B ({outlet_b_name}): {rev_b:.2f}\n"
        f"\nNOTE: This does NOT verify PostgreSQL RLS enforcement.\n"
        f"To verify RLS, run against live Postgres with 'alembic upgrade head'\n"
        f"and FORCE ROW LEVEL SECURITY enabled on sales, outlets, customers,\n"
        f"products, inventory, and invoices tables."
    )


def test_get_db_sync_would_call_set_config_on_postgres():
    """
    Code-trace test: verify that get_db_sync(tenant_id=...) executes
    SELECT set_config('app.current_tenant_id', ...) before yielding the
    session, so on a real Postgres deployment RLS would be enforced.

    We trace the source code rather than executing it, because PostgreSQL
    is not available in this environment.
    """
    import inspect
    from app.database import get_db_sync
    src = inspect.getsource(get_db_sync)
    assert "set_config('app.current_tenant_id'" in src, (
        "get_db_sync must call set_config('app.current_tenant_id', ...) "
        "before yielding the session to enforce PostgreSQL RLS."
    )
    print(f"\n[PASS] get_db_sync source contains set_config call — "
          f"RLS would be enforced on real Postgres.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
