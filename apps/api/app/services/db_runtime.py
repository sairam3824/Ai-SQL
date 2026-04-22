import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote

import duckdb
import psycopg
from fastapi import HTTPException, status
from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings
from app.schemas.schema import (
    SchemaColumn,
    SchemaForeignKey,
    SchemaIndex,
    SchemaResponse,
    SchemaTable,
)
from app.services.schema_summary import build_schema_summary

logger = logging.getLogger(__name__)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _safe_table_name(schema_name: str | None, table_name: str) -> str:
    return f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'


@dataclass
class RuntimeQueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    execution_time_ms: float
    truncated: bool
    row_count: int


class BaseAdapter:
    dialect: str

    def test_connection(self) -> str:
        raise NotImplementedError

    def introspect_schema(self, connection_id: str) -> SchemaResponse:
        raise NotImplementedError

    def execute_query(self, sql: str, max_rows: int) -> RuntimeQueryResult:
        raise NotImplementedError

    def explain_query(self, sql: str, analyze: bool) -> Any:
        raise NotImplementedError


class PostgresAdapter(BaseAdapter):
    dialect = "postgresql"

    def __init__(self, config: dict[str, Any]) -> None:
        sslmode = "require" if config.get("ssl") else "prefer"
        user = quote(str(config["user"]), safe="")
        password = quote(str(config["password"]), safe="")
        host = config["host"]
        port = config["port"]
        database = config["database"]
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
        self.engine = create_engine(
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}",
            future=True,
        )

    def test_connection(self) -> str:
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database()")
                database = cur.fetchone()[0]
        return f"Connected to PostgreSQL database {database}"

    def introspect_schema(self, connection_id: str) -> SchemaResponse:
        inspector = inspect(self.engine)
        tables: list[SchemaTable] = []
        schemas = [name for name in inspector.get_schema_names() if not name.startswith("pg_") and name != "information_schema"]

        with self.engine.connect() as conn:
            for schema_name in schemas:
                for table_name in inspector.get_table_names(schema=schema_name):
                    columns = [
                        SchemaColumn(
                            name=column["name"],
                            data_type=str(column["type"]),
                            nullable=bool(column["nullable"]),
                            default_value=str(column.get("default")) if column.get("default") is not None else None,
                        )
                        for column in inspector.get_columns(table_name, schema=schema_name)
                    ]
                    pk = inspector.get_pk_constraint(table_name, schema=schema_name).get("constrained_columns", []) or []
                    fks = [
                        SchemaForeignKey(
                            constrained_columns=fk.get("constrained_columns", []),
                            referred_table=f"{fk.get('referred_schema') + '.' if fk.get('referred_schema') else ''}{fk.get('referred_table')}",
                            referred_columns=fk.get("referred_columns", []),
                        )
                        for fk in inspector.get_foreign_keys(table_name, schema=schema_name)
                    ]
                    indexes = [
                        SchemaIndex(
                            name=index["name"],
                            columns=index.get("column_names", []),
                            unique=bool(index.get("unique")),
                        )
                        for index in inspector.get_indexes(table_name, schema=schema_name)
                    ]
                    estimate = conn.execute(
                        text(
                            """
                            SELECT reltuples::bigint
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE n.nspname = :schema_name AND c.relname = :table_name
                            """
                        ),
                        {"schema_name": schema_name, "table_name": table_name},
                    ).scalar_one_or_none()
                    tables.append(
                        SchemaTable(
                            name=table_name,
                            schema_name=schema_name,
                            columns=columns,
                            primary_key=pk,
                            foreign_keys=fks,
                            indexes=indexes,
                            estimated_row_count=int(estimate) if estimate is not None else None,
                        )
                    )

        response = SchemaResponse(connection_id=connection_id, refreshed_at=datetime.now(UTC), summary="", tables=tables)
        response.summary = build_schema_summary(response)
        return response

    def execute_query(self, sql: str, max_rows: int) -> RuntimeQueryResult:
        settings = get_settings()
        started = time.perf_counter()
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET statement_timeout TO {settings.query_timeout_seconds * 1000}")
                cur.execute(sql)
                rows = cur.fetchmany(max_rows + 1)
                columns = [desc.name for desc in cur.description] if cur.description else []
        execution_time_ms = (time.perf_counter() - started) * 1000
        truncated = len(rows) > max_rows
        serialized_rows = [
            {col: _serialize_value(val) for col, val in zip(columns, row)}
            for row in rows[:max_rows]
        ]
        return RuntimeQueryResult(
            columns=columns,
            rows=serialized_rows,
            execution_time_ms=execution_time_ms,
            truncated=truncated,
            row_count=len(serialized_rows),
        )

    def explain_query(self, sql: str, analyze: bool) -> Any:
        prefix = "EXPLAIN (FORMAT JSON, ANALYZE TRUE)" if analyze else "EXPLAIN (FORMAT JSON)"
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(f"{prefix} {sql}")
                row = cur.fetchone()
        if not row:
            return {}
        return row[0][0] if isinstance(row[0], list) else row[0]


class SQLiteAdapter(BaseAdapter):
    dialect = "sqlite"

    def __init__(self, config: dict[str, Any]) -> None:
        self.path = config["path"]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    def test_connection(self) -> str:
        if not Path(self.path).exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SQLite file does not exist.")
        with self._connect() as conn:
            conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
        return f"Connected to SQLite database {Path(self.path).name}"

    def introspect_schema(self, connection_id: str) -> SchemaResponse:
        tables: list[SchemaTable] = []
        with self._connect() as conn:
            table_rows = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
            for table_row in table_rows:
                table_name = table_row["name"]
                columns = [
                    SchemaColumn(
                        name=row["name"],
                        data_type=row["type"] or "TEXT",
                        nullable=not bool(row["notnull"]),
                        default_value=row["dflt_value"],
                    )
                    for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
                ]
                primary_key = [
                    row["name"]
                    for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
                    if row["pk"]
                ]
                foreign_keys = [
                    SchemaForeignKey(
                        constrained_columns=[row["from"]],
                        referred_table=row["table"],
                        referred_columns=[row["to"]],
                    )
                    for row in conn.execute(f'PRAGMA foreign_key_list("{table_name}")').fetchall()
                ]
                indexes = []
                for index_row in conn.execute(f'PRAGMA index_list("{table_name}")').fetchall():
                    info_rows = conn.execute(f'PRAGMA index_info("{index_row["name"]}")').fetchall()
                    indexes.append(
                        SchemaIndex(
                            name=index_row["name"],
                            columns=[info["name"] for info in info_rows],
                            unique=bool(index_row["unique"]),
                        )
                    )
                estimate = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                tables.append(
                    SchemaTable(
                        name=table_name,
                        schema_name=None,
                        columns=columns,
                        primary_key=primary_key,
                        foreign_keys=foreign_keys,
                        indexes=indexes,
                        estimated_row_count=int(estimate),
                    )
                )

        response = SchemaResponse(connection_id=connection_id, refreshed_at=datetime.now(UTC), summary="", tables=tables)
        response.summary = build_schema_summary(response)
        return response

    def execute_query(self, sql: str, max_rows: int) -> RuntimeQueryResult:
        settings = get_settings()
        started = time.perf_counter()
        with self._connect() as conn:
            deadline = started + settings.query_timeout_seconds

            def progress_handler() -> int:
                return 1 if time.perf_counter() > deadline else 0

            conn.set_progress_handler(progress_handler, 10000)
            try:
                cursor = conn.execute(sql)
                rows = cursor.fetchmany(max_rows + 1)
            except sqlite3.OperationalError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            finally:
                conn.set_progress_handler(None, 0)

        execution_time_ms = (time.perf_counter() - started) * 1000
        columns = [column[0] for column in cursor.description] if cursor.description else []
        serialized_rows = [{columns[index]: _serialize_value(value) for index, value in enumerate(row)} for row in rows[:max_rows]]
        return RuntimeQueryResult(
            columns=columns,
            rows=serialized_rows,
            execution_time_ms=execution_time_ms,
            truncated=len(rows) > max_rows,
            row_count=len(serialized_rows),
        )

    def explain_query(self, sql: str, analyze: bool) -> Any:
        with self._connect() as conn:
            rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()
        return [dict(row) for row in rows]


class DuckDBAdapter(BaseAdapter):
    dialect = "duckdb"

    def __init__(self, config: dict[str, Any]) -> None:
        self.path = config["path"]

    def _connect(self, read_only: bool = True) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.path, read_only=read_only)

    def test_connection(self) -> str:
        if not Path(self.path).exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DuckDB file does not exist.")
        with self._connect() as conn:
            conn.execute("SHOW TABLES").fetchall()
        return f"Connected to DuckDB database {Path(self.path).name}"

    def introspect_schema(self, connection_id: str) -> SchemaResponse:
        tables: list[SchemaTable] = []
        with self._connect() as conn:
            table_rows = conn.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY table_schema, table_name
                """
            ).fetchall()

            index_lookup: dict[tuple[str, str], list[SchemaIndex]] = {}
            try:
                index_rows = conn.execute(
                    """
                    SELECT schema_name, table_name, index_name, expressions, is_unique
                    FROM duckdb_indexes()
                    """
                ).fetchall()
                for schema_name, table_name, index_name, expressions, is_unique in index_rows:
                    index_lookup.setdefault((schema_name, table_name), []).append(
                        SchemaIndex(
                            name=index_name,
                            columns=[expr.strip() for expr in str(expressions).split(",")],
                            unique=bool(is_unique),
                        )
                    )
            except Exception:
                index_lookup = {}

            constraint_lookup: dict[tuple[str, str], dict[str, list]] = {}
            try:
                constraint_rows = conn.execute(
                    """
                    SELECT schema_name, table_name, constraint_type, constraint_column_names,
                           referenced_table, referenced_column_names
                    FROM duckdb_constraints()
                    """
                ).fetchall()
                for row in constraint_rows:
                    info = constraint_lookup.setdefault((row[0], row[1]), {"pk": [], "fk": []})
                    try:
                        columns = json.loads(row[3]) if isinstance(row[3], str) and row[3].startswith("[") else row[3]
                    except (json.JSONDecodeError, TypeError):
                        columns = row[3]
                    columns = columns if isinstance(columns, list) else [columns]
                    if row[2] == "PRIMARY KEY":
                        info["pk"] = columns
                    if row[2] == "FOREIGN KEY":
                        try:
                            referenced_columns = (
                                json.loads(row[5]) if isinstance(row[5], str) and row[5].startswith("[") else row[5]
                            )
                        except (json.JSONDecodeError, TypeError):
                            referenced_columns = row[5]
                        info["fk"].append(
                            SchemaForeignKey(
                                constrained_columns=columns,
                                referred_table=str(row[4]),
                                referred_columns=referenced_columns if isinstance(referenced_columns, list) else [referenced_columns],
                            )
                        )
            except Exception:
                constraint_lookup = {}

            for schema_name, table_name in table_rows:
                column_rows = conn.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = ? AND table_name = ?
                    ORDER BY ordinal_position
                    """,
                    [schema_name, table_name],
                ).fetchall()
                columns = [
                    SchemaColumn(
                        name=row[0],
                        data_type=row[1],
                        nullable=row[2] == "YES",
                        default_value=str(row[3]) if row[3] is not None else None,
                    )
                    for row in column_rows
                ]
                estimate = conn.execute(f"SELECT COUNT(*) FROM {_safe_table_name(schema_name, table_name)}").fetchone()[0]
                constraints = constraint_lookup.get((schema_name, table_name), {"pk": [], "fk": []})
                tables.append(
                    SchemaTable(
                        name=table_name,
                        schema_name=schema_name,
                        columns=columns,
                        primary_key=constraints.get("pk", []),
                        foreign_keys=constraints.get("fk", []),
                        indexes=index_lookup.get((schema_name, table_name), []),
                        estimated_row_count=int(estimate),
                    )
                )

        response = SchemaResponse(connection_id=connection_id, refreshed_at=datetime.now(UTC), summary="", tables=tables)
        response.summary = build_schema_summary(response)
        return response

    def execute_query(self, sql: str, max_rows: int) -> RuntimeQueryResult:
        started = time.perf_counter()
        with self._connect() as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(max_rows + 1)
            columns = [column[0] for column in cursor.description] if cursor.description else []
        execution_time_ms = (time.perf_counter() - started) * 1000
        serialized_rows = [{columns[index]: _serialize_value(value) for index, value in enumerate(row)} for row in rows[:max_rows]]
        return RuntimeQueryResult(
            columns=columns,
            rows=serialized_rows,
            execution_time_ms=execution_time_ms,
            truncated=len(rows) > max_rows,
            row_count=len(serialized_rows),
        )

    def explain_query(self, sql: str, analyze: bool) -> Any:
        prefix = "EXPLAIN ANALYZE" if analyze else "EXPLAIN"
        with self._connect() as conn:
            rows = conn.execute(f"{prefix} {sql}").fetchall()
        return "\n".join(str(row[0]) for row in rows)


def adapter_for_config(config: dict[str, Any]) -> BaseAdapter:
    database_type = config["type"]
    if database_type == "postgresql":
        return PostgresAdapter(config)
    if database_type == "sqlite":
        return SQLiteAdapter(config)
    if database_type == "duckdb":
        return DuckDBAdapter(config)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported database type: {database_type}")


def remove_file_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        return
