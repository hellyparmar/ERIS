"""Safe executor for the AI assistant's pre-approved SELECT templates."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import logging
import time
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class QueryExecutor:
    def execute_template_query_with_session(
        self,
        template_sql: str,
        semantic_layer,
        db: Session,
        params: Optional[dict[str, Any]] = None,
        max_rows: int = 100,
    ) -> dict[str, Any]:
        is_valid, issues = semantic_layer.validate_sql(template_sql)
        if not is_valid:
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": 0,
                "error": issues[0]["message"],
                "validation_issues": issues,
            }

        started = time.perf_counter()
        try:
            rows = db.execute(text(template_sql), params or {}).fetchmany(max_rows)
            data = [self._serialize_row(dict(row._mapping)) for row in rows]
            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "execution_time_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": None,
                "validation_issues": issues,
            }
        except SQLAlchemyError:
            logger.exception("A pre-approved AI grounding query failed")
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "execution_time_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": "Grounding query could not be executed",
                "validation_issues": issues,
            }

    @staticmethod
    def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                serialized[key] = value.isoformat()
            elif isinstance(value, Decimal):
                serialized[key] = float(value)
            elif isinstance(value, (int, float, str, bool, type(None))):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        return serialized

    @staticmethod
    def format_results_for_llm(query_result: dict[str, Any], max_rows: int = 20) -> str:
        data = query_result.get("data", [])[:max_rows]
        if not data:
            return "The verified query returned no rows."
        lines = [f"Verified rows returned: {query_result.get('row_count', len(data))}"]
        for index, row in enumerate(data, 1):
            values = " | ".join(f"{key}: {value}" for key, value in row.items())
            lines.append(f"{index}. {values}")
        return "\n".join(lines)


query_executor = QueryExecutor()
