"""
Agent 3: Validation Agent

WHAT IT DOES:
Validates the SQL results and formats them into a natural language response.

HOW IT WORKS:
1. Checks if there was a SQL error → triggers retry
2. Checks if results are empty → triggers retry with hint
3. If valid, asks the LLM to format raw data into a conversational response
4. After max retries, returns a graceful fallback message

WHY VALIDATION MATTERS:
- LLM-generated SQL can reference wrong columns, use wrong syntax, etc.
- Without validation, the user would see raw errors or misleading empty results
- The retry loop gives the SQL agent a chance to self-correct using error feedback
"""

import json
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES
from prompts.templates import VALIDATION_PROMPT

genai.configure(api_key=GEMINI_API_KEY)


def validation_agent(state: dict) -> dict:
    """Validate query results and format the response."""
    retry_count = state.get("retry_count", 0)

    # Case 1: SQL execution error — retry if we haven't hit the limit
    if state.get("error"):
        if retry_count < MAX_RETRIES:
            return {
                **state,
                "needs_retry": True,
                "retry_count": retry_count + 1,
            }
        else:
            return {
                **state,
                "needs_retry": False,
                "final_response": (
                    f"I encountered an issue querying the data after multiple attempts. "
                    f"Error: {state['error']}\n\n"
                    f"Could you try rephrasing your question?"
                ),
            }

    # Case 2: Empty results — retry once with a hint
    if not state.get("query_result"):
        if retry_count < MAX_RETRIES:
            return {
                **state,
                "error": "Query returned empty results. Try a broader query or check table/column names.",
                "needs_retry": True,
                "retry_count": retry_count + 1,
            }
        else:
            return {
                **state,
                "needs_retry": False,
                "final_response": "I couldn't find any data matching your query. The dataset may not contain information for those specific filters. Try broadening your question.",
            }

    # Case 3: We have results — format them with LLM
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Build a readable result string with column headers
    columns = state.get("column_names", [])
    rows = state["query_result"]

    # Format as a list of dicts for clarity
    if columns:
        formatted_results = [dict(zip(columns, row)) for row in rows[:50]]  # cap at 50 rows
    else:
        formatted_results = rows[:50]

    prompt = VALIDATION_PROMPT.format(
        user_query=state["user_query"],
        sql_query=state["sql_query"],
        query_result=json.dumps(formatted_results, default=str),
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    result = json.loads(response.text)

    if result.get("valid", True):
        return {
            **state,
            "needs_retry": False,
            "final_response": result.get("response", "Here are your results."),
        }
    else:
        # LLM thinks results are invalid
        if retry_count < MAX_RETRIES:
            return {
                **state,
                "error": result.get("reason", "Results seem incorrect"),
                "needs_retry": True,
                "retry_count": retry_count + 1,
            }
        else:
            return {
                **state,
                "needs_retry": False,
                "final_response": result.get(
                    "response",
                    "I found some data but I'm not confident in the results. Please try rephrasing your question.",
                ),
            }
