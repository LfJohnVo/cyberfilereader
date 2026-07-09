"""Factoría del chat model (Ollama vía init_chat_model). Único punto para cambiar de proveedor."""

import re

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.core.config import get_settings

_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def get_chat_model() -> BaseChatModel:
    s = get_settings()
    return init_chat_model(
        s.ollama_chat_model,
        model_provider="ollama",
        base_url=s.ollama_base_url,
        temperature=s.llm_temperature,
        num_ctx=s.ollama_num_ctx,
        # qwen3 es "thinking": desactivarlo evita respuestas vacías (solo <think>) y baja latencia.
        reasoning=False,
    )


def strip_reasoning(text: str) -> str:
    """Elimina bloques de razonamiento <think>...</think> que algunos modelos emiten."""
    return _THINK_RE.sub("", text or "").strip()
