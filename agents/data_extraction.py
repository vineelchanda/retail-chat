"""
Agent 2: Data Extraction Agent

WHAT IT DOES:
Takes the parsed intent + entities and generates a DuckDB SQL query,
then executes it against the database.

HOW IT WORKS:
1. Receives intent, entities, and schema from state
2. Builds a prompt asking the LLM to write SQL
3. Calls Google Gemini to generate the SQL
4. Executes the SQL against DuckDB
5. If execution fails, stores the error (Validation Agent will trigger a retry)

KEY DESIGN DECISIONS:
- The LLM generates raw SQL (not Python code) — SQL is safer and easier to validate
- We pass the error from previous attempts so the LLM can self-correct
- DuckDB's read_csv_auto already inferred types, so SQL "just works"
"""

import re
import json
from typing import Optional
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from prompts.templates import DATA_EXTRACTION_PROMPT

genai.configure(api_key=GEMINI_API_KEY)

# SQL statements that should never appear in generated queries
DANGEROUS_SQL = re.compile(
    r"\b(DROP|DELETE|ALTER|TRUNCATE|INSERT|UPDATE|CREATE|EXEC|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def sanitize_sql(sql: str) -> Optional[str]:
    """Returns an error message if SQL contains dangerous statements, else None."""
    match = DANGEROUS_SQL.search(sql)
    if match:
        return f"Blocked: generated SQL contains disallowed statement '{match.group()}'"
    return None


def data_extraction_agent(state: dict) -> dict:
    """Generate and execute SQL query based on parsed intent."""
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Build error context if this is a retry
    error_context = ""
    if state.get("error"):
        error_context = (
            f"PREVIOUS ATTEMPT FAILED. The SQL query:\n{state.get('sql_query', '')}\n"
            f"Produced this error: {state['error']}\n"
            f"Please fix the query and try a different approach."
        )

    prompt = DATA_EXTRACTION_PROMPT.format(
        schema_description=state["schema_description"],
        intent=state["intent"],
        entities=json.dumps(state["entities"]),
        user_query=state["user_query"],
        error_context=error_context,
    )

    # Call Gemini to generate SQL
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0),
    )

    sql_query = response.text.strip()

    # Clean up markdown code blocks if LLM wraps the SQL
    if sql_query.startswith("```"):
        sql_query = sql_query.split("\n", 1)[1]  # remove first line (```sql)
        sql_query = sql_query.rsplit("```", 1)[0]  # remove closing ```
        sql_query = sql_query.strip()

    # Sanitize SQL before execution
    sql_error = sanitize_sql(sql_query)
    if sql_error:
        return {
            **state,
            "sql_query": sql_query,
            "query_result": None,
            "column_names": [],
            "error": sql_error,
        }

    # Execute the SQL against DuckDB
    con = state["db_connection"]
    try:
        result = con.execute(sql_query).fetchall()
        # Also get column names for better formatting
        columns = [desc[0] for desc in con.description]
        return {
            **state,
            "sql_query": sql_query,
            "query_result": result,
            "column_names": columns,
            "error": None,
        }
    except Exception as e:
        return {
            **state,
            "sql_query": sql_query,
            "query_result": None,
            "column_names": [],
            "error": str(e),
        }
