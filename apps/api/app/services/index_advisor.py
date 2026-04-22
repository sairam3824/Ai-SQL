from collections import defaultdict
from typing import Any

from sqlglot import exp, parse_one

from app.schemas.chat import IndexAdviceResponse, IndexSuggestion
from app.schemas.schema import SchemaResponse

DIALECT_MAP = {"postgresql": "postgres", "sqlite": "sqlite", "duckdb": "duckdb"}


def _alias_map(expression: exp.Expression) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for table in expression.find_all(exp.Table):
        actual = table.name
        alias = table.alias_or_name
        mapping[alias] = actual
        mapping[actual] = actual
    return mapping


def _extract_columns(node: exp.Expression | None, alias_lookup: dict[str, str], fallback_table: str | None = None) -> dict[str, list[str]]:
    columns: dict[str, list[str]] = defaultdict(list)
    if node is None:
        return columns
    for column in node.find_all(exp.Column):
        table_name = alias_lookup.get(column.table or "", fallback_table or "")
        if not table_name or not column.name:
            continue
        if column.name not in columns[table_name]:
            columns[table_name].append(column.name)
    return columns


def _has_similar_index(existing_indexes: list[list[str]], candidate: list[str]) -> bool:
    candidate_lower = [column.lower() for column in candidate]
    return any([column.lower() for column in index[: len(candidate_lower)]] == candidate_lower for index in existing_indexes)


def advise_indexes(sql: str, dialect: str, schema: SchemaResponse) -> IndexAdviceResponse:
    expression = parse_one(sql, read=DIALECT_MAP[dialect])
    alias_lookup = _alias_map(expression)
    single_table = next(iter(alias_lookup.values()), None)

    where_columns = _extract_columns(expression.args.get("where"), alias_lookup, single_table)
    group_columns = _extract_columns(expression.args.get("group"), alias_lookup, single_table)
    order_columns = _extract_columns(expression.args.get("order"), alias_lookup, single_table)

    join_columns: dict[str, list[str]] = defaultdict(list)
    for join in expression.find_all(exp.Join):
        join_bits = _extract_columns(join.args.get("on"), alias_lookup, single_table)
        for table_name, columns in join_bits.items():
            for column in columns:
                if column not in join_columns[table_name]:
                    join_columns[table_name].append(column)

    suggestions: list[IndexSuggestion] = []
    tables_by_name = {table.name: table for table in schema.tables}

    for table_name, table in tables_by_name.items():
        candidate_columns = []
        if where_columns.get(table_name):
            candidate_columns.extend(where_columns[table_name])
        if join_columns.get(table_name):
            candidate_columns.extend([col for col in join_columns[table_name] if col not in candidate_columns])
        if order_columns.get(table_name):
            candidate_columns.extend([col for col in order_columns[table_name] if col not in candidate_columns])
        if group_columns.get(table_name) and not candidate_columns:
            candidate_columns.extend(group_columns[table_name])

        if not candidate_columns:
            continue

        existing_indexes = [index.columns for index in table.indexes]
        if _has_similar_index(existing_indexes, candidate_columns):
            continue

        index_name = f"idx_{table.name}_{'_'.join(candidate_columns[:3])}"
        quoted_columns = ", ".join(f'"{col}"' for col in candidate_columns)
        statement = f'CREATE INDEX "{index_name}" ON "{table.name}" ({quoted_columns});'
        suggestions.append(
            IndexSuggestion(
                summary=f"Consider indexing {table.name} on {', '.join(candidate_columns)}",
                rationale="These columns appear in filters, joins, or ordering clauses and are not covered by an existing index prefix.",
                statement=statement,
                confidence="medium" if len(candidate_columns) > 2 else "high",
                tradeoffs=[
                    "Improves read performance for matching query patterns.",
                    "Adds write overhead when rows are inserted or updated.",
                    "Consumes extra storage and may be redundant if workloads change.",
                ],
            )
        )

    overview = (
        "No obvious index gaps were found from the query shape and known indexes."
        if not suggestions
        else "These conservative index candidates are based on WHERE, JOIN, ORDER BY, and GROUP BY usage."
    )
    return IndexAdviceResponse(overview=overview, suggestions=suggestions)
