"""Factoría del chat model (Ollama). Único punto para cambiar de proveedor."""

import re

from langchain_ollama import ChatOllama

from app.core.config import get_settings

_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def get_chat_model() -> ChatOllama:
    s = get_settings()
    return ChatOllama(
        model=s.ollama_chat_model,
        base_url=s.ollama_base_url,
        temperature=s.llm_temperature,
        num_ctx=s.ollama_num_ctx,
    )


def strip_reasoning(text: str) -> str:
    """Elimina bloques de razonamiento <think>...</think> que algunos modelos emiten."""
    return _THINK_RE.sub("", text or "").strip()
