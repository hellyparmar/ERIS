"""Small helpers shared by routers."""
from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def paginate(db: Session, query: Select, page: int, page_size: int) -> tuple[list, int]:
    page = max(page, 1)
    page_size = max(1, min(page_size, 500))
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    rows = db.execute(query.limit(page_size).offset((page - 1) * page_size)).all()
    return rows, total


def page_response(items: list, total: int, page: int, page_size: int) -> dict:
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "pages": max(1, -(-total // max(page_size, 1)))}


def get_or_404(db: Session, model, obj_id: int, name: str | None = None):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, f"{name or model.__name__} not found")
    return obj


def csv_response(filename: str, header: list[str], rows: Iterable[list]) -> StreamingResponse:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})
