"""
THE FLOW:
    [START] → Prompt Guard →(blocked=True)→ [END]
                            →(blocked=False)→ Query Understanding → Data Extraction → Validation
                                                                          ↑                |
                                                                          └── needs_retry ──┘
                                                                                           |
                                                                                        [END]


─────────────────────────────────────────────────────────────
STATE REFERENCE  (state is a dict of 5 sub-dicts)
─────────────────────────────────────────────────────────────
state["input"]    — user input, set once, never modified
  user_query        str   — raw user question
                          → QUERY_UNDERSTANDING_PROMPT {user_query}
                          → DATA_EXTRACTION_PROMPT     {user_query}
                          → VALIDATION_PROMPT          {user_query}
  chat_history      list  — prior conversation turns
                          → QUERY_UNDERSTANDING_PROMPT {chat_history}

state["context"]  — infrastructure, set once, never modified
  db_connection     obj   — live DuckDB connection (used directly in data_extraction, not in prompts)
  schema_description str  — table/column metadata for prompts
                          → QUERY_UNDERSTANDING_PROMPT {schema_description}
                          → DATA_EXTRACTION_PROMPT     {schema_description}

state["parsed"]   — set by query_understanding_agent
  intent            ""    → "summarization" or "question"
                          → DATA_EXTRACTION_PROMPT     {intent}
  entities          {}    → time_period, category, region, etc.
                          → DATA_EXTRACTION_PROMPT     {entities}

state["result"]   — set by data_extraction_agent
  sql_query         ""    → generated SQL string
                          → VALIDATION_PROMPT          {sql_query}
  query_result      None  → list of rows from DuckDB
                          → VALIDATION_PROMPT          {query_result}
  column_names      []    → column headers for query_result (used in response formatting, not injected into prompts)
  error             None  → error string if SQL failed; used as retry feedback
                          → DATA_EXTRACTION_PROMPT     {error_context}

state["control"]  — routing flags and final output
  final_response    ""    → filled by prompt_guard (blocked) or validation (success/failure)
  needs_retry       False → set by validation; controls the retry edge
  retry_count       0     → incremented by validation on each retry
  blocked           False → set True by prompt_guard if query is unsafe

EDGE-CONTROLLING KEYS  (read by routing functions only):
  control.blocked      → after_guard()   → True=END, False="query_understanding"
  control.needs_retry  → should_retry()  → True="data_extraction", False=END

VALIDATION NODE — what it does with query_result=None:
  Situation          | Data?  | Validation's job
  -------------------|--------|----------------------------------------------
  SQL error          | None   | Retry (needs_retry=True) or give up (final_response)
  Empty result       | None   | Retry with hint or give up (final_response)
  Valid result       | Rows   | Format rows into natural language via LLM
  LLM says invalid   | Rows   | Retry with reason or give up (final_response)

  NOTE: Even with no data, validation must run — it is the only place that
  checks MAX_RETRIES, sets needs_retry, and controls the graph's next step.
─────────────────────────────────────────────────────────────
"""

from langgraph.graph import StateGraph, END
from agents.prompt_guard import prompt_guard_agent
from agents.query_understanding import query_understanding_agent
from agents.data_extraction import data_extraction_agent
from agents.validation import validation_agent


def after_guard(state: dict) -> str:
    """Route after prompt guard: block or continue."""
    if state["control"].get("blocked", False):
        return END
    return "query_understanding"


def should_retry(state: dict) -> str:
    """Routing function: retry data extraction or finish."""
    if state["control"].get("needs_retry", False):
        return "data_extraction"
    return END


def create_graph():
    """Build and compile the multi-agent LangGraph workflow.

    THE FLOW:
        [START] → Prompt Guard →(blocked)→ [END]
                                →(safe)→ Query Understanding → Data Extraction → Validation
                                                                    ↑                |
                                                                    └── needs_retry ──┘
                                                                                     |
                                                                                  [END]
    """
    workflow = StateGraph(dict)

    # Add all agent nodes
    workflow.add_node("prompt_guard", prompt_guard_agent)
    workflow.add_node("query_understanding", query_understanding_agent)
    workflow.add_node("data_extraction", data_extraction_agent)
    workflow.add_node("validation", validation_agent)

    # Entry point is now the prompt guard
    workflow.set_entry_point("prompt_guard")

    # Guard routes to either END (blocked) or query_understanding (safe)
    workflow.add_conditional_edges("prompt_guard", after_guard)

    # Rest of the flow is the same
    workflow.add_edge("query_understanding", "data_extraction")
    workflow.add_edge("data_extraction", "validation")
    workflow.add_conditional_edges("validation", should_retry)

    return workflow.compile()


def run_query(graph, user_query: str, chat_history: list, db_connection, schema_description: str) -> dict:
    """
    Execute the full agent pipeline for a user query.

    Args:
        graph: Compiled LangGraph workflow
        user_query: The user's natural language question
        chat_history: List of {"role": "user"/"assistant", "content": "..."} dicts
        db_connection: DuckDB connection
        schema_description: Schema metadata string for prompts

    Returns:
        dict with "final_response" (the answer) and "sql_query" (for transparency)
    """
    initial_state = {
        # User input — set once, never modified
        "input": {
            "user_query": user_query,
            "chat_history": chat_history,
        },
        # Infrastructure — set once, never modified
        "context": {
            "db_connection": db_connection,
            "schema_description": schema_description,
        },
        # Set by query_understanding_agent
        "parsed": {
            "intent": "",
            "entities": {},
        },
        # Set by data_extraction_agent
        "result": {
            "sql_query": "",
            "query_result": None,
            "column_names": [],
            "error": None,
        },
        # Routing flags and final output
        "control": {
            "final_response": "",
            "needs_retry": False,
            "retry_count": 0,
            "blocked": False,
        },
    }

    # Run the graph — LangGraph handles the flow automatically
    final_state = graph.invoke(initial_state)

    return {
        "response": final_state["control"].get("final_response", "Sorry, I couldn't process that query."),
        "sql_query": final_state["result"].get("sql_query", ""),
        "intent": final_state["parsed"].get("intent", ""),
        "entities": final_state["parsed"].get("entities", {}),
    }
