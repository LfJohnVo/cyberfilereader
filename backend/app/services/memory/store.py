"""Memoria de conversación por sesión, en proceso (MVP). Implementa `MemoryPort`.

Acota los turnos por sesión (maxlen) y el NÚMERO de sesiones vivas (LRU): al superar el máximo se
descarta la menos usada recientemente. Esto cierra la fuga del diseño anterior (dict sin cota ni
TTL). En producción: adaptador Redis (compartido entre réplicas, con TTL) sustituyendo esta clase
por DI, sin tocar la capa de aplicación.
"""

from collections import OrderedDict, deque

_MAX_TURNS = 8  # últimos 8 mensajes (4 pares) por sesión — suficiente para follow-ups
_MAX_SESSIONS = 5000  # cota de sesiones vivas (LRU)


class InProcessMemory:
    def __init__(self, max_turns: int = _MAX_TURNS, max_sessions: int = _MAX_SESSIONS):
        self._max_turns = max_turns
        self._max_sessions = max_sessions
        self._sessions: OrderedDict[str, deque] = OrderedDict()

    def _touch(self, session_id: str) -> deque:
        dq = self._sessions.get(session_id)
        if dq is None:
            dq = deque(maxlen=self._max_turns)
            self._sessions[session_id] = dq
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)  # descarta la sesión LRU
        else:
            self._sessions.move_to_end(session_id)
        return dq

    def get_history(self, session_id: str) -> list[tuple[str, str]]:
        dq = self._sessions.get(session_id)
        if dq is None:
            return []
        self._sessions.move_to_end(session_id)
        return list(dq)

    def append(self, session_id: str, role: str, content: str) -> None:
        self._touch(session_id).append((role, content))

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


# Instancia por defecto: expone el API a nivel de módulo (compat) hasta inyectarla por DI en C4.
_default = InProcessMemory()
get_history = _default.get_history
append = _default.append
clear = _default.clear
