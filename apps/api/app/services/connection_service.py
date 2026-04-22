import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.security import ConfigCipher, redact_config
from app.models import Connection
from app.schemas.connections import ConnectionDetail, ConnectionSummary, ConnectionTestResponse
from app.services.db_runtime import adapter_for_config, remove_file_if_exists

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB


class ConnectionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.cipher = ConfigCipher()

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Strip path traversal and dangerous characters from user-supplied filenames."""
        safe = os.path.basename(filename).replace("..", "_").replace("/", "_").replace("\\", "_")
        return safe or "database.bin"

    def _save_upload(self, upload: UploadFile, target_dir: Path) -> str:
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._sanitize_filename(upload.filename or "database.bin")
        target_path = target_dir / safe_name
        with target_path.open("wb") as output:
            shutil.copyfileobj(upload.file, output)
        return str(target_path)

    def _build_config(
        self,
        connection_type: str,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        ssl: bool = False,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        if connection_type == "postgresql":
            if not all([host, port, database, username]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing PostgreSQL connection fields.")
            if port is not None and not (1 <= port <= 65535):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Port must be between 1 and 65535.")
            return {
                "type": connection_type,
                "host": host,
                "port": port,
                "database": database,
                "user": username,
                "password": password or "",
                "ssl": ssl,
            }
        if connection_type in {"sqlite", "duckdb"}:
            if not file_path:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A database file is required.")
            return {"type": connection_type, "path": file_path}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported database type.")

    def test_connection(self, config: dict[str, Any]) -> ConnectionTestResponse:
        adapter = adapter_for_config(config)
        message = adapter.test_connection()
        return ConnectionTestResponse(
            ok=True,
            message=message,
            inferred_name=Path(config.get("path", config.get("database", "connection"))).stem,
            config_summary=redact_config(config),
        )

    def create_duckdb_file(self, name: str) -> str:
        import duckdb

        target_dir = self.settings.uploads_dir / "duckdb"
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = name.replace(" ", "_").lower()
        path = target_dir / f"{safe_name}.duckdb"
        duckdb.connect(str(path)).close()
        return str(path)

    def prepare_uploaded_file(
        self,
        connection_type: str,
        upload: UploadFile | None,
        connection_name: str,
        create_duckdb: bool = False,
    ) -> str | None:
        if upload and upload.filename:
            target_dir = self.settings.uploads_dir / connection_type / connection_name.replace(" ", "_")
            return self._save_upload(upload, target_dir)
        if connection_type == "duckdb" and create_duckdb:
            return self.create_duckdb_file(connection_name)
        return None

    def create_connection_record(self, name: str, config: dict[str, Any], status_message: str) -> Connection:
        return Connection(
            name=name,
            type=config["type"],
            encrypted_config=self.cipher.encrypt_json(config),
            status="connected",
            status_message=status_message,
        )

    def decrypt_config(self, connection: Connection) -> dict[str, Any]:
        payload = self.cipher.decrypt_json(connection.encrypted_config)
        payload["type"] = connection.type
        return payload

    def to_summary(self, connection: Connection) -> ConnectionSummary:
        payload = self.decrypt_config(connection)
        return ConnectionSummary(
            id=connection.id,
            name=connection.name,
            type=connection.type,
            status=connection.status,
            status_message=connection.status_message,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
            config_summary=redact_config(payload),
        )

    def to_detail(self, connection: Connection) -> ConnectionDetail:
        summary = self.to_summary(connection)
        return ConnectionDetail(
            **summary.model_dump(),
            schema_cached_at=connection.schema_cache.refreshed_at if connection.schema_cache else None,
        )

    def build_temp_file_config(
        self,
        connection_type: str,
        upload: UploadFile,
        connection_name: str,
    ) -> tuple[dict[str, Any], str]:
        suffix = Path(upload.filename or connection_name).suffix or (".duckdb" if connection_type == "duckdb" else ".db")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        with temp_file:
            shutil.copyfileobj(upload.file, temp_file)
        config = self._build_config(connection_type=connection_type, file_path=temp_file.name)
        return config, temp_file.name

    def cleanup_temp_file(self, path: str | None) -> None:
        if path:
            remove_file_if_exists(path)
