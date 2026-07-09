import logging

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    # force=True evita handlers duplicados si se reinvoca (tests/recarga uvicorn)
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
