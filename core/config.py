import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM Provider ──────────────────────────────────────────────────
# Change this one value to swap the entire project's LLM
# Options: "gemini" | "claude" | "groq"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL     = os.getenv("GEMINI_MODEL", "gemini-2.0-pro-exp")   # your free Gemini Pro

CLAUDE_API_KEY   = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL     = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # free tier

# ── GitHub ────────────────────────────────────────────────────────
GITHUB_TOKEN          = os.getenv("GITHUB_TOKEN", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# ── Database ──────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentops.db")   # SQLite for local dev

# ── Agent settings ────────────────────────────────────────────────
CONFIDENCE_THRESHOLD  = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
MAX_TOKENS_PER_AGENT  = int(os.getenv("MAX_TOKENS_PER_AGENT", "2048"))
