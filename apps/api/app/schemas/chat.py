from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.schemas.common import ApiModel, ConfidenceLevel, SeverityLevel


class GenerateSqlRequest(ApiModel):
    question: str = Field(min_length=2)
    session_id: str | None = None


class ExecuteSqlRequest(ApiModel):
    sql: str = Field(min_length=1)
    page: int = Field(1, ge=1)
    page_size: int = Field(100, ge=1, le=1000)


class ExplainRequest(ApiModel):
    sql: str = Field(min_length=1)
    analyze: bool = False


class AdviseIndexesRequest(ApiModel):
    sql: str = Field(min_length=1)


class ChatMessageResponse(ApiModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    generated_sql: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class ChatSessionCreateRequest(ApiModel):
    title: str | None = None


class ChatSessionResponse(ApiModel):
    id: str
    connection_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []


class SessionSummary(ApiModel):
    id: str
    connection_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message: ChatMessageResponse | None = None


class SqlGenerationResponse(ApiModel):
    session_id: str
    sql: str
    explanation: str
    assumptions: list[str]
    warnings: list[str]
    visualization_suggestion: str | None = None
    confidence: ConfidenceLevel


class QueryResultResponse(ApiModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool
    page: int
    page_size: int
    chart_recommendation: str | None = None


class PlanInsight(ApiModel):
    title: str
    detail: str
    severity: SeverityLevel


class ExplainResponse(ApiModel):
    dialect: str
    raw_plan: Any
    summary: str
    insights: list[PlanInsight]


class IndexSuggestion(ApiModel):
    summary: str
    rationale: str
    statement: str
    confidence: ConfidenceLevel
    tradeoffs: list[str]


class IndexAdviceResponse(ApiModel):
    overview: str
    suggestions: list[IndexSuggestion]
