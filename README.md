# Retail Insights Assistant

A GenAI-powered multi-agent chatbot that analyzes retail sales data using natural language. Built with **LangGraph** (multi-agent orchestration), **DuckDB** (SQL analytics), **OpenAI GPT-4o** (LLM), and **Streamlit** (UI).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key
echo 'OPENAI_API_KEY=sk-...' > .env
# OR
export OPENAI_API_KEY=sk-...

# 3. Run the app
streamlit run app.py
```

## Architecture

### Multi-Agent Pipeline (LangGraph)

Three agents work in sequence to answer each query:

```
User Query → [Query Understanding] → [Data Extraction] → [Validation] → Response
                                           ↑                   |
                                           └── retry on error ─┘
```

1. **Query Understanding Agent** — Parses natural language into structured intent (summarization vs. question) and entities (time period, category, region, etc.)
2. **Data Extraction Agent** — Generates DuckDB SQL from the parsed intent, executes it against the database
3. **Validation Agent** — Checks results for errors/empty data, formats valid results into conversational responses. Triggers retry (max 2) if SQL fails.

### Data Layer (DuckDB)

CSV files are loaded into an in-memory DuckDB database on startup:

| Table | Source | Rows | Description |
|-------|--------|------|-------------|
| `amazon_sales` | Amazon Sale Report.csv | 128,975 | Amazon marketplace transactions |
| `international_sales` | International sale Report.csv | 37,432 | B2B international sales |
| `inventory` | Sale Report.csv | 9,271 | Stock levels by SKU |
| `product_pricing_2021` | P L March 2021.csv | 1,330 | MRP across platforms (2021) |
| `product_pricing_2022` | May-2022.csv | 1,330 | MRP across platforms (2022) |

### Why DuckDB?
- Reads CSVs directly with zero setup (no server, no config)
- SQL interface — same language the LLM generates
- Extremely fast columnar engine for analytical queries
- In-memory mode perfect for datasets under 1GB

## Project Structure

```
├── app.py                      # Streamlit UI entry point
├── agents/
│   ├── graph.py                # LangGraph state graph wiring
│   ├── query_understanding.py  # Agent 1: intent + entity extraction
│   ├── data_extraction.py      # Agent 2: SQL generation + execution
│   └── validation.py           # Agent 3: validation + response formatting
├── data/
│   ├── loader.py               # CSV → DuckDB loading + cleaning
│   └── schema_info.py          # Dynamic schema metadata for prompts
├── prompts/
│   └── templates.py            # All system prompts centralized
├── config.py                   # Configuration and env vars
├── requirements.txt            # Python dependencies
└── Sales Dataset/              # Raw CSV files
```

## Example Queries

- "What are the top 5 product categories by total revenue?"
- "How many orders were cancelled in April 2022?"
- "Which states generate the most Amazon sales?"
- "Compare Kurta pricing across Amazon, Flipkart, and Myntra"
- "Who are the top international customers by gross amount?"
- "What is the B2B vs B2C split?"
- "Show me inventory stock levels by category"

## Features

- **Summarization Mode**: Click "Summarize All Data" for a comprehensive overview
- **Conversational Q&A**: Ask any question about the sales data
- **SQL Transparency**: Expand "View SQL Query" to see the generated SQL
- **Conversation Memory**: Maintains context across messages
- **Auto-retry**: Validation agent retries failed SQL queries (up to 2 attempts)

## Scalability Design (100GB+)

For scaling beyond the current in-memory approach:

- **Storage**: DuckDB on disk → Cloud warehouse (Snowflake/BigQuery)
- **Partitioning**: Date-based partitions to reduce scan scope
- **Caching**: Redis layer for frequent queries
- **ETL**: PySpark/Dask for batch preprocessing of raw CSVs
- **Schema Retrieval**: Vector store (FAISS) for schema search when table count grows
- **Streaming**: Async agent execution + streaming LLM responses

## Assumptions & Limitations

- Requires OpenAI API key (GPT-4o) — not free
- Dataset is loaded in-memory (works for current ~180K total rows, not 100GB+)
- Date parsing assumes MM-DD-YY format as found in the CSVs
- Cloud Warehouse and Expense CSVs are skipped (semi-structured, not suitable for SQL)
- Python 3.9+ compatible

## Tech Stack

- **Python 3.9+**
- **OpenAI GPT-4o** — LLM for all three agents
- **LangGraph** — Multi-agent orchestration with state management
- **DuckDB** — In-memory SQL analytics engine
- **Streamlit** — Chat UI framework
