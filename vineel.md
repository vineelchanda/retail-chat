# Vineel's Knowledge Tracker — Retail Insights Assistant

## Current Understanding Level

### Big Picture
- [ ] Can explain the project in 2-3 sentences
- [ ] Can draw the 3-agent flow on a whiteboard
- [ ] Can explain why multi-agent > single LLM call

### Tech Stack
| Technology | What It Does | Confidence |
|---|---|---|
| DuckDB | In-memory SQL database, reads CSVs directly | ⬜ Not started |
| Gemini API | LLM that powers all 3 agents | ⬜ Not started |
| LangGraph | Wires agents together, manages state & retry | ⬜ Not started |
| Streamlit | Chat UI framework | ⬜ Not started |
| Python | Primary language | ⬜ Not started |

**Confidence levels**: ⬜ Not started → 🟡 Basics understood → 🟢 Can explain confidently

### Agent Deep Dive
| Agent | Purpose | Can Explain? | Can Modify? |
|---|---|---|---|
| Query Understanding | Parses question → intent + entities JSON | ⬜ | ⬜ |
| Data Extraction | Generates SQL → executes on DuckDB | ⬜ | ⬜ |
| Validation | Checks results → formats response / retries | ⬜ | ⬜ |

### Key Concepts
- [ ] Prompt Engineering — how system prompts work, why schema is injected
- [ ] Schema Injection — dynamic metadata from DuckDB into prompts
- [ ] Conversation Memory — sliding window of chat history
- [ ] Retry Mechanism — conditional edge in LangGraph
- [ ] State Management — how data flows between agents via state dict
- [ ] Temperature — 0 for deterministic, 0.3 for creative formatting

### Scalability (100GB+)
- [ ] Can explain current limitations (in-memory, single node)
- [ ] Can propose cloud warehouse swap (Snowflake/BigQuery)
- [ ] Can explain partitioning, caching, vector store for schema retrieval
- [ ] Can discuss PySpark/Dask for ETL preprocessing

### Code Files — Can Walk Through Each
| File | Purpose | Reviewed? |
|---|---|---|
| `config.py` | API keys, model name, constants | ⬜ |
| `data/loader.py` | Loads CSVs into DuckDB, cleans columns | ⬜ |
| `data/schema_info.py` | Builds schema description for prompts | ⬜ |
| `prompts/templates.py` | All 3 agent system prompts | ⬜ |
| `agents/query_understanding.py` | Agent 1 — NLP parsing | ⬜ |
| `agents/data_extraction.py` | Agent 2 — SQL generation + execution | ⬜ |
| `agents/validation.py` | Agent 3 — validation + formatting | ⬜ |
| `agents/graph.py` | LangGraph StateGraph wiring | ⬜ |
| `app.py` | Streamlit UI entry point | ⬜ |

---

## Study Sessions Log

### Session 1 — [Date: ___]
- Topics covered:
- Questions I struggled with:
- Action items:

### Session 2 — [Date: ___]
- Topics covered:
- Questions I struggled with:
- Action items:

---

## Mock Interview Questions — Practice Tracker

| # | Question | Can Answer? |
|---|---|---|
| 1 | Explain your project at a high level | ⬜ |
| 2 | Why 3 agents instead of 1 LLM call? | ⬜ |
| 3 | Why DuckDB instead of Pandas? | ⬜ |
| 4 | How does the LLM know about your data? | ⬜ |
| 5 | How do you handle LLM hallucinations? | ⬜ |
| 6 | What is LangGraph and why use it? | ⬜ |
| 7 | Walk me through a query end-to-end | ⬜ |
| 8 | How does the retry mechanism work? | ⬜ |
| 9 | How would you scale this to 100GB+? | ⬜ |
| 10 | How does conversation memory work? | ⬜ |
| 11 | What is prompt engineering in your context? | ⬜ |
| 12 | What if the user asks something not in the data? | ⬜ |
| 13 | How would you deploy this to production? | ⬜ |
| 14 | What are the limitations of your approach? | ⬜ |
| 15 | How would you add a new dataset/table? | ⬜ |

---

## Notes & Things to Remember

_Add anything you learn or want to revisit here_

