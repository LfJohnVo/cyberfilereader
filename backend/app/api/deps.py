from fastapi import Header


def get_user_areas(x_user_areas: str | None = Header(default=None)) -> list[str] | None:
    # Cabecera CONFIADA: solo válida detrás de la red interna.
    if not x_user_areas:
        return ["*"]
    return [a.strip() for a in x_user_areas.split(",") if a.strip()]
