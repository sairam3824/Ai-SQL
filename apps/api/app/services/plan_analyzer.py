from typing import Any


def _postgres_walk_plan(node: dict[str, Any], findings: list[dict[str, str]]) -> None:
    node_type = node.get("Node Type", "Operation")
    relation = node.get("Relation Name")
    plan_rows = int(node.get("Plan Rows", 0) or 0)

    if node_type == "Seq Scan" and plan_rows > 1000:
        findings.append(
            {
                "title": f"Sequential scan on {relation or 'table'}",
                "detail": "The planner expects to scan many rows without using an index.",
                "severity": "warning",
            }
        )
    if node_type == "Sort" and plan_rows > 1000:
        findings.append(
            {
                "title": "Large sort step",
                "detail": "Sorting many rows can become expensive, especially without a supporting index.",
                "severity": "warning",
            }
        )
    if node_type == "Nested Loop" and plan_rows > 1000:
        findings.append(
            {
                "title": "Nested loop on a large relation",
                "detail": "Nested loops are efficient for small joins, but can become slow when both sides are large.",
                "severity": "high",
            }
        )

    for child in node.get("Plans", []) or []:
        _postgres_walk_plan(child, findings)


def analyze_plan(dialect: str, raw_plan: Any) -> tuple[str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []

    if dialect == "postgresql" and isinstance(raw_plan, dict):
        plan = raw_plan.get("Plan", raw_plan)
        _postgres_walk_plan(plan, findings)
        total_cost = plan.get("Total Cost")
        summary = f"PostgreSQL plans to use {plan.get('Node Type', 'multiple operators')} with total cost {total_cost}."
        return summary, findings

    if dialect == "sqlite" and isinstance(raw_plan, list):
        details = [str(row.get("detail", "")) for row in raw_plan]
        if any("SCAN" in detail.upper() for detail in details):
            findings.append(
                {
                    "title": "Table scan detected",
                    "detail": "SQLite is scanning a table instead of narrowing the search with an index.",
                    "severity": "warning",
                }
            )
        if any("TEMP B-TREE" in detail.upper() for detail in details):
            findings.append(
                {
                    "title": "Temporary sort structure",
                    "detail": "SQLite had to build a temporary B-tree, often because ORDER BY or GROUP BY is not index-backed.",
                    "severity": "warning",
                }
            )
        summary = "SQLite returned a compact query plan. The key signal is whether it is searching with an index or scanning tables."
        return summary, findings

    if dialect == "duckdb" and isinstance(raw_plan, str):
        upper = raw_plan.upper()
        if "SEQ_SCAN" in upper:
            findings.append(
                {
                    "title": "Sequential scan detected",
                    "detail": "DuckDB is reading a full table or large chunk of it, which may be expected for analytics but can still be a hotspot.",
                    "severity": "warning",
                }
            )
        if "ORDER_BY" in upper:
            findings.append(
                {
                    "title": "Sort in execution plan",
                    "detail": "A sort operator appears in the plan and may dominate runtime on larger result sets.",
                    "severity": "info",
                }
            )
        summary = "DuckDB produced a physical plan. Scan and sort operators are usually the best first clues for bottlenecks."
        return summary, findings

    return "Plan analysis is available, but this plan shape did not match the current parser.", findings
