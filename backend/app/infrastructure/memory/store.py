"""Memoria de conversación por sesión, en proceso. Implementa `MemoryPort`."""

import threading
from collections import OrderedDict, deque

_MAX_TURNS = 8
_MAX_SESSIONS = 5000


class InProcessMemory:
    # RLock: serializa accesos concurrentes (pool de to_thread + event loop).

    def __init__(self, max_turns: int = _MAX_TURNS, max_sessions: int = _MAX_SESSIONS):
        self._max_turns = max_turns
        self._max_sessions = max_sessions
        self._sessions: OrderedDict[str, deque] = OrderedDict()
        self._lock = threading.RLock()

    def _touch(self, session_id: str) -> deque:
        with self._lock:
            dq = self._sessions.get(session_id)
            if dq is None:
                dq = deque(maxlen=self._max_turns)
                self._sessions[session_id] = dq
                while len(self._sessions) > self._max_sessions:
                    self._sessions.popitem(last=False)
            else:
                self._sessions.move_to_end(session_id)
            return dq

    def get_history(self, session_id: str) -> list[tuple[str, str]]:
        with self._lock:
            dq = self._sessions.get(session_id)
            if dq is None:
                return []
            self._sessions.move_to_end(session_id)
            return list(dq)

    def append(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._touch(session_id).append((role, content))

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
