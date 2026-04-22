import re
from dataclasses import dataclass, field

from fastapi import HTTPException, status
from sqlglot import exp, parse

from app.core.config import get_settings

COMMENT_PATTERN = re.compile(r"(--|/\*|\*/)")

DIALECT_MAP = {
    "postgresql": "postgres",
    "sqlite": "sqlite",
    "duckdb": "duckdb",
}

MUTATING_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Attach,
    exp.Command,
    exp.Copy,
    exp.Merge,
    exp.TruncateTable,
)


@dataclass
class GuardResult:
    sql: str
    warnings: list[str] = field(default_factory=list)


def _raise_unsafe(message: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def validate_read_only_sql(
    sql: str,
    dialect: str,
    page: int = 1,
    page_size: int = 100,
    apply_row_limit: bool = True,
) -> GuardResult:
    settings = get_settings()
    if not sql.strip():
        _raise_unsafe("SQL is required.")

    stripped = sql.strip()
    if COMMENT_PATTERN.search(stripped):
        _raise_unsafe("Comments are not allowed in v1 queries.")

    try:
        expressions = parse(stripped.rstrip(";"), read=DIALECT_MAP[dialect])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse SQL safely: {exc}",
        ) from exc

    if len(expressions) != 1:
        _raise_unsafe("Multiple statements are not allowed.")

    expression = expressions[0]

    if any(expression.find(node_type) for node_type in MUTATING_NODE_TYPES):
        _raise_unsafe("Only read-only SQL is allowed.")

    if not isinstance(expression, (exp.Select, exp.Union, exp.Except, exp.Intersect)):
        _raise_unsafe("Only SELECT-style queries are allowed in the execute endpoint.")

    effective_page_size = max(1, min(page_size, settings.query_max_rows))
    offset = max(page - 1, 0) * effective_page_size
    warnings: list[str] = []

    if apply_row_limit:
        if not expression.args.get("limit"):
            if not expression.find(exp.Group) and not expression.find(exp.AggFunc):
                expression = expression.limit(effective_page_size)
                warnings.append(f"Applied LIMIT {effective_page_size} for safety.")
        else:
            limit_expression = expression.args.get("limit")
            if limit_expression and isinstance(limit_expression.expression, exp.Literal):
                existing_limit = int(limit_expression.expression.this)
                if existing_limit > settings.query_max_rows:
                    expression = expression.limit(settings.query_max_rows)
                    warnings.append(
                        f"Reduced LIMIT from {existing_limit} to {settings.query_max_rows} to respect max rows."
                    )

        if offset:
            expression = expression.offset(offset)

    return GuardResult(sql=expression.sql(dialect=DIALECT_MAP[dialect]), warnings=warnings)
