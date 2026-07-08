"""Memoria por sesión en proceso (MVP). En producción: Redis (compartida entre
réplicas, con TTL) + volcado a PostgreSQL para historial consultable/auditoría."""

from collections import defaultdict, deque

_MAX_TURNS = 8  # últimos 8 mensajes (4 pares) — suficiente para follow-ups
_sessions: dict[str, deque] = defaultdict(lambda: deque(maxlen=_MAX_TURNS))


def get_history(session_id: str) -> list[tuple[str, str]]:
    return list(_sessions[session_id])


def append(session_id: str, role: str, content: str) -> None:
    _sessions[session_id].append((role, content))


def clear(session_id: str) -> None:
    _sessions.pop(session_id, None)
