from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models import Connection, SchemaCache


class ConnectionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_connections(self) -> list[Connection]:
        stmt = select(Connection).order_by(desc(Connection.updated_at))
        return list(self.db.scalars(stmt).all())

    def get_connection(self, connection_id: str) -> Connection | None:
        stmt = (
            select(Connection)
            .where(Connection.id == connection_id)
            .options(selectinload(Connection.schema_cache))
        )
        return self.db.scalars(stmt).first()

    def save_connection(self, connection: Connection) -> Connection:
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def delete_connection(self, connection: Connection) -> None:
        self.db.delete(connection)
        self.db.commit()

    def upsert_schema_cache(self, connection_id: str, schema_json: dict) -> SchemaCache:
        stmt = select(SchemaCache).where(SchemaCache.connection_id == connection_id)
        cache = self.db.scalars(stmt).first()
        if cache:
            cache.schema_json = schema_json
            cache.refreshed_at = datetime.now(timezone.utc)
        else:
            cache = SchemaCache(connection_id=connection_id, schema_json=schema_json)
            self.db.add(cache)
        self.db.commit()
        self.db.refresh(cache)
        return cache
