import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Set it in a .env file or as an environment variable.\n"
        "Example: echo 'GEMINI_API_KEY=AIza...' > .env"
    )

# LangSmith tracing (auto-enabled when env vars are set)
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "retail-chat-indulge")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
DATA_DIR = "Sales Dataset"
MAX_RETRIES = 2
MAX_CHAT_HISTORY = 10
