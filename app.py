"""
Streamlit UI for the Retail Insights Assistant.

HOW TO RUN:
    export OPENAI_API_KEY="your-key"
    streamlit run app.py

LAYOUT:
- Sidebar: title, loaded tables info, Summarize button, Clear Chat button
- Main area: chat message history + chat input box

HOW IT CONNECTS:
1. On first load: creates DuckDB connection (loads all CSVs), builds schema, compiles LangGraph
2. On user input: runs the 3-agent pipeline → displays response
3. Chat history stored in st.session_state for conversation memory
"""

import logging
import streamlit as st
from config import LANGCHAIN_PROJECT
from data.loader import load_all_data
from data.schema_info import get_schema_description
from agents.graph import create_graph, run_query
from prompts.templates import SUMMARIZATION_QUERY

logger = logging.getLogger(__name__)

# ──────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────
st.set_page_config(
    page_title="Retail Insights Assistant",
    page_icon="📊",
    layout="wide",
)

# ──────────────────────────────────────
# Initialize session state (runs once)
# ──────────────────────────────────────
if "initialized" not in st.session_state:
    logger.info("Starting Retail Insights Assistant...")
    with st.spinner("Loading sales data into DuckDB..."):
        st.session_state.con = load_all_data()
        logger.info("DuckDB data loaded successfully")
        st.session_state.schema_desc = get_schema_description(st.session_state.con)
        logger.info("Schema description built")
        st.session_state.graph = create_graph()
        logger.info("LangGraph workflow compiled")
        st.session_state.chat_history = []
        st.session_state.initialized = True
    logger.info("App initialized and ready — LangSmith project: %s", LANGCHAIN_PROJECT)

# ──────────────────────────────────────
# Sidebar
# ──────────────────────────────────────
with st.sidebar:
    st.title("📊 Retail Insights Assistant")
    st.markdown("---")

    # Show loaded tables
    st.subheader("Loaded Tables")
    tables = st.session_state.con.execute("SHOW TABLES").fetchall()
    for (table_name,) in tables:
        row_count = st.session_state.con.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]
        st.markdown(f"✅ **{table_name}** ({row_count:,} rows)")

    st.markdown("---")

    # Summarize button
    if st.button("📋 Summarize All Data", use_container_width=True):
        st.session_state.trigger_summary = True

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.caption("Built with LangGraph + DuckDB + OpenAI GPT-4o")

# ──────────────────────────────────────
# Main Chat Area
# ──────────────────────────────────────
st.header("💬 Chat with Your Sales Data")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Show SQL query in expander for transparency
        if message["role"] == "assistant" and message.get("sql_query"):
            with st.expander("🔍 View SQL Query"):
                st.code(message["sql_query"], language="sql")

# ──────────────────────────────────────
# Handle user input or summary trigger
# ──────────────────────────────────────
user_input = st.chat_input("Ask a question about your sales data...")

# Check if summary was triggered
if st.session_state.get("trigger_summary"):
    user_input = SUMMARIZATION_QUERY
    st.session_state.trigger_summary = False

if user_input:
    logger.info("User query received: %s", user_input)

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Add to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Run the agent pipeline
    with st.chat_message("assistant"):
        with st.spinner("Analyzing your data..."):
            result = run_query(
                graph=st.session_state.graph,
                user_query=user_input,
                chat_history=st.session_state.chat_history,
                db_connection=st.session_state.con,
                schema_description=st.session_state.schema_desc,
            )

        logger.info("Query processed — intent: %s, blocked: %s", result.get("intent", "N/A"), result.get("response", "")[:50])

        # Display response
        st.markdown(result["response"])

        # Show SQL in expander
        if result["sql_query"]:
            with st.expander("🔍 View SQL Query"):
                st.code(result["sql_query"], language="sql")

    # Add to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result["response"],
        "sql_query": result["sql_query"],
    })
