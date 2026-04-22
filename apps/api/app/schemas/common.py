from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HealthResponse(ApiModel):
    status: str
    timestamp: datetime


class ErrorResponse(ApiModel):
    detail: str


ConfidenceLevel = Literal["high", "medium", "low"]
SeverityLevel = Literal["info", "warning", "high"]


class PaginationRequest(ApiModel):
    page: int = 1
    page_size: int = 100


class JsonObject(ApiModel):
    data: dict[str, Any]
