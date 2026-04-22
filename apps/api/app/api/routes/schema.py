from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_connection_or_404, get_connection_service
from app.db.session import get_db
from app.repositories import ConnectionRepository
from app.schemas.schema import SchemaResponse
from app.services.connection_service import ConnectionService
from app.services.db_runtime import adapter_for_config

router = APIRouter()


@router.get("/connections/{connection_id}/schema", response_model=SchemaResponse)
def get_schema(
    connection=Depends(get_connection_or_404),
    db: Session = Depends(get_db),
    service: ConnectionService = Depends(get_connection_service),
):
    repo = ConnectionRepository(db)
    if connection.schema_cache:
        return SchemaResponse(**connection.schema_cache.schema_json)
    config = service.decrypt_config(connection)
    adapter = adapter_for_config(config)
    schema = adapter.introspect_schema(connection.id)
    repo.upsert_schema_cache(connection.id, schema.model_dump(mode="json"))
    return schema


@router.post("/connections/{connection_id}/schema/refresh", response_model=SchemaResponse)
def refresh_schema(
    connection=Depends(get_connection_or_404),
    db: Session = Depends(get_db),
    service: ConnectionService = Depends(get_connection_service),
):
    repo = ConnectionRepository(db)
    config = service.decrypt_config(connection)
    adapter = adapter_for_config(config)
    schema = adapter.introspect_schema(connection.id)
    repo.upsert_schema_cache(connection.id, schema.model_dump(mode="json"))
    return schema
