"""Configuración central de logging de la aplicación (guidelines §6).

Formato con timestamp y nivel; prohibido `print` en código de aplicación.
El nivel se toma de `LOG_LEVEL` vía settings.
"""

import logging

from app.core.config import get_settings


def setup_logging() -> None:
    """Configura el logger raíz. Idempotente: `force=True` evita handlers duplicados
    si se invoca más de una vez (p. ej. en tests o recargas de uvicorn)."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
