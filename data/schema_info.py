"""
Builds a human-readable description of all DuckDB tables for LLM prompts.

The output string looks like:
    Table: amazon_sales (128,975 rows)
    Columns: order_id (VARCHAR), Date (DATE), Status (VARCHAR), ...
    Sample values for Status: Shipped, Cancelled, Shipped - Delivered to Buyer
"""

import duckdb


def get_schema_description(con: duckdb.DuckDBPyConnection) -> str:
    """Generate a formatted schema description of all tables in the database."""
    tables = con.execute("SHOW TABLES").fetchall()
    descriptions = []

    for (table_name,) in tables:
        # Get row count
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        # Get column info
        columns = con.execute(f"DESCRIBE {table_name}").fetchall()
        col_descriptions = []
        sample_values = []

        for col in columns:
            col_name = col[0]
            col_type = col[1]
            col_descriptions.append(f"{col_name} ({col_type})")

            # Get sample distinct values for VARCHAR columns (helps LLM know valid values)
            if "VARCHAR" in col_type:
                try:
                    samples = con.execute(
                        f'SELECT DISTINCT "{col_name}" FROM {table_name} '
                        f'WHERE "{col_name}" IS NOT NULL LIMIT 5'
                    ).fetchall()
                    if samples:
                        vals = [str(s[0]) for s in samples]
                        sample_values.append(f"  Sample {col_name}: {', '.join(vals)}")
                except Exception:
                    pass

        desc = f"Table: {table_name} ({row_count:,} rows)\n"
        desc += f"Columns: {', '.join(col_descriptions)}\n"
        if sample_values:
            desc += "\n".join(sample_values)

        descriptions.append(desc)
    return "\n\n".join(descriptions)
