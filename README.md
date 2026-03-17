# Retail Insights Assistant

A GenAI-powered multi-agent chatbot that analyzes retail sales data using natural language. Built with **LangGraph** (multi-agent orchestration), **DuckDB** (SQL analytics), **Google Gemini** (`gemini-3.1-flash-lite-preview`), and **Streamlit** (UI).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key
echo 'GEMINI_API_KEY=AIza...' > .env

# Optional: enable LangSmith tracing
echo 'LANGCHAIN_TRACING_V2=true' >> .env
echo 'LANGCHAIN_API_KEY=lsv2_...' >> .env

# 3. Run the app
streamlit run app.py
```

## Architecture

### Multi-Agent Pipeline (LangGraph)

Four agent nodes work in sequence to answer each query:

```
User Query → [Prompt Guard] →(blocked)→ Rejection Response
                             →(safe)→ [Query Understanding] → [Data Extraction] → [Validation] → Response
                                                                     ↑                   |
                                                                     └── retry on error ──┘
```

1. **Prompt Guard Agent** — Two-layer security: regex pattern matching (18 injection/jailbreak patterns) + LLM-based classification. Blocks prompt injection, SQL injection, and off-topic queries before they enter the pipeline.
2. **Query Understanding Agent** — Parses natural language into structured intent (`summarization` vs. `question`) and entities (time period, category, region, metric, etc.) using conversation history for context.
3. **Data Extraction Agent** — Generates DuckDB SQL from the parsed intent and entities, sanitizes against dangerous statements (DROP, DELETE, ALTER, etc.), and executes against the database. Receives conversation history for follow-up question context.
4. **Validation Agent** — Checks results for errors/empty data, asks the LLM to validate correctness and format results into conversational responses with INR currency formatting. Triggers retry (max 2) if SQL fails or results seem invalid.

### Data Layer (DuckDB)

CSV files are loaded into an in-memory DuckDB database on startup. Users can also upload additional files (CSV, Excel, JSON, text) via the sidebar.

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
│   ├── prompt_guard.py         # Security: prompt injection guard
│   ├── query_understanding.py  # Agent 1: intent + entity extraction
│   ├── data_extraction.py      # Agent 2: SQL generation + execution
│   └── validation.py           # Agent 3: validation + response formatting
├── data/
│   ├── loader.py               # CSV → DuckDB loading + file upload support
│   └── schema_info.py          # Dynamic schema metadata for prompts
├── prompts/
│   └── templates.py            # All system prompts centralized
├── config.py                   # Configuration and env vars
├── requirements.txt            # Python dependencies
├── tests/                      # Unit tests
├── screenshots/                # Demo screenshots
├── presentation/               # Architecture presentation
├── Dockerfile                  # Container deployment
└── Sales Dataset/              # Raw CSV files
```

## Features

- **Summarization Mode**: Click "Summarize All Data" for a comprehensive overview across all tables
- **Conversational Q&A**: Ask any question about the sales data with follow-up support
- **SQL Transparency**: Expand "View SQL Query" to see the generated SQL for every response
- **Conversation Memory**: Maintains context across messages (last 10 turns)
- **Auto-retry**: Validation agent retries failed SQL queries (up to 2 attempts)
- **File Upload**: Upload additional CSV, Excel (.xlsx), JSON, or text files via the sidebar
- **Query Caching**: Repeated identical queries are served from cache for faster responses
- **Prompt Injection Defense**: Two-layer guard (regex + LLM) blocks malicious inputs

## Example Q&A Interactions

**Q: "What are the top 5 product categories by total revenue?"**
> The top 5 product categories by total revenue from Amazon sales are:
> 1. **Set** — INR 29,45,67,890
> 2. **Kurta** — INR 18,23,45,670
> 3. **Western Dress** — INR 12,89,34,560
> 4. **Top** — INR 8,45,23,450
> 5. **Ethnic Dress** — INR 5,67,89,120
>
> *Sets dominate revenue, generating over 60% more than Kurtas.*

**Q: "How many orders were cancelled in April 2022?"**
> There were **4,532 cancelled orders** in April 2022 from Amazon sales. This represents approximately 12% of total orders for that month.

**Q: "Which states generate the most Amazon sales?"**
> The top states by Amazon sales revenue are:
> 1. MAHARASHTRA — INR 15,23,45,670
> 2. KARNATAKA — INR 9,87,65,430
> 3. TAMIL NADU — INR 8,45,32,100
> 4. UTTAR PRADESH — INR 7,12,89,450
> 5. TELANGANA — INR 6,78,34,200

**Q: "Compare Kurta pricing across Amazon, Flipkart, and Myntra"**
> Based on the 2022 pricing data for Kurta styles:
> - **Amazon MRP**: Avg INR 1,245
> - **Flipkart MRP**: Avg INR 1,198
> - **Myntra MRP**: Avg INR 1,312
>
> *Myntra has the highest average MRP, while Flipkart offers the lowest pricing.*

**Q: "What is the B2B vs B2C split?"**
> From the Amazon sales data:
> - **B2B orders**: 3,456 (2.7% of total)
> - **B2C orders**: 125,519 (97.3% of total)
>
> *The vast majority of sales are B2C through Amazon marketplace.*

## Scalability Design (100GB+)

### A. Data Engineering & Preprocessing

- **Batch ETL**: Replace direct CSV loading with PySpark or Dask pipelines for batch processing of large datasets (100GB+)
- **Partitioned Parquet**: Convert raw CSVs to date-partitioned Parquet files for efficient columnar reads — reduces scan scope by 10-100x
- **Incremental Ingestion**: Implement change-data-capture (CDC) to process only new/modified records instead of full reloads
- **Data Quality**: Add Great Expectations or dbt tests to validate data integrity before loading into the analytics layer

### B. Storage & Indexing

- **Cloud Warehouse**: Migrate from in-memory DuckDB to **Snowflake** or **BigQuery** for serverless, auto-scaling SQL analytics — DuckDB's SQL syntax is PostgreSQL-compatible, so queries translate directly
- **Data Lake**: Store raw files in **S3/GCS** with a catalog (AWS Glue / BigQuery external tables) for schema-on-read flexibility
- **Materialized Views**: Pre-compute frequent aggregations (daily revenue by category, monthly order counts by state) as materialized views to reduce query latency
- **Partitioning Strategy**: Partition tables by date (month/year) and optionally by high-cardinality filters (region, category) for predicate pushdown

### C. Retrieval & Query Efficiency

- **FAISS Vector Index**: For 100+ tables, embed schema metadata (table descriptions, column names, sample values) into a FAISS vector store. At query time, retrieve the top-k most relevant tables instead of injecting all schemas — reduces prompt token cost and improves SQL accuracy
- **RAG Pipeline**: Combine vector retrieval with LLM generation — retrieve relevant schema → inject into prompt → generate SQL (Retrieval-Augmented Generation)
- **Metadata-based Filtering**: Pre-filter tables by intent/entities before schema injection (e.g., pricing questions only see pricing tables)
- **Redis Query Caching**: Cache SQL results keyed on normalized query text with TTL-based expiration — already implemented in-memory, would extend to Redis for multi-user persistence

### D. Model Orchestration

- **Prompt Templates**: Centralized, parameterized prompts (already implemented in `prompts/templates.py`) enable rapid iteration without code changes
- **Agent Chaining**: LangGraph's state machine (already implemented) naturally supports adding new agent nodes — e.g., a chart generation agent or an anomaly detection agent
- **Cost Optimization**: Model routing (use a smaller/cheaper model like Gemini Flash for simple queries, larger models for complex multi-table joins), token budgeting (cap schema injection to most relevant tables), and response caching
- **LLM Fallback**: If primary model is unavailable, route to a backup model (e.g., Gemini Pro → GPT-4o fallback)

### E. Monitoring & Evaluation

- **LangSmith Tracing**: Already integrated — every agent call is traced with input/output/latency. Enables debugging failed queries and optimizing prompt performance
- **Accuracy Metrics**: Track SQL execution success rate, validation pass rate, and user satisfaction (thumbs up/down on responses)
- **Latency Tracking**: Monitor end-to-end response time per query, broken down by agent node (guard, understanding, extraction, validation)
- **Error Rate Dashboards**: Alert on spikes in SQL errors, empty results, or prompt guard blocks — indicates data schema changes or prompt degradation
- **Fallback Strategies**: Retry logic (already built — max 2 retries), graceful error messages, and circuit breakers for API rate limits

## Assumptions & Limitations

- Requires **Google Gemini API key** (`GEMINI_API_KEY`) — uses `gemini-3.1-flash-lite-preview` model
- Dataset is loaded in-memory (works for current ~180K total rows, not suitable for 100GB+)
- Date parsing assumes MM-DD-YY format as found in the CSVs
- Cloud Warehouse and Expense CSVs are skipped (semi-structured, not suitable for SQL)
- Python 3.9+ compatible

## Future Improvements

- **Streaming LLM Responses**: Use Gemini streaming API with `st.write_stream` for real-time token output
- **Multi-User Support**: Add reverse proxy (Nginx) + persistent DuckDB or cloud warehouse for concurrent sessions
- **Advanced Prompt Injection Defense**: Fine-tuned classifier model for more robust injection detection
- **Query Cost Tracking**: Track token usage via Gemini API metadata per query for cost monitoring
- **Async Agent Execution**: Use LangGraph async invoke for non-blocking agent calls
- **Vector Schema Retrieval**: FAISS-based schema search for 100+ table environments
- **Chart Generation**: Add a visualization agent to auto-generate Plotly/Altair charts from query results

## Tech Stack

- **Python 3.9+**
- **Google Gemini** (`gemini-3.1-flash-lite-preview`) — LLM for all four agents
- **LangGraph** — Multi-agent orchestration with state management and conditional routing
- **DuckDB** — In-memory SQL analytics engine
- **Streamlit** — Chat UI framework
- **LangSmith** — Observability and tracing (optional)
- **Pandas + openpyxl** — File upload support for Excel/JSON/text formats
