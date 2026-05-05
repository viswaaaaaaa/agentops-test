"""
LLM Factory
-----------
Single import for all agents. Uses Groq as primary provider.
"""

from functools import lru_cache
from core.config import (
    LLM_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
)


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.2):
    """Return Groq LLM (primary provider)."""

    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=temperature,
        )

    else:
        raise ValueError(
            f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Set it to 'groq'."
        )


def get_fast_llm():
    """
    Fast LLM for orchestrator decisions.
    Always uses Groq (fast + stable).
    """
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=0.0,
    )