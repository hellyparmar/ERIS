"""Shared response schemas for CSV data sources and imports."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    rows_processed: int
    validation_errors: list[str] = Field(default_factory=list)
    status: str


class DataSource(BaseModel):
    name: str
    type: str
    last_updated: Optional[datetime] = None
    row_count: int


class DataSourcesResponse(BaseModel):
    sources: list[DataSource]
