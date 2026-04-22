from datetime import UTC, datetime

from app.schemas.schema import SchemaColumn, SchemaResponse, SchemaTable
from app.services.schema_summary import build_schema_summary


def test_schema_summary_contains_key_details() -> None:
    schema = SchemaResponse(
        connection_id="1",
        refreshed_at=datetime.now(UTC),
        summary="",
        tables=[
            SchemaTable(
                name="orders",
                schema_name=None,
                columns=[
                    SchemaColumn(name="id", data_type="INTEGER", nullable=False),
                    SchemaColumn(name="customer_id", data_type="INTEGER", nullable=False),
                ],
                primary_key=["id"],
                foreign_keys=[],
                indexes=[],
                estimated_row_count=1024,
            )
        ],
    )
    summary = build_schema_summary(schema)
    assert "orders" in summary
    assert "customer_id" in summary
    assert "1024" in summary
