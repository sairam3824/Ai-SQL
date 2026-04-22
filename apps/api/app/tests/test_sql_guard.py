import pytest
from fastapi import HTTPException

from app.services.sql_guard import validate_read_only_sql


def test_sql_guard_blocks_delete() -> None:
    with pytest.raises(HTTPException):
        validate_read_only_sql("DELETE FROM customers", "sqlite")


def test_sql_guard_applies_limit() -> None:
    result = validate_read_only_sql("SELECT * FROM customers", "sqlite", page=1, page_size=50)
    assert "LIMIT 50" in result.sql.upper()


def test_sql_guard_blocks_multiple_statements() -> None:
    with pytest.raises(HTTPException):
        validate_read_only_sql("SELECT * FROM customers; DROP TABLE customers;", "sqlite")


def test_sql_guard_allows_blocked_words_inside_string_literals() -> None:
    result = validate_read_only_sql("SELECT 'drop' AS note", "sqlite")
    assert "SELECT 'drop' AS note".lower() in result.sql.lower()


def test_sql_guard_can_preserve_original_sql_for_explain() -> None:
    result = validate_read_only_sql("SELECT * FROM customers", "sqlite", apply_row_limit=False)
    assert "LIMIT" not in result.sql.upper()
