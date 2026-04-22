from app.schemas.schema import SchemaResponse


def build_schema_summary(schema: SchemaResponse, max_tables: int = 25) -> str:
    lines: list[str] = []
    for table in schema.tables[:max_tables]:
        header = f"Table {table.schema_name + '.' if table.schema_name else ''}{table.name}"
        row_count = f" (~{table.estimated_row_count} rows)" if table.estimated_row_count is not None else ""
        lines.append(f"{header}{row_count}")
        column_bits = [
            f"{column.name} {column.data_type}{' not null' if not column.nullable else ''}"
            for column in table.columns
        ]
        lines.append(f"Columns: {', '.join(column_bits)}")
        if table.primary_key:
            lines.append(f"Primary key: {', '.join(table.primary_key)}")
        if table.foreign_keys:
            fk_text = "; ".join(
                f"{', '.join(fk.constrained_columns)} -> {fk.referred_table}({', '.join(fk.referred_columns)})"
                for fk in table.foreign_keys
            )
            lines.append(f"Foreign keys: {fk_text}")
        if table.indexes:
            index_text = "; ".join(
                f"{idx.name}({', '.join(idx.columns)}){' unique' if idx.unique else ''}" for idx in table.indexes
            )
            lines.append(f"Indexes: {index_text}")
        lines.append("")
    return "\n".join(lines).strip()
