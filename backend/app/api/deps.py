"""Dependencias comunes de la API."""

from fastapi import Header


def get_user_areas(x_user_areas: str | None = Header(default=None)) -> list[str] | None:
    """MVP (demo interna): las áreas llegan en la cabecera 'X-User-Areas'
    (ej. 'Calidad,RRHH' o '*'). ⚠️ Es una cabecera CONFIADA: solo válida detrás
    de la red interna. En producción se sustituye por las áreas del JWT (Fase 9)
    sin tocar las rutas: misma firma, otra implementación."""
    if not x_user_areas:
        return ["*"]
    return [a.strip() for a in x_user_areas.split(",") if a.strip()]
