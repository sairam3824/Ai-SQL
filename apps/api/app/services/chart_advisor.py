from datetime import datetime
from typing import Any


def _looks_like_date(value: Any) -> bool:
    if isinstance(value, datetime):
        return True
    if isinstance(value, str):
        normalized = value.replace("T", " ")
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y-%m-%d %H:%M:%S"):
            try:
                sample_length = len(datetime.now().strftime(fmt))
                datetime.strptime(normalized[:sample_length], fmt)
                return True
            except ValueError:
                continue
    return False


def _is_numeric(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def infer_chart_type(columns: list[str], rows: list[dict[str, Any]]) -> str:
    if not rows or not columns:
        return "table"

    sample = rows[0]
    if len(columns) >= 2:
        x_value = sample.get(columns[0])
        y_value = sample.get(columns[1])
        if _looks_like_date(x_value) and _is_numeric(y_value):
            return "line"
        if isinstance(x_value, str) and _is_numeric(y_value):
            unique_categories = len({str(row.get(columns[0])) for row in rows[:20]})
            if unique_categories <= 6:
                return "pie"
            return "bar"
    return "table"
