import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_connection_or_404, get_connection_service
from app.core.config import get_settings
from app.db.session import get_db
from app.repositories import ChatRepository, ConnectionRepository

logger = logging.getLogger(__name__)
from app.schemas.chat import (
    AdviseIndexesRequest,
    ExecuteSqlRequest,
    ExplainRequest,
    ExplainResponse,
    GenerateSqlRequest,
    IndexAdviceResponse,
    QueryResultResponse,
    SqlGenerationResponse,
)
from app.schemas.schema import SchemaResponse
from app.services.chart_advisor import infer_chart_type
from app.services.chat_service import get_or_create_session
from app.services.connection_service import ConnectionService
from app.services.db_runtime import adapter_for_config
from app.services.index_advisor import advise_indexes
from app.services.plan_analyzer import analyze_plan
from app.services.sql_generation import SqlGenerationService
from app.services.sql_guard import validate_read_only_sql

router = APIRouter()


@router.post("/connections/{connection_id}/generate-sql", response_model=SqlGenerationResponse)
async def generate_sql(
    payload: GenerateSqlRequest,
    connection=Depends(get_connection_or_404),
    db: Session = Depends(get_db),
    service: ConnectionService = Depends(get_connection_service),
):
    connection_repo = ConnectionRepository(db)
    chat_repo = ChatRepository(db)
    session = get_or_create_session(chat_repo, connection.id, payload.session_id, payload.question)
    chat_repo.add_message(session.id, "user", payload.question)

    schema_json = connection.schema_cache.schema_json if connection.schema_cache else None
    if not schema_json:
        schema = adapter_for_config(service.decrypt_config(connection)).introspect_schema(connection.id)
        schema_json = connection_repo.upsert_schema_cache(connection.id, schema.model_dump(mode="json")).schema_json
    schema_response = SchemaResponse(**schema_json)
    session_detail = chat_repo.get_session(session.id)
    chat_context = [
        {"role": message.role, "content": message.content, "generated_sql": message.generated_sql}
        for message in session_detail.messages
    ]
    generator = SqlGenerationService()
    result = await generator.generate(
        dialect=connection.type,
        schema=schema_response,
        question=payload.question,
        chat_context=chat_context,
        session_id=session.id,
    )
    try:
        validate_read_only_sql(result.sql, connection.type, apply_row_limit=False)
    except Exception as exc:
        detail = getattr(exc, "detail", str(exc))
        result.warnings.append(f"Generated SQL did not pass the safety guard: {detail}")
    chat_repo.add_message(
        session.id,
        "assistant",
        result.explanation,
        generated_sql=result.sql,
        metadata_json={
            "assumptions": result.assumptions,
            "warnings": result.warnings,
            "visualization_suggestion": result.visualization_suggestion,
            "confidence": result.confidence,
        },
    )
    return result


@router.post("/connections/{connection_id}/execute", response_model=QueryResultResponse)
def execute_sql(
    payload: ExecuteSqlRequest,
    connection=Depends(get_connection_or_404),
    service: ConnectionService = Depends(get_connection_service),
):
    settings = get_settings()
    config = service.decrypt_config(connection)
    guard = validate_read_only_sql(payload.sql, connection.type, page=payload.page, page_size=payload.page_size)
    adapter = adapter_for_config(config)
    result = adapter.execute_query(guard.sql, settings.query_max_rows)
    chart = infer_chart_type(result.columns, result.rows)
    return QueryResultResponse(
        columns=result.columns,
        rows=result.rows,
        row_count=result.row_count,
        execution_time_ms=result.execution_time_ms,
        truncated=result.truncated,
        page=payload.page,
        page_size=payload.page_size,
        chart_recommendation=chart,
    )


@router.post("/connections/{connection_id}/explain", response_model=ExplainResponse)
def explain_sql(
    payload: ExplainRequest,
    connection=Depends(get_connection_or_404),
    service: ConnectionService = Depends(get_connection_service),
):
    guard = validate_read_only_sql(payload.sql, connection.type, apply_row_limit=False)
    adapter = adapter_for_config(service.decrypt_config(connection))
    raw_plan = adapter.explain_query(guard.sql, payload.analyze)
    summary, insights = analyze_plan(connection.type, raw_plan)
    return ExplainResponse(dialect=connection.type, raw_plan=raw_plan, summary=summary, insights=insights)


@router.post("/connections/{connection_id}/advise-indexes", response_model=IndexAdviceResponse)
def advise_query_indexes(
    payload: AdviseIndexesRequest,
    connection=Depends(get_connection_or_404),
    db: Session = Depends(get_db),
    service: ConnectionService = Depends(get_connection_service),
):
    guard = validate_read_only_sql(payload.sql, connection.type, apply_row_limit=False)
    repo = ConnectionRepository(db)
    if not connection.schema_cache:
        config = service.decrypt_config(connection)
        schema = adapter_for_config(config).introspect_schema(connection.id)
        repo.upsert_schema_cache(connection.id, schema.model_dump(mode="json"))
        connection = repo.get_connection(connection.id)
    schema_response = SchemaResponse(**connection.schema_cache.schema_json)
    return advise_indexes(guard.sql, connection.type, schema_response)
