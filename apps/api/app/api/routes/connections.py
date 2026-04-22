import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.deps import get_connection_or_404, get_connection_service
from app.db.session import get_db
from app.repositories import ConnectionRepository
from app.schemas.common import HealthResponse
from app.schemas.connections import ConnectionDeleteResponse, ConnectionDetail, ConnectionSummary, ConnectionTestResponse
from app.services.connection_service import ConnectionService
from app.services.db_runtime import adapter_for_config

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


@router.get("/connections", response_model=list[ConnectionSummary])
def list_connections(db: Session = Depends(get_db), service: ConnectionService = Depends(get_connection_service)):
    repo = ConnectionRepository(db)
    return [service.to_summary(connection) for connection in repo.list_connections()]


@router.get("/connections/{connection_id}", response_model=ConnectionDetail)
def get_connection(
    connection=Depends(get_connection_or_404),
    service: ConnectionService = Depends(get_connection_service),
):
    return service.to_detail(connection)


@router.post("/connections/test", response_model=ConnectionTestResponse)
async def test_connection(
    type: str = Form(...),
    name: str = Form("Untitled connection"),
    host: str | None = Form(None),
    port: int | None = Form(None),
    database: str | None = Form(None),
    username: str | None = Form(None),
    password: str | None = Form(None),
    ssl: bool = Form(False),
    create_duckdb: bool = Form(False),
    file: UploadFile | None = File(None),
    service: ConnectionService = Depends(get_connection_service),
):
    temp_file_path: str | None = None
    try:
        if type == "postgresql":
            config = service._build_config(type, host, port, database, username, password, ssl=ssl)
        else:
            if file:
                config, temp_file_path = service.build_temp_file_config(type, file, name)
            else:
                file_path = service.prepare_uploaded_file(type, None, name, create_duckdb=create_duckdb)
                config = service._build_config(type, file_path=file_path)
        return service.test_connection(config)
    finally:
        service.cleanup_temp_file(temp_file_path)


@router.post("/connections", response_model=ConnectionDetail)
async def create_connection(
    type: str = Form(...),
    name: str = Form(...),
    host: str | None = Form(None),
    port: int | None = Form(None),
    database: str | None = Form(None),
    username: str | None = Form(None),
    password: str | None = Form(None),
    ssl: bool = Form(False),
    create_duckdb: bool = Form(False),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    service: ConnectionService = Depends(get_connection_service),
):
    repo = ConnectionRepository(db)
    if type == "postgresql":
        config = service._build_config(type, host, port, database, username, password, ssl=ssl)
    else:
        file_path = service.prepare_uploaded_file(type, file, name, create_duckdb=create_duckdb)
        config = service._build_config(type, file_path=file_path)

    test_result = service.test_connection(config)
    record = service.create_connection_record(name=name, config=config, status_message=test_result.message)
    saved = repo.save_connection(record)

    adapter = adapter_for_config(config)
    schema = adapter.introspect_schema(saved.id)
    repo.upsert_schema_cache(saved.id, schema.model_dump(mode="json"))
    refreshed = repo.get_connection(saved.id)
    return service.to_detail(refreshed)


@router.delete("/connections/{connection_id}", response_model=ConnectionDeleteResponse)
def delete_connection(connection=Depends(get_connection_or_404), db: Session = Depends(get_db)):
    repo = ConnectionRepository(db)
    repo.delete_connection(connection)
    return ConnectionDeleteResponse(ok=True)
