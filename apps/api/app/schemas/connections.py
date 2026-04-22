from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import ApiModel


ConnectionType = Literal["postgresql", "sqlite", "duckdb"]


class ConnectionSummary(ApiModel):
    id: str
    name: str
    type: ConnectionType
    status: str
    status_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    config_summary: dict[str, Any]


class ConnectionDetail(ConnectionSummary):
    schema_cached_at: datetime | None = None


class ConnectionTestResponse(ApiModel):
    ok: bool
    message: str
    inferred_name: str | None = None
    config_summary: dict[str, Any]


class ConnectionDeleteResponse(ApiModel):
    ok: bool
