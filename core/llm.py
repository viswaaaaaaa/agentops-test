"""
LLM Factory
-----------
Single import for all agents. Swap provider in config.py or via env var.
All providers return an OpenAI-compatible interface via LangChain.
"""
from functools import lru_cache
from core.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY, GEMINI_MODEL,
    CLAUDE_API_KEY, CLAUDE_MODEL,
    GROQ_API_KEY,   GROQ_MODEL,
)


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.2):
    """Return a LangChain chat model based on LLM_PROVIDER config."""

    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True,
        )

    elif LLM_PROVIDER == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=CLAUDE_MODEL,
            anthropic_api_key=CLAUDE_API_KEY,
            temperature=temperature,
            max_tokens=2048,
        )

    elif LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=temperature,
        )

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use gemini | claude | groq")


def get_fast_llm():
    """
    Lightweight LLM for Orchestrator routing decisions.
    Uses Groq free tier (fastest) if key is set, otherwise falls back to main LLM.
    """
    if GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0.0,
        )
    return get_llm()
