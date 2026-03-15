"""
LangGraph State Graph — wires the 3 agents together.

THE FLOW:
    [START] → Query Understanding → Data Extraction → Validation
                                          ↑                |
                                          └── needs_retry ──┘
                                                           |
                                                        [END]

HOW LangGraph WORKS:
- You define a StateGraph with a shared state dictionary
- Each "node" is a function that reads state, does work, returns updated state
- "Edges" connect nodes in sequence
- "Conditional edges" let you branch (e.g., retry on failure)
- compile() turns the graph into a runnable app

WHY LangGraph (not raw function calls):
- Built-in state management — no manual passing of variables
- Visual graph representation — easy to explain in interviews
- Conditional routing — retry logic is declarative, not nested if/else
- Easy to add more agents later (just add nodes and edges)
"""

from langgraph.graph import StateGraph, END
from agents.prompt_guard import prompt_guard_agent
from agents.query_understanding import query_understanding_agent
from agents.data_extraction import data_extraction_agent
from agents.validation import validation_agent


def after_guard(state: dict) -> str:
    """Route after prompt guard: block or continue."""
    if state.get("blocked", False):
        return END
    return "query_understanding"


def should_retry(state: dict) -> str:
    """Routing function: retry data extraction or finish."""
    if state.get("needs_retry", False):
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
        "user_query": user_query,
        "chat_history": chat_history,
        "db_connection": db_connection,
        "schema_description": schema_description,
        "intent": "",
        "entities": {},
        "sql_query": "",
        "query_result": None,
        "column_names": [],
        "error": None,
        "final_response": "",
        "needs_retry": False,
        "retry_count": 0,
    }

    # Run the graph — LangGraph handles the flow automatically
    final_state = graph.invoke(initial_state)

    return {
        "response": final_state.get("final_response", "Sorry, I couldn't process that query."),
        "sql_query": final_state.get("sql_query", ""),
        "intent": final_state.get("intent", ""),
        "entities": final_state.get("entities", {}),
    }
