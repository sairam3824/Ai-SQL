from datetime import UTC, datetime

from app.schemas.schema import SchemaColumn, SchemaIndex, SchemaResponse, SchemaTable
from app.services.index_advisor import advise_indexes


def test_index_advisor_recommends_where_index() -> None:
    schema = SchemaResponse(
        connection_id="1",
        refreshed_at=datetime.now(UTC),
        summary="",
        tables=[
            SchemaTable(
                name="orders",
                schema_name=None,
                columns=[
                    SchemaColumn(name="customer_id", data_type="INTEGER", nullable=False),
                    SchemaColumn(name="created_at", data_type="TIMESTAMP", nullable=False),
                ],
                primary_key=[],
                foreign_keys=[],
                indexes=[SchemaIndex(name="idx_orders_created_at", columns=["created_at"], unique=False)],
                estimated_row_count=10_000,
            )
        ],
    )
    advice = advise_indexes(
        "SELECT * FROM orders WHERE customer_id = 42 ORDER BY created_at DESC",
        "sqlite",
        schema,
    )
    assert advice.suggestions
    assert "customer_id" in advice.suggestions[0].statement
