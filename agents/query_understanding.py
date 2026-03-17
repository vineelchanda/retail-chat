"""
Agent 1: Query Understanding Agent

WHAT IT DOES:
Takes the user's natural language question and extracts:
- intent: "summarization" (broad overview) or "question" (specific query)
- entities: structured data like time_period, category, region, etc.

HOW IT WORKS:
1. Receives user_query and chat_history from the LangGraph state
2. Injects the database schema into the prompt (so LLM knows valid column values)
3. Calls Google Gemini with the prompt
4. Parses the JSON response to extract intent and entities
5. Updates the state with these values

WHY A SEPARATE AGENT:
Separating "understanding" from "SQL generation" means each LLM call has a
focused job. This improves accuracy vs. asking one prompt to do everything.
"""

import json
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from prompts.templates import QUERY_UNDERSTANDING_PROMPT

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


def query_understanding_agent(state: dict) -> dict:
    """Parse user query into intent and entities."""
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Format chat history as readable text
    history_text = ""
    if state["input"].get("chat_history"):
        for msg in state["input"]["chat_history"][-10:]:
            role = msg["role"].capitalize()
            history_text += f"{role}: {msg['content']}\n"

    # Build the prompt with schema and history injected
    prompt = QUERY_UNDERSTANDING_PROMPT.format(
        schema_description=state["context"]["schema_description"],
        chat_history=history_text or "No previous conversation.",
        user_query=state["input"]["user_query"],
    )

    try:
        # Call Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )

        # Parse the JSON response
        result = json.loads(response.text)

        return {
            **state,
            "parsed": {
                "intent": result.get("intent", "question"),
                "entities": result.get("entities", {}),
            },
        }
    except Exception as e:
        logger.error("Query understanding failed: %s", e)
        return {
            **state,
            "parsed": {
                "intent": "question",
                "entities": {},
            },
            "result": {
                **state["result"],
                "error": f"Query understanding failed: {e}",
            },
        }
