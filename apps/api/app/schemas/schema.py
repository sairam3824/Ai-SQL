from datetime import datetime

from pydantic import Field

from app.schemas.common import ApiModel


class SchemaColumn(ApiModel):
    name: str
    data_type: str
    nullable: bool
    default_value: str | None = None


class SchemaIndex(ApiModel):
    name: str
    columns: list[str]
    unique: bool


class SchemaForeignKey(ApiModel):
    constrained_columns: list[str]
    referred_table: str
    referred_columns: list[str]


class SchemaTable(ApiModel):
    name: str
    schema_name: str | None = Field(default=None, alias="schema", serialization_alias="schema")
    columns: list[SchemaColumn]
    primary_key: list[str]
    foreign_keys: list[SchemaForeignKey]
    indexes: list[SchemaIndex]
    estimated_row_count: int | None = None


class SchemaResponse(ApiModel):
    connection_id: str
    refreshed_at: datetime
    summary: str
    tables: list[SchemaTable]
